from llm_sdk.llm_sdk import Small_LLM_Model
import torch

model = Small_LLM_Model()

prompt = [
    {"role": "user", "content": "What is the sum of 2 and 3?"}
]

text = model._tokenizer.apply_chat_template(
    prompt,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)

print(f"Formating prompt: {prompt}")

input_ids = model.encode(text)

with torch.no_grad():
    output = model._model.generate(
        input_ids,
        max_new_tokens=500,
        do_sample=False,
        pad_token_id=model._tokenizer.pad_token_id,
        eos_token_id=model._tokenizer.eos_token_id,
    )

new_tokens = output[0][input_ids.shape[1]:]
response = model.decode(new_tokens)

print(f"Prompt: {prompt}")
print(f"Response: {response}")
