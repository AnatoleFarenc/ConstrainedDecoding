from llm_sdk import Small_LLM_Model
from src_older.Prompt import Prompt
import json
from typing import List
from enum import Enum


class State(Enum):
    OPEN_JSON = 0          # "["
    OPEN_BRACE = 1         # "{" v
    KEY_PROMPT = 2         # "prompt" v
    VALUE_PROMPT = 3       # prompt value(string) V
    KEY_NAME = 4           # "name" v
    VALUE_NAME = 5         # name of function v
    KEY_PARAMETERS = 6     # "parameters" v
    OPEN_PARAMS = 7        # "{" v
    PARAM_KEY = 8          # name of parameters ("a", "b"...) v
    PARAM_VALUE_NUM = 9    # number type v
    PARAM_VALUE_STR = 10    # string type V
    PARAM_VALUE_BOOL = 11  # bool type
    CLOSE_PARAMS = 12      # "}" v
    CLOSE_BRACE = 13       # "}" v
    CLOSE_JSON = 14        # "]"
    DONE = 15              # end


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
        self.__total_user_prompt = len(self.__prompt.user_prompts) - 1
        self.__nb_user_prompt = 0

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

    def __current_function_name(self, p_so_far: str) -> str:
        """Return the function name of the current (latest) call object."""
        last_pos = -1
        current_name = ""
        for name in self.__prompt.fun_name:
            marker = f'"name":"{name}"'
            pos = p_so_far.rfind(marker)
            if pos > last_pos:
                last_pos = pos
                current_name = name
        return current_name

    def get_token_param_key(self, p_so_far: str) -> List[int]:
        f_name = self.__current_function_name(p_so_far)

        if not f_name:
            return []

        marker = '"parameters":{'
        if marker not in p_so_far:
            return []
        params_chunk = p_so_far.rsplit(marker, 1)[1]

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

    def __latest_params_chunk(self, p_so_far: str) -> str:
        marker = '"parameters":{'
        if marker not in p_so_far:
            return ""
        return p_so_far.rsplit(marker, 1)[1]

    def __current_param_value_fragment(self, p_so_far: str) -> str:
        params_chunk = self.__latest_params_chunk(p_so_far)
        if ":" not in params_chunk:
            return ""
        return params_chunk.rsplit(":", 1)[1].lstrip()

    def __is_current_string_closed(self, p_so_far: str) -> bool:
        fragment = self.__current_param_value_fragment(p_so_far)
        if not fragment.startswith('"'):
            return False
        return '"' in fragment[1:]

    def __dedupe_ids(self, token_ids: List[int]) -> List[int]:
        unique = []
        for token in token_ids:
            if token not in unique:
                unique.append(token)
        return unique

    def get_valid_token(self, state: State, p_so_far: str = "") -> List[int]:
        """ List of good token """
        match state:
            case State.OPEN_JSON:
                return [self.__token_ids['[']]
            case State.CLOSE_JSON:
                return [self.__token_ids[']']]
            case State.OPEN_BRACE | State.OPEN_PARAMS:
                return [self.__token_ids['{']]
            case State.CLOSE_PARAMS:
                return [self.__token_ids['}']]
            case State.CLOSE_BRACE:
                return [self.__token_ids['},']]
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
                value_fragment = self.__current_param_value_fragment(p_so_far)
                if not value_fragment:
                    return self.__tokens_for_target(p_so_far, '"')
                if not value_fragment.startswith('"'):
                    return self.__tokens_for_target(p_so_far, '"')

                if self.__is_current_string_closed(p_so_far):
                    if self.__all_params_done(p_so_far):
                        return self.__tokens_for_target(p_so_far, "}")
                    return self.__tokens_for_target(p_so_far, ",")

                token_ids = self.get_token_not_contain('"')
                token_ids += self.__tokens_for_target(p_so_far, '"')
                return self.__dedupe_ids(token_ids)
            case State.PARAM_VALUE_BOOL:
                return self.get_token_for_words(["True", "False", ","])
        return []

    def get_last_param_key(self, p_so_far: str) -> str:
        f_name = self.__current_function_name(p_so_far)
        for fn in self.__prompt.fun:
            if fn['name'] == f_name:
                for par_name, par_type in fn["parameters"].items():
                    if (p_so_far.endswith(f'"{par_name}"')
                            or p_so_far.endswith(f'"{par_name}":')
                            or p_so_far.endswith(f'"{par_name}": ')):
                        return par_type['type']
        return ""

    def __all_params_done(self, p_so_far: str) -> bool:
        f_name = self.__current_function_name(p_so_far)

        if not f_name:
            return False

        marker = '"parameters":{'
        if marker not in p_so_far:
            return False
        params_chunk = p_so_far.rsplit(marker, 1)[1]

        for fn in self.__prompt.fun:
            if fn['name'] == f_name:
                for param_name in fn['parameters']:
                    if f'"{param_name}"' not in params_chunk:
                        return False
                return True
        return False

    def set_next_u_prompt(self) -> None:
        self.__prompt.idx_prompt += 1
        idx = self.__prompt.idx_prompt
        if idx <= self.__total_user_prompt:
            self.__nb_user_prompt += 1
            self.__cur_pr = self.__prompt.user_prompts[idx]

    def next_state(self, state: State, p_so_far: str) -> State:
        if state == State.OPEN_JSON and "[" in p_so_far:
            return State.OPEN_BRACE
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
        if state == State.PARAM_VALUE_STR:
            if p_so_far.endswith('",'):
                return State.PARAM_KEY
            if (self.__is_current_string_closed(p_so_far)
                    and self.__all_params_done(p_so_far)):
                return State.CLOSE_PARAMS
            return state
        if state == State.PARAM_VALUE_BOOL:
            if p_so_far.endswith('",'):
                return State.PARAM_KEY
            if self.__all_params_done(p_so_far):
                return State.CLOSE_PARAMS
            return state

        if state == State.CLOSE_PARAMS and p_so_far.endswith("}"):
            return State.CLOSE_BRACE
        if state == State.CLOSE_BRACE and p_so_far.endswith("}},"):
            if self.__nb_user_prompt < self.__total_user_prompt:
                self.set_next_u_prompt()
                return State.OPEN_BRACE
            return State.CLOSE_JSON
        if state == State.CLOSE_JSON and p_so_far.endswith("]"):
            return State.DONE
        return state
