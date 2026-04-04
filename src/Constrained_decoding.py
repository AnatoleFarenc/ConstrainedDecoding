from enum import Enum
from src.Prompt import Prompt
from llm_sdk import Small_LLM_Model
import json
from typing import cast
from pydantic import BaseModel, Field


class State(Enum):
    OPEN_BRACE = 0         # "{"
    KEY_PROMPT = 1         # "prompt"
    VALUE_PROMPT = 2       # prompt value(string
    KEY_NAME = 3           # "name"
    VALUE_NAME = 4         # name of function
    KEY_PARAMETERS = 5     # "parameters"
    OPEN_PARAMS = 6        # "{"
    PARAM_KEY = 7          # name of parameters ("a", "b"...)
    PARAM_VALUE_NUM = 8    # number type
    PARAM_VALUE_STR = 9    # string type
    PARAM_VALUE_BOOL = 10  # bool type
    CLOSE_PARAMS = 11      # "}"
    CLOSE_BRACE = 12       # "}"
    DONE = 13              # end


class ConstrainedDecodingState(BaseModel):
    """Runtime cache and state for Constrained_decoding."""

    tok_cache: dict[str, list[int]] = Field(default_factory=dict)
    tok_cache_txt: dict[int, str] = Field(default_factory=dict)


class Constrained_decoding():
    """Constrained decoder driven by a finite-state machine."""

    def __init__(self, model: Small_LLM_Model, prompt: Prompt):
        state = ConstrainedDecodingState()

        self.__model = model
        self.__pr = prompt
        self.__vocab_path = model.get_path_to_vocab_file()
        self.__tok_ids = self.__init_token_ids()
        self.__tok_cache = state.tok_cache
        self.__tok_cache_txt = state.tok_cache_txt
        self.__user_pr = self.__pr.cur_user_pr

    def __init_token_ids(self) -> dict[str, int]:
        """ Init token ids dict """
        try:
            with open(self.__vocab_path) as f:
                vocab = cast(dict[str, int], json.load(f))
        except FileNotFoundError:
            raise FileNotFoundError("ERROR: File "
                                    f"{self.__vocab_path} not found")

        return vocab

    def __target_prefix(self, g_str: str, target: str) -> str:
        """ Return prefix of target """
        min_len = min(len(g_str), len(target))
        for i in range(min_len, -1, -1):
            if g_str.endswith(target[:i]):
                return target[:i]
        return ""

    def __tok_txt(self, tok_id: int) -> str:
        """ return text of token and set in cache """
        if tok_id in self.__tok_cache_txt:
            return self.__tok_cache_txt[tok_id]

        tok_txt = cast(str, self.__model.decode([tok_id]))
        self.__tok_cache_txt[tok_id] = tok_txt
        return tok_txt

    def __toks_for_target(self, g_str: str, target: str) -> list[int]:
        """ Return list of token for a target string """
        prefix = self.__target_prefix(g_str, target)
        if prefix == target:
            return []

        toks = []
        for tok_id in self.__tok_ids.values():
            tok_txt = self.__tok_txt(tok_id)
            if tok_txt and target.startswith(prefix + tok_txt):
                toks.append(tok_id)
        return toks

    def __cur_fun_name(self, cur_response: str) -> str:
        """ Return name of function choose in currenst response """
        for name in self.__pr.fun_name:
            marker = f'"name": "{name}"'
            idx = cur_response.find(marker)
            if idx != -1:
                return name
        return ""

    def __tok_param_key(self, cur_response: str) -> list[int]:
        """ Return list of token for key of parameter """
        f_name = self.__cur_fun_name(cur_response)
        if not f_name:
            return []
        marker = '"parameters": {'
        if marker not in cur_response:
            return []
        params_chunk = cur_response.rsplit(marker, 1)[1]

        toks = []
        for fn in self.__pr.fun:
            if fn['name'] != f_name:
                continue
            params = cast(dict[str, dict[str, str]], fn['parameters'])
            for k in params:
                if f'"{k}"' in params_chunk:
                    continue
                toks.extend(self.__toks_for_target(cur_response, f'"{k}": '))
        return toks

    def __toks_for_str(self, str_name: str) -> list[int]:
        """ Return list of token id for one string """
        if str_name in self.__tok_cache:
            return self.__tok_cache[str_name]

        toks = []
        for tok_id in self.__tok_ids.values():
            tok_txt = self.__tok_txt(tok_id)
            if tok_txt and (str_name in tok_txt or tok_txt in str_name):
                toks.append(tok_id)
        self.__tok_cache[str_name] = toks
        return toks

    def __toks_for_words(self, words: list[str]) -> list[int]:
        """ Return list of token for differents word """
        toks = []
        for word in words:
            toks += self.__toks_for_str(word)
        return toks

    def __last_params_key(self, cur_responce: str) -> str:
        """ Return the last parm in parameters objec """
        f_name = self.__cur_fun_name(cur_responce)
        for fn in self.__pr.fun:
            if fn['name'] == f_name:
                params = cast(dict[str, dict[str, str]], fn['parameters'])
                for param_name, param_type in params.items():
                    if (cur_responce.endswith(f'"{param_name}"')
                            or cur_responce.endswith(f'"{param_name}":')
                            or cur_responce.endswith(f'"{param_name}": ')):
                        return str(param_type['type'])
        return ""

    def get_valid_tok_ids(self, state: State,
                          cur_responce: str = "") -> list[int]:
        """ Return list of valid token id according to the current state"""
        match state:
            case State.OPEN_BRACE:
                return [self.__tok_ids['{']]
            case State.OPEN_PARAMS:
                return [self.__tok_ids['{']]
            case State.CLOSE_PARAMS:
                return [self.__tok_ids['}']]
            case State.CLOSE_BRACE:
                return [self.__tok_ids['}']]
            case State.KEY_NAME:
                return self.__toks_for_target(cur_responce, '"name": ')
            case State.KEY_PROMPT:
                return self.__toks_for_target(cur_responce, '"prompt": ')
            case State.KEY_PARAMETERS:
                return self.__toks_for_target(cur_responce, '"parameters": ')
            case State.VALUE_NAME:
                tok_ids = []
                for name in self.__pr.fun_name:
                    tok_ids += self.__toks_for_target(cur_responce,
                                                      f'"{name}",')
                return tok_ids

            case State.VALUE_PROMPT:
                return self.__toks_for_target(cur_responce,
                                              f'"{self.__user_pr}",')
            case State.PARAM_KEY:
                return self.__tok_param_key(cur_responce)
            case State.PARAM_VALUE_NUM:
                return self.__toks_for_str('0123456789., eE}')
            case State.PARAM_VALUE_STR:
                return [v for _, v in self.__tok_ids.items()]
            case State.PARAM_VALUE_BOOL:
                return self.__toks_for_words(["True ,}", "False ,}"])
        return []

    def next_state(self, state: State, cur_response: str) -> State:
        """ Return the next state """
        if state == State.OPEN_BRACE and "{" in cur_response:
            return State.KEY_PROMPT
        if state == State.KEY_PROMPT and cur_response.endswith('"prompt": '):
            return State.VALUE_PROMPT
        if state == State.VALUE_PROMPT and cur_response.endswith('",'):
            return State.KEY_NAME
        if state == State.KEY_NAME and cur_response.endswith('"name": '):
            return State.VALUE_NAME
        if state == State.VALUE_NAME and cur_response.endswith('",'):
            return State.KEY_PARAMETERS
        if (state == State.KEY_PARAMETERS and
                cur_response.endswith('"parameters": ')):
            return State.OPEN_PARAMS
        if state == State.OPEN_PARAMS and cur_response.endswith("{"):
            return State.PARAM_KEY
        if state == State.PARAM_KEY and cur_response.endswith('":'):
            last_param = self.__last_params_key(cur_response)
            if (last_param == "number" or last_param == "integer"
                    or last_param == "float"):
                return State.PARAM_VALUE_NUM
            if last_param == "string":
                return State.PARAM_VALUE_STR
            if last_param == "boolean":
                return State.PARAM_VALUE_BOOL
        if (state == State.PARAM_VALUE_NUM or
                state == State.PARAM_VALUE_BOOL):
            if cur_response.endswith('}'):
                return State.CLOSE_BRACE
            if cur_response.endswith(', '):
                return State.PARAM_KEY
        if state == State.PARAM_VALUE_STR:
            if '"}}' in cur_response:
                return State.DONE
            if cur_response.endswith('" }'):
                return State.CLOSE_BRACE
            if cur_response.endswith('", '):
                return State.PARAM_KEY
        if state == State.CLOSE_BRACE and cur_response.endswith('}'):
            return State.DONE
        return state
