import argparse
import os
import sys
import json 
from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
def tool_execute(tool_calls):
    for tool_call in tool_calls:
        if tool_call.function.name == "Read":
            arguments = json.loads(tool_call.function.arguments)
            with open(arguments["file_path"], "r") as f:
                return f.read()
        else:
            raise ValueError(f"Unknown tool: {tool_call.function.name}")
def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
        tools = [
            {
                "type": "function",
                "function": {
                    "name" : "Read",
                    "description":"Read and return the content of a file",
                    "parameters":{
                        "type": "object",
                        "properties":{
                            "file_path":{
                                "type": "string",
                                "description": "The path to the file to read"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]
    )
    message = chat.choices[0].message
    if hasattr(message, "tool_calls") and message.tool_calls:
        tool_execute(message.tool_calls)
    else:
        print(message.content)
    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")
    
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # TODO: Uncomment the following line to pass the first stage
    print(chat.choices[0].message.content)


if __name__ == "__main__":
    main()
