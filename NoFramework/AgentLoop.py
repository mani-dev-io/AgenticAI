from rich.console import Console
from dotenv import load_dotenv
from openai import OpenAI
import json
from rules import rules
load_dotenv(override=True)

def show(text):
    try:
        Console().print(text)
    except Exception:
        print(text)

openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama') 

checklist = []
completed = []

def get_checklist_report() -> str:
    result = ""
    for index, item in enumerate(checklist):
        if completed[index]:
            result += f"Checklist #{index + 1}: [green][strike]{item}[/strike][/green]\n"
        else:
            result += f"Checklist #{index + 1}: {item}\n"
    show(result)
    return result

#get_checklist_report()

def create_checklist(descriptions: list[str]) -> str:
    checklist.extend(descriptions)
    completed.extend([False] * len(descriptions))
    return get_checklist_report()

def mark_complete(index: int, completion_notes: str) -> str:
    if 1 <= index <= len(checklist):
        completed[index - 1] = True
    else:
        return "No checklist at this index."
    Console().print(completion_notes)
    return get_checklist_report()

checklist, completed = [], []

create_checklist_json = {
    "name": "create_checklist",
    "description": "Add new checklist from a list of descriptions and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "descriptions": {
                'type': 'array',
                'items': {'type': 'string'},
                'title': 'Descriptions of checklist items'
                }
            },
        "required": ["descriptions"],
        "additionalProperties": False
    }
}

mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark complete the checklist item at the given position (starting from 1) and return the full list",
    "parameters": {
        'properties': {
            'index': {
                'description': 'The 1-based index of the checklist item to mark as complete',
                'title': 'Index',
                'type': 'integer'
                },
            'completion_notes': {
                'description': 'Notes about how you completed the checklist item in rich console markup',
                'title': 'Completion Notes',
                'type': 'string'
                }
            },
        'required': ['index', 'completion_notes'],
        'type': 'object',
        'additionalProperties': False
    }
}

tools = [{"type": "function", "function": create_checklist_json},
        {"type": "function", "function": mark_complete_json}]

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results

def loop(messages):
    response = openai.chat.completions.create(model="llama3.2", messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = openai.chat.completions.create(model="llama3.2", messages=messages, tools=tools)
    show(response.choices[0].message.content)

system_message = f"""
You are the reasoning engine for an AI agent.

Your responsibility is to solve problems by creating and executing a checklist of small, independent tasks.

## Workflow

You MUST always follow this sequence:

1. Understand the user's request completely.
2. Create a complete checklist before attempting to solve the problem.
3. Add every checklist item using the available checklist tools.
4. Execute one checklist item at a time.
5. After completing an item, continue with the next unfinished item.
6. Continue until every checklist item is completed.
7. Only after the checklist is finished should you produce the final answer.

Never skip the planning phase.

---

## Checklist Planning Rules

A good checklist decomposes a problem into atomic reasoning steps.

Each checklist item must perform exactly ONE action.

Examples of actions:

- Identify known information
- Identify unknown information
- Detect assumptions
- Estimate missing values
- Gather required information
- Choose an approach
- Perform one calculation
- Verify a calculation
- Compare alternatives
- Analyze results
- Summarize findings
- Produce the final answer

Never combine multiple reasoning steps into one checklist item.

Bad:

- Solve the problem

Good:

- Identify known information
- Identify missing information
- Estimate missing values
- Perform first calculation
- Perform second calculation
- Verify results
- Produce final answer

---

## Planning Guidelines

When creating the checklist, determine:

• What information is already available?
• What information is missing?
• What assumptions are required?
• Which intermediate results are needed?
• What dependencies exist between steps?
• What calculations or reasoning must occur?
• How can the solution be verified?

Every required intermediate result should become its own checklist item.

---

## Missing Information

If the task cannot be solved exactly because information is missing:

- Create a checklist item to estimate the missing information.
- Clearly state the assumption used.
- Continue solving using that assumption.
- Never invent values without first creating an estimation step.

---

## Tool Usage

The checklist is the source of truth.

Before execution:
- Every required step must exist in the checklist.

During execution:
- Work on exactly one checklist item.
- Mark it complete before moving on.

Do not execute work that is not represented in the checklist.

---

## Quality Checks

Before considering the checklist complete, verify:

✓ Every part of the user's request is covered.
✓ Missing information has been addressed.
✓ Every calculation has its own checklist item.
✓ Every dependency has been resolved.
✓ No reasoning step has been skipped.
✓ The checklist could be executed by another AI without additional planning.

---

## Final Answer

Only after all checklist items are complete:

- Review the completed checklist.
- Verify the final answer is consistent with all completed work.
- Present a complete, well-formatted response.
- Do not mention internal reasoning or hidden thoughts.
"""
user_message = """"
A train leaves Boston at 2:00 pm traveling 60 mph.
Another train leaves New York at 3:00 pm traveling 80 mph toward Boston.
When do they meet?
"""
messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]

checklist, completed = [], []
loop(messages)
