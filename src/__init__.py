from src.Prompt import Prompt
from src.Constrained_decoding import Constrained_decoding, State
ID_FUNC = 0
ID_CALL = 1
ID_OUTPUT = 2
MONO_TEST = 3

FUNC_SHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "description": "List of function definitions with parameters and types",
  "items": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Function name"
      },
      "description": {
        "type": "string",
        "description": "What the function does"
      },
      "parameters": {
        "type": "object",
        "description": "Dictionary of parameters",
        "additionalProperties": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["string", "number", "integer", "boolean", "array",
                       "object"]
            }
          },
          "required": ["type"]
        }
      },
      "returns": {
        "type": "object",
        "description": "Return type specification",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["string", "number", "integer", "boolean", "array",
                     "object"]
          }
        },
        "required": ["type"]
      }
    },
    "required": ["name", "description", "parameters", "returns"]
  }
}

CALL_SHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "description": "List of prompts",
  "items": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "Instruction or question to process"
      }
    },
    "required": ["prompt"]
  }
}

__all__ = [
  "Prompt", "Constrained_decoding", "State"
]
