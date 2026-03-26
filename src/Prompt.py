import json
from typing import List


class Prompt():
    """ Class for manage prompte """
    def __init__(self, functions_path: str, call_path: str) -> None:
        self.fun_path = functions_path
        self.call_path = call_path
        self.sys_prompt = ""
        self.user_prompts: List[str] = []
        self.llm_prompt = ""
        self.cur_u_prompt = ""
        self.fun_name = []
        self.fun_param = []
        self.fun = ""

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
    def user_prompts(self) -> List[str]:
        """ Return user prompt list """
        return self.__user_prompts

    @user_prompts.setter
    def user_prompts(self, user_prompts: List[str]) -> None:
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

    def init_sys_prompt(self) -> None:
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
            self.sys_prompt += f"- {fn['name']}: {fn["description"]}\n"
            for par_name, par_type in fn["parameters"].items():
                self.sys_prompt += f"    {par_name} -> {par_type["type"]}\n"
            returns_type = []
            for _, type in fn["returns"].items():
                returns_type.append(type)
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

        for prompt in calling:
            self.user_prompts.append(prompt['prompt'])

        self.cur_u_prompt = self.user_prompts[0]

    def gen_prompt(self, user_prompt: str) -> None:
        """ Gene promt for llm """
        self.cur_u_prompt = user_prompt
        self.llm_prompt = ""
        self.llm_prompt += "<|im_start|> The output must be formatted in "
        self.llm_prompt += "JSON format: "
        self.llm_prompt += "{[prompt]: [user_prompt], [name]: [function_name],"
        self.llm_prompt += "[parameters]: {[pparameters_name]: "
        self.llm_prompt += "[value_of_parameter], []...]}}\n\n"
        self.llm_prompt += f"system\n{self.sys_prompt}<|im_end|>\n"
        self.llm_prompt += f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        self.llm_prompt += "<|im_start|>assistant\n"
