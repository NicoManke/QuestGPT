import openai
import time
import color_console


class OpenAIFacade:
    def __init__(self, api_key: str, api_model: str, max_request_tries=12, waiting_time=30):
        openai.api_key = api_key
        self.__model = api_model  # "gpt-3.5-turbo-0613" or "gpt-4"
        self.__max_tries = max_request_tries
        self.__waiting_time = waiting_time
        self.__messages = []
        self.__coco = color_console.ColorConsole()

    def add_message(self, message: str, role: str = "user"):
        self.__messages.append(
            {"role": role,
             "content": message}
        )

    def get_response(self, messages: [], temperature=0.0):
        while True:
            try:
                response = openai.ChatCompletion.create(
                    model=self.__model,
                    messages=messages,
                    temperature=temperature
                )
            except openai.error.RateLimitError:
                self.__coco.coco_print(f"\nWaiting for {self.__waiting_time} seconds...\n")
                time.sleep(self.__waiting_time)
            except Exception as e:
                self.__coco.coco_error(f"an unknown Error occured: {e}")
            else:
                messages.append(response["choices"][0]["message"])
                break

        prompt_tokens = response["usage"]["prompt_tokens"]
        completion_tokens = response["usage"]["completion_tokens"]
        self.__coco.coco_debug(f"prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}.")

        return response

    def make_function_call(self, messages: [], functions: [], function_call: str = "auto", temperature=0.0):
        while True:
            try:
                response = openai.ChatCompletion.create(
                    model=self.__model,
                    messages=messages,
                    functions=functions,
                    function_call={"name": function_call},
                    temperature=temperature
                )
            except openai.error.RateLimitError:
                waiting_time = 10
                self.__coco.coco_print(f"\nWaiting for {waiting_time} seconds...\n")
                time.sleep(waiting_time)
            else:
                break

        prompt_tokens = response["usage"]["prompt_tokens"]
        completion_tokens = response["usage"]["completion_tokens"]
        self.__coco.coco_debug(f"prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}.")

        return response

    def print_response(self, response):
        print(response["choices"][0]["message"]["content"])
