import json
import time

from openai import OpenAI

from config import config, logger


class Completions:
    def __init__(
        self,
        name="CHAT_COMPLETIONS",
        model="gpt-4o-mini",
        json_tools=[],
        functions={},
        tool_choice="auto",
    ):
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
        )
        self.name = name
        self.model = model
        self.json_tools = json_tools
        self.functions = functions
        self.tool_choice = tool_choice
        self.error_response = """Ha ocurrido un error ejecutando la herramienta {tool_name} con los argumentos {tool_args}"""

    def submit_message(self, messages):
        last_time = time.time()
        logger.info(f"Running {self.name} with {len(self.functions)} tools")
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.json_tools,
                tool_choice=self.tool_choice,  # type: ignore
            )
            if response.choices[0].message.tool_calls:
                self.run_tools(messages, response)
                continue

            break

        ans = response.choices[0].message.content.strip()  # type: ignore
        logger.info(f"{self.name}: {ans}")
        logger.debug(f"Performance de {self.name}: {time.time() - last_time}")
        return ans

    def run_tools(self, messages, response) -> None:
        tools = response.choices[0].message.tool_calls
        logger.info(f"{len(tools)} tools need to be called!")
        messages.append(response.choices[0].message)  # Tools call

        for tool in tools:
            function_name = tool.function.name
            function_args = json.loads(tool.function.arguments)
            logger.info(f"function_name: {function_name}")
            logger.info(f"function_args: {function_args}")
            function_to_call = self.functions[function_name]

            try:
                function_response = function_to_call(
                    **function_args,
                )
                logger.info(f"{tool.function.name}: {function_response[:100]}")
            except Exception as exc:
                logger.error(f"{tool.function.name}: {exc}")
                function_response = self.error_response.format(
                    tool_name=function_name, tool_args=function_args
                )

            messages.append(
                {
                    "tool_call_id": tool.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
