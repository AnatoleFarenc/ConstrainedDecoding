from llm_sdk import Small_LLM_Model
import json


class Constrain_decoding():
    def __init__(self, model: Small_LLM_Model):
        self.__vocab_path = model.get_path_to_vocab_file()
        self.__token_ids = self.__init_token_ids()

    def get_token_ids(self) -> dict:
        """ Returen dict of tokens / ids """
        return self.__token_ids

    def __init_token_ids(self) -> dict:
        """ Init token ids dict """
        try:
            with open(self.__vocab_path) as f:
                token_ids = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("ERROR: File "
                                    f"{self.__vocab_path} not found")
        return token_ids

    def is_valid(self, token_id, idx: int) -> bool:
        """ Check if token is good """
        ...
        