import json
from llm_sdk import Small_LLM_Model
from src.Prompt import Prompt
from src.Constrained_decoding import Constrained_decoding, State
import os
from pathlib import Path
import sys
from pydantic import BaseModel, Field


class GeneratorConfig(BaseModel):
    """Validated configuration used to initialize Generator."""

    input_func: str
    input_call: str
    output_json: str
    max_steps: int = 500


class GeneratorState(BaseModel):
    """Runtime state container for generated outputs."""

    responce: str = ""
    responces: list[str] = Field(default_factory=list)


class Generator():
    """ Class to generate response of prompt """

    def __init__(self, input_func: str, input_call: str,
                 output_json: str) -> None:
        """ Init Generator attributs """
        config = GeneratorConfig(
            input_func=input_func,
            input_call=input_call,
            output_json=output_json,
        )
        state = GeneratorState()

        self.model = Small_LLM_Model()
        self.pr = Prompt(config.input_func, config.input_call)
        self.max_steps = config.max_steps
        self.responce = state.responce
        self.responces = state.responces
        self.output = config.output_json

    @property
    def model(self) -> Small_LLM_Model:
        """ Return ai model (Qwen) """
        return self.__model

    @model.setter
    def model(self, model: Small_LLM_Model) -> None:
        """ Set model """
        self.__model = model

    def generate_responce(self, user_prompt: str) -> None:
        """ Generate responce to user prompt """
        self.pr.gen_prompt(user_prompt)
        cd = Constrained_decoding(self.model, self.pr)

        encode_pr = self.model.encode(self.pr.llm_prompt)
        input_ids = [int(x) for x in encode_pr[0]]
        generated: list[int] = []
        state = State.OPEN_BRACE
        step = 0

        while state != State.DONE:
            step += 1

            generated_str = self.model.decode(generated)

            if "--token" in sys.argv:
                print(generated_str)

            if step >= self.max_steps:
                print(f"Prompt: {generated_str}")
                print(f"State: {state}")
                raise RuntimeError("ERROR: Generation stoped max_step reached")

            valid_tok_ids_list = cd.get_valid_tok_ids(state, generated_str)
            if not valid_tok_ids_list:
                print(f"Prompt: {generated_str}")
                raise ValueError(f"ERROR: No valid token for state: {state}")
            valid_tok_ids = set(valid_tok_ids_list)

            logits = self.model.get_logits_from_input_ids(input_ids)
            for i in range(len(logits)):
                if i not in valid_tok_ids:
                    logits[i] = float("-inf")

            next_tok = logits.index(max(logits))
            generated.append(next_tok)
            input_ids.append(next_tok)

            generated_str = self.model.decode(generated)
            state = cd.next_state(state, generated_str)
        self.responce = generated_str

    def write_responce_json(self) -> None:
        """ Write one respons on output json file """
        try:
            json_output = json.loads(self.responce)
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"ERRROR: Invalid format: {str(e)}")

        path = self.output.rsplit("/", 1)
        output_dir = path[0]
        if not Path(output_dir).exists() and len(path) > 1:
            os.mkdir(output_dir)
        with open(self.output, 'w') as fd:
            json.dump(json_output, fd, indent=4)

    def generate_all_responce(self) -> None:
        """ Generate all responce to user prompt in json output"""
        json_outputs = []
        for i, u_pr in enumerate(self.pr.user_prompts):
            try:
                self.generate_responce(u_pr)
            except (ValueError, RuntimeError) as e:
                print(f"prompt {i}")
                print(e)
                continue
            try:
                json_outputs.append(json.loads(self.responce))
            except json.decoder.JSONDecodeError as e:
                print(f"{self.responce}")
                print(e)
                continue
            self.responces.append(self.responce)

        path = self.output.rsplit("/", 1)
        output_dir = path[0]
        if not Path(output_dir).exists() and len(path) > 1:
            os.mkdir(output_dir)
        with open(self.output, 'w') as fd:
            json.dump(json_outputs, fd, indent=4)
