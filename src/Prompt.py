from typing import Any
import json
from pydantic import BaseModel, Field


class PromptConfig(BaseModel):
    """Validated input configuration for Prompt."""

    functions_path: str
    call_path: str


class PromptState(BaseModel):
    """Runtime state container for Prompt."""

    sys_prompt: str = ""
    user_prompts: list[str] = Field(default_factory=list)
    llm_prompt: str = ""
    cur_user_pr: str = ""
    idx_prompt: int = 0
    fun_name: list[str] = Field(default_factory=list)
    fun_param: list[dict[str, dict[str, str]]] = Field(default_factory=list)
    fun: list[dict[str, Any]] = Field(default_factory=list)


class Prompt():
    """ Class for manage prompte """

    def __init__(self, functions_path: str, call_path: str) -> None:
        config = PromptConfig(
            functions_path=functions_path,
            call_path=call_path,
        )
        state = PromptState()

        self.fun_path = config.functions_path
        self.call_path = config.call_path
        self.sys_prompt = state.sys_prompt
        self.user_prompts = state.user_prompts
        self.llm_prompt = state.llm_prompt
        self.cur_user_pr = state.cur_user_pr
        self.idx_prompt = state.idx_prompt
        self.fun_name = state.fun_name
        self.fun_param = state.fun_param
        self.fun = state.fun

        self.init_sys_prompt()
        self.init_user_prompts()

    @property
    def fun_path(self) -> str:
        """ Return path of functions files """
        return self.__fun_path

    @fun_path.setter
    def fun_path(self, fun_path: str) -> None:
        """ Set functions path """
        self.__fun_path = fun_path

    @property
    def call_path(self) -> str:
        """ Return path of call files """
        return self.__call_path

    @call_path.setter
    def call_path(self, call_path: str) -> None:
        """ Set call path """
        self.__call_path = call_path

    @property
    def sys_prompt(self) -> str:
        """ Return system prompt """
        return self.__sys_prompt

    @sys_prompt.setter
    def sys_prompt(self, sys_prompt: str) -> None:
        """ Set system prompt """
        self.__sys_prompt = sys_prompt

    @property
    def user_prompts(self) -> list[str]:
        """ Return user prompt list """
        return self.__user_prompts

    @user_prompts.setter
    def user_prompts(self, user_prompts: list[str]) -> None:
        """ Set user prompt list"""
        self.__user_prompts = user_prompts

    @property
    def llm_prompt(self) -> str:
        """ Return llm prompt """
        return self.__llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, llm_prompt: str) -> None:
        """ Set llm prompt """
        self.__llm_prompt = llm_prompt

    @property
    def fun_name(self) -> list[str]:
        """ Return list of name function autorized """
        return self.__fun_name

    @fun_name.setter
    def fun_name(self, fun_name: list[str]) -> None:
        """ Set fun name """
        self.__fun_name = fun_name

    @property
    def fun_param(self) -> list[dict[str, dict[str, str]]]:
        """ Return list of param autorized """
        return self.__fun_param

    @fun_param.setter
    def fun_param(self, fun_param: list[dict[str, dict[str, str]]]) -> None:
        """ Set fun param """
        self.__fun_param = fun_param

    @property
    def fun(self) -> list[dict[str, Any]]:
        """ Return string of fun json """
        return self.__fun

    @fun.setter
    def fun(self, fun: list[dict[str, Any]]) -> None:
        """ Set fun string """
        self.__fun = fun

    @property
    def idx_prompt(self) -> int:
        """ Return current idx_prompte """
        return self.__idx_prompt

    @idx_prompt.setter
    def idx_prompt(self, idx: int) -> None:
        """ Set idx prompt """
        self.__idx_prompt = idx

    def init_sys_prompt(self) -> None:
        """Load function definitions and build the system prompt text."""
        try:
            with open(self.fun_path) as f:
                functions = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("ERROR: File "
                                    f"{self.fun_path} not found")
        self.fun = functions

        self.sys_prompt = ""
        for fn in functions:
            self.fun_name.append(fn['name'])
            self.fun_param.append(fn['parameters'])
            self.sys_prompt += f"- {fn['name']}: {fn['description']}\n"
            for par_name, par_type in fn["parameters"].items():
                self.sys_prompt += f"    {par_name} -> {par_type['type']}\n"
            returns_type = []
            for _, ret_type in fn["returns"].items():
                returns_type.append(ret_type)
            returns_type_str = " | ".join(returns_type)
            self.sys_prompt += f"    returns type: {returns_type_str}\n"

    def init_user_prompts(self) -> None:
        """ Init user prompts list """
        try:
            with open(self.call_path) as f:
                calling = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("ERROR: File "
                                    f"{self.call_path} not found")

        for i, prompt in enumerate(calling):
            self.user_prompts.append(prompt['prompt'])
            self.user_prompts[i] = self.user_prompts[i].replace('"', '\'')
            self.user_prompts[i] = self.user_prompts[i].replace('\\', '\\\\')
        self.cur_user_pr = self.user_prompts[0]

    def gen_prompt(self, user_prompt: str) -> None:
        """ Gene promt for llm """

        info = ("You are a function calling agent. Your job is to call the "
                "correct function depending on the users prompt. You have "
                f"access to the following functions: {self.sys_prompt}. The "
                "output must be a JSON object with the following keys: "
                "prompt (string): The original natural-language request, "
                "name (string): The name of the function to call, "
                "parameters (object): All required arguments with the correct "
                "types, if the types is number only write a float numbers in "
                "this "
                "format: 1.0 and if the type is string only write between "
                "backslash string inside in "
                'this format : "Say \\"hello\\" to {name}" .'
                "Make sure to output ONLY the json object. "
                'If no suitable function is found, the program will display ')

        self.cur_user_pr = user_prompt
        self.llm_prompt = ""
        self.llm_prompt += "<|im_start|>system\n "
        self.llm_prompt += info + '\n'
        self.llm_prompt += "The output must be formatted "
        self.llm_prompt += "in JSON format:\n"
        self.llm_prompt += "{[prompt]: [user_prompt], [name]: [function_name],"
        self.llm_prompt += " [parameters]: {[pparameters_name]: "
        self.llm_prompt += "[value_of_parameter], []...]}}\n"
        self.llm_prompt += f"{self.sys_prompt}<|im_end|>\n"
        self.llm_prompt += f"<|im_start|>user\n{user_prompt}\n<|im_end|>\n"
        self.llm_prompt += "<|im_start|>assistant\n"
