from llm_sdk import Small_LLM_Model
from . import Prompt
from . import Constrain_decoding as CD
import sys


def main():
    func_def_paht = "data/input/functions_definition.json"
    func_call_path = "data/input/function_calling_tests.json"
    try:
        prompt = Prompt(func_def_paht, func_call_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    model = Small_LLM_Model()

    # cd = CD(model)
    # print(f"{list(ids for keys, ids in cd.get_token_ids().items()
    #               if keys == "et")}")

    prompt.gen_prompt(prompt.user_prompts[0])

    encode = model.encode(prompt.llm_prompt)
    input_ids = [int(x) for x in encode[0]]

    generated = []
    while True:
        logits = model.get_logits_from_input_ids(input_ids)

        next_token_id = logits.index(max(logits))
        if next_token_id == model.encode("<|im_end|>")[0]:
            break

        generated.append(next_token_id)
        input_ids.append(next_token_id)

    response = model.decode(generated)
    print(response)


if __name__ == "__main__":
    main()
