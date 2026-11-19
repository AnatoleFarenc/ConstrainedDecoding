# Description
This project aims to teach us how to optimize the output of an SLM (Small Language Model). The accuracy of correct responses for this type of model is usually around 30%. The goal of this project is to implement a Constrained Decoding approach that filters tokens one by one and only selects those that are valid according to the expected output. This allows us to get closer to 100% correct responses.

# Instruction
## Make Install

The first step is to make sure you are in the root folder of the project. Once there, you can run the command "make install". This will set up a virtual environment with all the dependencies installed.

```console
$> make install
```

## Make Lint

Now that the venv is set up, you can run "make lint" to verify the source code. More specifically, this target will run two linters: Flake8, and Mypy. Flake8 makes sure the code is formatted properly and has proper syntax, while Mypy is a type checker that verifies the type hints are consistent.

## Run Program

### Make Run
The first way to run the program is by using the Makefile with the command "make run". This will launch the **TUI** version in the terminal.

```console
$> make run
```
## Command Line
The second way to run the program is by using the command "uv run python3 -m src". The advantage of this method is that you can add flags to specify different parameters and avoid launching the TUI version.

### Flags
```console
--functions_definition [path/to/functions_definition.json]
--input [path/to/funcions_calling.json]
--output [path/to/output.json]
--mono_test [index of calling function (begining 0)]
```

```console
uv run python3 -m src
```

## Make Clean
To remove the virtual environment with all its dependencies and cache files, you can run this command.

```console
$> make clean
```

## Make Clean Cache
To remove cache files from various dependencies such as Hugging Face.

```console
>$ make clean_cache
```

# Overview

## Algorithm Explanation
To implement my Constrained Decoding algorithm, I based it on a sequence of **State** objects. Each **State** corresponds to a part of the .json format. I process tokens one by one and select the most probable token from the list of valid tokens for the current **State**. I continue this process until all expected characters for that **State** are generated, then move on to the next **State**. I loop through all prompts in this way.

## Design Decisions
For the project design, I used the **Enum** class, which allows me to create states and track where the generation process currently is.

## Performance Analysis
I defined fairly strict rules to properly constrain the model, which makes the project heavier. It would be possible to improve performance by removing some rules, but this would likely reduce the reliability of the output.
I still optimized the algorithm by adding caches to avoid recomputing already discovered tokens.
It is worth noting that the project runs very slowly on school computers due to their low specifications, but it takes around fifteen seconds to start on a more modern machine with average components.

## Challenges Faced
The first challenge was understanding what Constrained Decoding is, as well as the basic functioning of an SLM and an LLM.
The biggest difficulty was implementing the parsing part, as it is easy to become too restrictive or fail to properly guide the model.

## Testing strategy
The testing phase was an interesting part of the project. Since we were limited by hardware, I chose an architecture where prompts are processed one by one to save time between executions.
To go into more detail, I first implemented all the rules I could think of, then analyzed the generated tokens to refine the constraints. In hindsight, this was not necessarily the best approach, and it might have been simpler to work on each State individually and progress step by step.

## Example Usage

### Function calling
```json
[
    {
        "prompt": "What is the sum of 2 and 3?"
    },
    {
        "prompt": "What is the sum of 265 and 345?"
    },
    {
        "prompt": "Greet shrek"
    },
    {
        "prompt": "Greet john"
    },
    {
        "prompt": "Reverse the string 'hello'"
    },
    {
        "prompt": "Reverse the string 'world'"
    },
    {
        "prompt": "What is the square root of 16?"
    },
    {
        "prompt": "Calculate the square root of 144"
    },
    {
        "prompt": "Replace all numbers in \"Hello 34 I'm 233 years old\" with NUMBERS"
    },
    {
        "prompt": "Replace all vowels in 'Programming is fun' with asterisks"
    },
    {
        "prompt": "Substitute the word 'cat' with 'dog' in 'The cat sat on the mat with another cat'"
    }
]
```

### Function Definition
```json
[
    {
        "name": "fn_add_numbers",
        "description": "Add two numbers together and return their sum.",
        "parameters": {
            "a": {
                "type": "number"
            },
            "b": {
                "type": "number"
            }
        },
        "returns": {
            "type": "number"
        }
    },
    {
        "name": "fn_greet",
        "description": "Generate a greeting message for a person by name.",
        "parameters": {
            "name": {
                "type": "string"
            }
        },
        "returns": {
            "type": "string"
        }
    },
    {
        "name": "fn_reverse_string",
        "description": "Reverse a string and return the reversed result.",
        "parameters": {
            "s": {
                "type": "string"
            }
        },
        "returns": {
            "type": "string"
        }
    },
    {
        "name": "fn_get_square_root",
        "description": "Calculate the square root of a number.",
        "parameters": {
            "a": {
                "type": "number"
            }
        },
        "returns": {
            "type": "number"
        }
    },
    {
        "name": "fn_substitute_string_with_regex",
        "description": "Replace all occurrences matching a regex pattern in a string.",
        "parameters": {
            "source_string": {
                "type": "string"
            },
            "regex": {
                "type": "string"
            },
            "replacement": {
                "type": "string"
            }
        },
        "returns": {
            "type": "string"
        }
    }
]
```

### Output
```json
[
    {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {
            "a": 2,
            "b": 3
        }
    },
    {
        "prompt": "What is the sum of 265 and 345?",
        "name": "fn_add_numbers",
        "parameters": {
            "a": 265,
            "b": 345
        }
    },
    {
        "prompt": "Greet shrek",
        "name": "fn_greet",
        "parameters": {
            "name": "shrek"
        }
    },
    {
        "prompt": "Greet john",
        "name": "fn_greet",
        "parameters": {
            "name": "john"
        }
    },
    {
        "prompt": "Reverse the string 'hello'",
        "name": "fn_reverse_string",
        "parameters": {
            "s": "hello"
        }
    },
    {
        "prompt": "Reverse the string 'world'",
        "name": "fn_reverse_string",
        "parameters": {
            "s": "world"
        }
    },
    {
        "prompt": "What is the square root of 16?",
        "name": "fn_get_square_root",
        "parameters": {
            "a": 16.0
        }
    },
    {
        "prompt": "Calculate the square root of 144",
        "name": "fn_get_square_root",
        "parameters": {
            "a": 144
        }
    },
    {
        "prompt": "Replace all numbers in 'Hello 34 I'm 233 years old' with NUMBERS",
        "name": "fn_substitute_string_with_regex",
        "parameters": {
            "source_string": "Hello 34 I'm 233 years old",
            "regex": "([0-9]+)",
            "replacement": "NUMBERS"
        }
    },
    {
        "prompt": "Replace all vowels in 'Programming is fun' with asterisks",
        "name": "fn_substitute_string_with_regex",
        "parameters": {
            "source_string": "Programming is fun",
            "regex": "aeiou",
            "replacement": "*"
        }
    },
    {
        "prompt": "Substitute the word 'cat' with 'dog' in 'The cat sat on the mat with another cat'",
        "name": "fn_substitute_string_with_regex",
        "parameters": {
            "source_string": "The cat sat on the mat with another cat",
            "regex": "cat",
            "replacement": "dog"
        }
    }
]
```


# Ressource
[geeksforgeeks](https://www.geeksforgeeks.org/)
## AI
I mainly used AI to understand what constrained decoding is. I also used it a bit for debugging, although its suggestions often did not match what I was expecting.