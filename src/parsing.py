from typing import List, Dict
import sys
from src import ID_FUNC, ID_CALL, ID_OUTPUT, MONO_TEST
import json
from jsonschema import validate, ValidationError
from pathlib import Path


def get_parameters_value(param_key, default_value) -> str:
    """ Get the value of parameter key """
    for i, param in enumerate(sys.argv):
        if param_key == param:
            if i + 1 < len(sys.argv):
                if sys.argv[i + 1].startswith('--'):
                    raise ValueError("Missing value parameters: "
                                     f"{param_key} {sys.argv[i]}")
                return sys.argv[i + 1]
    return default_value


def check_files(path: str, shema: Dict) -> None:
    """ Check format of input files """
    if not Path(path).exists():
        raise FileNotFoundError(f"ERROR: File {path} not found")

    try:
        with open(path) as fd:
            validate(json.load(fd), schema=shema)
    except (ValidationError, json.JSONDecodeError) as e:
        raise ValueError(f"ERROR: Invalid format in {path}: {str(e)}")


def parse_argument(arguments: List) -> List[str]:
    """ Return path to input and output"""
    if "--functions_definition" in sys.argv:
        arguments[ID_FUNC] = get_parameters_value("--functions_definition",
                                                  arguments[ID_FUNC])
    if "--input" in sys.argv:
        arguments[ID_CALL] = get_parameters_value("--input",
                                                  arguments[ID_CALL])
    if "--output" in sys.argv:
        arguments[ID_OUTPUT] = get_parameters_value("--output",
                                                    arguments[ID_OUTPUT])
    if "--mono_test" in sys.argv:
        arguments[MONO_TEST] = get_parameters_value("--mono_test",
                                                    arguments[MONO_TEST])
    return arguments
