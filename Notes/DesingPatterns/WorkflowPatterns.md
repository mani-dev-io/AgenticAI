# Workflow design patterns

## Prompt chaining 
    Taking a bigger task and dividing into multiple sub tasks and run the LLMs sequentially
    IN --> LLM1 --> GATE (some code) --> LLM2 --> LLM3 --> Output

## Routing
    Direct an input to specialized sub-task ensuring separation of concern

                        --> LLM1
    IN --> LLM Router   --> LLM2    --> OUTPUT
                        --> LLM3    

## Parallelization
    Breakdown the complex task and run subtasks on multiple LLMs in parallel then agregate to generate output. Split and Aggregate is custom code in this pattern.
                                    --> LLM1
    IN --> (Code to spit the tasks) --> LLM2 --> (Code to aggregate) --> Output
                                    --> LLM3

## Orchestrator-Worker
    Breakdown the complex task and run subtasks on multiple LLMs in parallel then agregate to generate output. Split and Aggregate is done by LLMs dynamically in this pattern.

                                        --> LLM1
    IN --> (use LLLM to spit the tasks) --> LLM2 --> (use LLM to aggregate) --> Output
                                        --> LLM3

## Evaluator-Optimizer
    LLM output is validated by another LLM

                            -Solution->
    IN --> (LLM Generator)                (LLM Evaluator)   -Accepted->     Output 
                            <-Rejected-