from llm_sdk import Small_LLM_Model
from . import Prompt
from . import Constrain_decoding as CD, State
import sys
import json


def main():
    func_def_paht = "data/input/functions_definition.json"
    func_call_path = "data/input/function_calling_tests.json"
    # func_def_paht = "data/input/test_function.json"
    # func_call_path = "data/input/test_pr.json"
    try:
        prompt = Prompt(func_def_paht, func_call_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    model = Small_LLM_Model()

    cd = CD(model, prompt)

    prompt.gen_prompt(prompt.user_prompts[0])

    encode = model.encode(prompt.llm_prompt)
    input_ids = [int(x) for x in encode[0]]

    generated = []
    state = State.OPEN_JSON
    max_steps = 1512
    steps = 0
    while state != State.DONE:
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Generation stopped: max_steps reached")

        generated_str = model.decode(generated)

        print(generated_str)

        valid_token_id = cd.get_valid_token(state, generated_str)
        if not valid_token_id:
            raise RuntimeError(f"No valid tokens for state: {state}")
        valid_token_set = set(valid_token_id)
        logits = model.get_logits_from_input_ids(input_ids)

        for i in range(len(logits)):
            if i not in valid_token_set:
                logits[i] = float("-inf")

        next_token_id = logits.index(max(logits))
        generated.append(next_token_id)
        input_ids.append(next_token_id)

        generated_str = model.decode(generated)
        state = cd.next_state(state, generated_str)

    response = model.decode(generated)
    n_r = foramte_resonse(response)
    print(n_r)
    # json_obj = json.loads(n_r)
    # json_str = json.dumps(json_obj, indent=4)
    # with open("data/output/test.json", 'w') as f:
    #     f.write(json_str)


def foramte_resonse(response: str) -> str:
    new_response = []
    for i in range(len(response)):
        if response[i] in '{}':
            if response[i] == '{':
                new_response.append('\n')
            new_response.append(response[i] + '\n')
        elif response[i] in "\"\'":
            if response[i] == "\'":
                new_response.append("\\\"")
            elif (response[i - 1] not in ":{}," and
                  response[i + 1] not in ":{},"):
                new_response.append("\\\"")
            else:
                new_response.append('"')
        else:
            new_response.append(response[i])
    return "".join(new_response)


if __name__ == "__main__":
    main()
