# from llm_sdk import Small_LLM_Model
# from src.Prompt import Prompt
from src.Generator import Generator
# from src.Constrained_decoding import Constrain_decoding, State
import sys
# import json


def main():
    # func_def_paht = "data/input/functions_definition.json"
    # func_call_path = "data/input/function_calling_tests.json"
    func_def_paht = "moulinette/successfully~/input/functions_definition.json"
    func_call_path = "moulinette/successfully~/input/function_calling_tests.json"
    output = "data/output/test.json"

    # try:
    #     prompt = Prompt(func_def_paht, func_call_path)
    # except FileNotFoundError as e:
    #     print(e)
    #     sys.exit()

    gen = Generator(func_def_paht, func_call_path, output)
    # gen.generate_responce(gen.pr.user_prompts[2])
    # print(gen.responce)
    gen.generate_all_responce()


if __name__ == "__main__":
    main()