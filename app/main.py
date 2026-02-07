import argparse
import os
import sys
import json 
from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
def read(file_path):
    with open(file_path, "r") as f:
        return f.read()
def write(file_path, content):
    with open(file_path, "w") as f:
        f.write(content)
    return "OK"
def tool_execute(tool_calls):
    for tool_call in tool_calls:
        arguments = json.loads(tool_call.function.arguments)
        if tool_call.function.name == "Read":
            return read(arguments["file_path"])
        elif tool_call.function.name == "Write":
            write(arguments["file_path"], arguments["content"])
        else:
            raise ValueError(f"Unknown tool: {tool_call.function.name}")
def agent_loop(client, args):
    messages=[{"role": "user", "content": args.p}]
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
        },
        {
            "type": "function",
            "function": {
                "name": "Write",
                "description": "Write content to a file",
                "parameters": {
                "type": "object",
                "required": ["file_path", "content"],
                "properties": {
                    "file_path": {
                    "type": "string",
                    "description": "The path of the file to write to"
                    },
                    "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                    }
                }
                }
            }
        }
    ]
    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools = tools
        )
        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")
        message = chat.choices[0].message
        if hasattr(message, "tool_calls") and message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls":  [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )
            result = tool_execute(message.tool_calls)
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": message.tool_calls[0].id
            })
        else:
            print(message.content)
            break 
def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    agent_loop(client, args)
if __name__ == "__main__":
    main()
