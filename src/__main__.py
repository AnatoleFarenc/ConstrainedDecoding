from llm_sdk import Small_LLM_Model
from src.Prompt import Prompt
from src.Constrained_decoding import Constrain_decoding, State
import sys
import json


def main():
    func_def_paht = "data/input/functions_definition.json"
    func_call_path = "data/input/function_calling_tests.json"

    try:
        prompt = Prompt(func_def_paht, func_call_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    model = Small_LLM_Model()
    prompt.gen_prompt(prompt.user_prompts[8])
    cd = Constrain_decoding(model, prompt)

    encode_pr = model.encode(prompt.llm_prompt)
    input_ids = [int(x) for x in encode_pr[0]]
    generated = []
    state = State.OPEN_BRACE
    max_steps = 500
    steps = 0

    while state != State.DONE:
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Generation stopped: max_steps reached")

        generated_str = model.decode(generated)

        valid_tok_id = cd.get_valid_tok_ids(state, generated_str)
        if not valid_tok_id:
            print(generated_str)
            raise RuntimeError(f"No valid tokens for state: {state}")
        valid_tok_set = set(valid_tok_id)

        logits = model.get_logits_from_input_ids(input_ids)

        for i in range(len(logits)):
            if i not in valid_tok_set:
                logits[i] = float("-inf")

        next_token = logits.index(max(logits))
        generated.append(next_token)
        input_ids.append(next_token)

        generated_str = model.decode(generated)
        state = cd.next_state(state, generated_str)

    print(generated_str)
    json_outputs = json.loads(generated_str)
    with open("data/output/test.json", 'w') as fd:
        json.dump(json_outputs, fd, indent=4)


if __name__ == "__main__":
    main()
