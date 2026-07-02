
from rich.console import Console
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(override=True)

console = Console()

MODEL = "llama3.2"

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# ----------------------------
# Checklist state
# ----------------------------

checklist = []
completed = []
results = {}

def show(text):
    try:
        console.print(text)
    except Exception:
        print(text)

def checklist_report():
    lines = []
    for i, item in enumerate(checklist):
        state = "[green]✓[/green]" if completed[i] else "[yellow]•[/yellow]"
        lines.append(f"{state} {i+1}. {item}")
    report = "\n".join(lines)
    show(report)
    return report

# ----------------------------
# Tools
# ----------------------------

def create_checklist(descriptions: list[str]):
    checklist.clear()
    completed.clear()
    checklist.extend(descriptions)
    completed.extend([False] * len(descriptions))
    return checklist_report()

def mark_complete(index: int, completion_notes: str):
    completed[index - 1] = True
    results[index] = completion_notes
    show(f"[cyan]Completed #{index}[/cyan]")
    show(completion_notes)
    return checklist_report()

TOOL_MAP = {
    "create_checklist": create_checklist,
    "mark_complete": mark_complete,
}

TOOLS = [
{
"type":"function",
"function":{
"name":"create_checklist",
"description":"Create the complete checklist exactly once.",
"parameters":{
"type":"object",
"properties":{
"descriptions":{
"type":"array",
"items":{"type":"string"}
}
},
"required":["descriptions"]
}
}
},
{
"type":"function",
"function":{
"name":"mark_complete",
"description":"Mark exactly one checklist item complete.",
"parameters":{
"type":"object",
"properties":{
"index":{"type":"integer"},
"completion_notes":{"type":"string"}
},
"required":["index","completion_notes"]
}
}
}
]

# ----------------------------
# Prompts
# ----------------------------

PLANNER = """
You are the Planner.

Your ONLY job is planning.

Never solve the problem.

Use create_checklist exactly once.

Rules:

- Break work into atomic steps.
- One action per checklist item.
- Every intermediate calculation gets its own step.
- If information is missing create an estimation step.
- Do not answer the user.
- After create_checklist stop.
"""

EXECUTOR = """
You are the Executor.

A checklist already exists.

Execute ONLY the first unfinished checklist item.

Available completed work is provided in the conversation.

After finishing ONE item call mark_complete.

Never execute multiple items.

Never produce the final answer.
"""

FINALIZER = """
You are the Finalizer.

All checklist items are complete.

Use the completed work to answer the user's question.

Do not mention internal planning.
"""

# ----------------------------

def tool_loop(messages):
    while True:
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS
        )

        m = r.choices[0].message

        if r.choices[0].finish_reason != "tool_calls":
            return m.content

        messages.append(m)

        for tc in m.tool_calls:
            fn = TOOL_MAP[tc.function.name]
            args = json.loads(tc.function.arguments)
            output = fn(**args)

            messages.append({
                "role":"tool",
                "tool_call_id":tc.id,
                "content":json.dumps(output)
            })

def planner(user_prompt):

    messages=[
        {"role":"system","content":PLANNER},
        {"role":"user","content":user_prompt}
    ]

    tool_loop(messages)

def first_unfinished():
    for i,v in enumerate(completed):
        if not v:
            return i+1
    return None

def executor(user_prompt):

    while True:

        idx = first_unfinished()

        if idx is None:
            break

        completed_text="\n".join(
            f"{k}. {v}"
            for k,v in sorted(results.items())
        )

        messages=[
            {
                "role":"system",
                "content":EXECUTOR
            },
            {
                "role":"user",
                "content":
f"""Original request:

{user_prompt}

Checklist

{checklist_report()}

Completed work

{completed_text}
"""
            }
        ]

        tool_loop(messages)

def finalizer(user_prompt):

    completed_text="\n".join(
        f"{k}. {v}"
        for k,v in sorted(results.items())
    )

    messages=[
        {
            "role":"system",
            "content":FINALIZER
        },
        {
            "role":"user",
            "content":
f"""Original request

{user_prompt}

Completed work

{completed_text}
"""
        }
    ]

    r=client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    show("\n[bold green]Final Answer[/bold green]\n")
    show(r.choices[0].message.content)

if __name__ == "__main__":

    user_prompt = """
A train leaves Boston at 2:00 pm traveling 60 mph.
Another train leaves New York at 3:00 pm traveling 80 mph toward Boston.
When do they meet?
"""

    planner(user_prompt)
    executor(user_prompt)
    finalizer(user_prompt)
