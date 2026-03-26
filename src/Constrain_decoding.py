from llm_sdk import Small_LLM_Model
from src.Prompt import Prompt
import json
from typing import List
from enum import Enum


class State(Enum):
    OPEN_BRACE = 0         # "{" v
    KEY_PROMPT = 1         # "prompt" v
    VALUE_PROMPT = 2       # prompt value(string) V
    KEY_NAME = 3           # "name" v
    VALUE_NAME = 4         # name of function v
    KEY_PARAMETERS = 5     # "parameters" v
    OPEN_PARAMS = 6        # "{" v
    PARAM_KEY = 7          # name of parameters ("a", "b"...) v
    PARAM_VALUE_NUM = 8    # number type v
    PARAM_VALUE_STR = 9    # string type V
    PARAM_VALUE_BOOL = 10  # bool type
    CLOSE_PARAMS = 11      # "}" v
    CLOSE_BRACE = 12       # "}" v
    DONE = 13              # end


class Constrain_decoding():
    def __init__(self, model: Small_LLM_Model, prompt: Prompt):
        self.__vocab_path = model.get_path_to_vocab_file()
        self.__model = model
        self.__token_ids = self.__init_token_ids()
        self.__rev_token_ids = {v: k for k, v in self.__token_ids.items()}
        self.__prompt = prompt
        self.pars_statu = 0
        self.is_valid = []
        self.__cur_pr = self.__prompt.cur_u_prompt
        self.__token_cache = {}
        self.__token_text_cache = {}

    @property
    def pars_statu(self) -> int:
        """ Return pars_statu """
        return self.__pars_statu

    @pars_statu.setter
    def pars_statu(self, statu: int) -> None:
        """ Set new statu """
        self.__pars_statu = statu

    def get_token_ids(self) -> dict:
        """ Returen dict of tokens / ids """
        return self.__token_ids

    def __init_token_ids(self) -> dict:
        """ Init token ids dict """
        try:
            with open(self.__vocab_path) as f:
                vocab = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("ERROR: File "
                                    f"{self.__vocab_path} not found")

        return vocab

    def get_token_for_str(self, name: str) -> List[int]:
        if name in self.__token_cache:
            return self.__token_cache[name]

        tokens_id = []
        for tok_id in self.__token_ids.values():
            tok_text = self.__token_text(tok_id)
            if tok_text and (tok_text in name or name in tok_text):
                tokens_id.append(tok_id)
        self.__token_cache[name] = tokens_id
        return tokens_id

    def get_token_for_function(self) -> List[int]:
        all_tokens_id = []
        for name in self.__prompt.fun_name:
            tokens_id = self.get_token_for_str(f"\"{name}\",")
            for token in tokens_id:
                if token not in all_tokens_id:
                    all_tokens_id.append(token)
        return all_tokens_id

    def get_token_param_key(self, p_so_far: str) -> List[int]:
        f_name = ""
        for name in self.__prompt.fun_name:
            if f'"{name}"' in p_so_far:
                f_name = name
                break

        if not f_name:
            return []

        params_chunk = p_so_far
        marker = '"parameters":{'
        if marker in p_so_far:
            params_chunk = p_so_far.split(marker, 1)[1]

        all_tokens_id = []
        for fn in self.__prompt.fun:
            if fn['name'] != f_name:
                continue
            for k in fn['parameters']:
                if f'"{k}"' in params_chunk:
                    continue
                tokens_id = self.__tokens_for_target(p_so_far, f'"{k}":')
                for token in tokens_id:
                    if token not in all_tokens_id:
                        all_tokens_id.append(token)
        return all_tokens_id

    def get_token_not_contain(self, not_contain: str) -> List[int]:
        tokens_id = []
        for k, v in self.__token_ids.items():
            if not_contain not in k:
                tokens_id.append(v)
        return tokens_id

    def get_token_for_words(self, words: List[str]) -> List[int]:
        all_tokens_id = []
        for word in words:
            tokens_id = self.get_token_for_str(word)
            for token in tokens_id:
                if token not in all_tokens_id:
                    all_tokens_id.append(token)
        return all_tokens_id

    def __target_prefix(self, p_so_far: str, target: str) -> str:
        max_len = min(len(p_so_far), len(target))
        for i in range(max_len, -1, -1):
            if p_so_far.endswith(target[:i]):
                return target[:i]
        return ""

    def __token_text(self, tok_id: int) -> str:
        if tok_id in self.__token_text_cache:
            return self.__token_text_cache[tok_id]

        tok_text = self.__model.decode([tok_id])
        self.__token_text_cache[tok_id] = tok_text
        return tok_text

    def __tokens_for_target(self, p_so_far: str, target: str) -> List[int]:
        prefix = self.__target_prefix(p_so_far, target)
        if prefix == target:
            return []

        tokens = []
        for tok_id in self.__token_ids.values():
            tok_text = self.__token_text(tok_id)
            if tok_text and target.startswith(prefix + tok_text):
                tokens.append(tok_id)
        return tokens

    def get_valid_token(self, state: State, p_so_far: str = "") -> List[int]:
        """ List of good token """
        match state:
            case State.OPEN_BRACE | State.OPEN_PARAMS:
                return [self.__token_ids['{']]
            case State.CLOSE_BRACE | State.CLOSE_PARAMS:
                return [self.__token_ids['}']]
            case State.KEY_NAME:
                return self.__tokens_for_target(p_so_far, '"name":')
            case State.KEY_PROMPT:
                return self.__tokens_for_target(p_so_far, '"prompt":')
            case State.KEY_PARAMETERS:
                return self.__tokens_for_target(p_so_far, '"parameters":')
            case State.VALUE_PROMPT:
                return self.__tokens_for_target(
                    p_so_far,
                    f'"{self.__cur_pr}",',
                )
            case State.VALUE_NAME:
                all_tokens_id = []
                for name in self.__prompt.fun_name:
                    ids = self.__tokens_for_target(p_so_far, f'"{name}",')
                    for tok in ids:
                        if tok not in all_tokens_id:
                            all_tokens_id.append(tok)
                return all_tokens_id
            case State.PARAM_KEY:
                return self.get_token_param_key(p_so_far)
            case State.PARAM_VALUE_NUM:
                return self.get_token_for_str("0123456789.,-e")
            case State.PARAM_VALUE_STR:
                return self.get_token_not_contain("\"")
            case State.PARAM_VALUE_BOOL:
                return self.get_token_for_words(["True", "False", ","])
        return []

    def get_last_param_key(self, p_so_far: str) -> str:
        f_name = ""
        for name in self.__prompt.fun_name:
            if name in p_so_far:
                f_name = name
                break
        for fn in self.__prompt.fun:
            if fn['name'] == f_name:
                for par_name, par_type in fn["parameters"].items():
                    if (p_so_far.endswith(f'"{par_name}"')
                            or p_so_far.endswith(f'"{par_name}":')
                            or p_so_far.endswith(f'"{par_name}": ')):
                        return par_type['type']
        return ""

    def __all_params_done(self, p_so_far: str) -> bool:
        f_name = ""
        for name in self.__prompt.fun_name:
            if name in p_so_far:
                f_name = name
                break

        if not f_name:
            return False

        marker = '"parameters":{'
        if marker not in p_so_far:
            return False
        params_chunk = p_so_far.split(marker, 1)[1]

        for fn in self.__prompt.fun:
            if fn['name'] == f_name:
                for param_name in fn['parameters']:
                    if f'"{param_name}"' not in params_chunk:
                        return False
                return True

        return False

    def next_state(self, state: State, p_so_far: str) -> State:
        if state == State.OPEN_BRACE and "{" in p_so_far:
            return State.KEY_PROMPT
        if state == State.KEY_PROMPT and p_so_far.endswith('"prompt":'):
            return State.VALUE_PROMPT
        if state == State.VALUE_PROMPT and p_so_far.endswith('",'):
            return State.KEY_NAME
        if state == State.KEY_NAME and p_so_far.endswith('"name":'):
            return State.VALUE_NAME
        if state == State.VALUE_NAME and p_so_far.endswith('",'):
            return State.KEY_PARAMETERS
        if state == State.KEY_PARAMETERS:
            if p_so_far.endswith('"parameters":'):
                return State.OPEN_PARAMS
        if state == State.OPEN_PARAMS and p_so_far.endswith("{"):
            return State.PARAM_KEY
        if state == State.PARAM_KEY:
            params_type = self.get_last_param_key(p_so_far)
            if params_type == "number":
                return State.PARAM_VALUE_NUM
            elif params_type == "string":
                return State.PARAM_VALUE_STR
            elif params_type == "boolean":
                return State.PARAM_VALUE_BOOL
        if state == State.PARAM_VALUE_NUM:
            if self.__all_params_done(p_so_far):
                return State.CLOSE_PARAMS
            if p_so_far.endswith(','):
                return State.PARAM_KEY
            return State.PARAM_VALUE_NUM

        if state in (State.PARAM_VALUE_STR, State.PARAM_VALUE_BOOL):
            if self.__all_params_done(p_so_far):
                return State.CLOSE_PARAMS
            return State.PARAM_KEY
        if state == State.CLOSE_PARAMS and p_so_far.endswith("}"):
            return State.CLOSE_BRACE
        if state == State.CLOSE_BRACE and p_so_far.endswith("}}"):
            return State.DONE
        return state
