from llm_sdk import Small_LLM_Model
from . import Prompt
from . import Constrain_decoding as CD, State
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

    cd = CD(model, prompt)

    prompt.gen_prompt(prompt.user_prompts[0])

    encode = model.encode(prompt.llm_prompt)
    input_ids = [int(x) for x in encode[0]]

    generated = []
    state = State.OPEN_BRACE
    max_steps = 512
    steps = 0
    while state != State.DONE:
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Generation stopped: max_steps reached")

        generated_str = model.decode(generated)

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
    print(response)


if __name__ == "__main__":
    main()
