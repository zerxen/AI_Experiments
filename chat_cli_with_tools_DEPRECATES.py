#!/usr/bin/env python3
"""
Example interactive CLI that demonstrates function-calling with the
Chat Completions API (model: `gpt-4.1`) by declaring a simple tool that
returns the local system time.

This example registers a "function" in the ChatCompletion `functions`
option. If the model decides to call the function it will return a
`function_call` in its message; the client executes the corresponding
Python function and sends the function result back to the model with
role `function` so the model can continue the conversation.

Usage:
  - Fill `.config.txt` with `OPENAI_API_KEY=sk-...`
  - Install dependency: `pip install -r requirements.txt`
  - Run: `python chat_cli_with_tools.py`

Notes:
  - This is an example; adapt error handling and security checks as needed.
"""

import os
import sys
import json
import time
import openai
from tools import getCurrentDateAndTime

CONFIG_PATH = ".config.txt"


def load_api_key(path=CONFIG_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file '{path}' not found. Create it with OPENAI_API_KEY=your_key")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip().upper() in ("OPENAI_API_KEY", "API_KEY", "OPENAI_KEY"):
                    return v.strip()
            else:
                return line
    raise ValueError("No API key found in config file.")


def main():
    try:
        openai.api_key = load_api_key()
    except Exception as e:
        print("Error loading API key:", e)
        sys.exit(1)

    # Define the functions schema we register with the model. This tells the
    # model which functions it may call and what parameters to provide.
    functions = [
        {
            "name": "get_current_time",
            "description": "Get the current local date and time formatted using strftime format",
            "parameters": {
                "type": "object",
                "properties": {
                    "fmt": {"type": "string", "description": "strftime format string"}
                },
            },
        }
    ]

    messages = [
        {"role": "system", "content": "You are a helpful assistant. You may call the registered function get_current_time(fmt) to obtain the local system time."}
    ]

    print("Interactive Chat CLI with tools (model: gpt-4.1). Type 'exit' to quit.")

    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        messages.append({"role": "user", "content": prompt})

        try:
            # Ask the model; allow it to call our registered functions.
            resp = openai.ChatCompletion.create(
                model="gpt-4.1",
                messages=messages,
                functions=functions,
                function_call="auto",  # let model decide whether to call
                max_tokens=800,
            )

            msg = resp.choices[0].message

            # Get assistant content if any
            assistant_text = None
            try:
                assistant_text = msg.content.strip()
            except Exception:
                assistant_text = None

            # Check for a function call
            func_call = None
            try:
                # Some SDKs return a dict-like object, others have attributes
                func_call = msg.get("function_call")
            except Exception:
                func_call = getattr(msg, "function_call", None)

            if func_call:
                # Extract function name and arguments
                try:
                    name = func_call.get("name") if isinstance(func_call, dict) else getattr(func_call, "name", None)
                    arguments_raw = func_call.get("arguments") if isinstance(func_call, dict) else getattr(func_call, "arguments", None)
                    # arguments may be a JSON string
                    if isinstance(arguments_raw, str):
                        arguments = json.loads(arguments_raw)
                    else:
                        arguments = arguments_raw or {}
                except Exception as e:
                    print("Failed to parse function_call arguments:", e)
                    messages.append({"role": "assistant", "content": assistant_text or ""})
                    continue

                # Execute the corresponding Python function securely
                function_result = ""
                if name == "get_current_time":
                    fmt = arguments.get("fmt", "%Y-%m-%d %H:%M:%S")
                    try:
                        function_result = getCurrentDateAndTime(fmt)
                    except Exception as e:
                        function_result = f"Error executing tool: {e}"
                else:
                    function_result = f"Unknown function: {name}"

                # Append the assistant's function call and the function result (role='function')
                messages.append({"role": "assistant", "content": assistant_text or ""})
                messages.append({"role": "function", "name": name, "content": function_result})

                # Ask the model to continue the conversation now that it has the function result
                follow = openai.ChatCompletion.create(
                    model="gpt-4.1",
                    messages=messages,
                    max_tokens=800,
                )
                follow_msg = follow.choices[0].message.content.strip()
                print("\nChatGPT:", follow_msg)
                messages.append({"role": "assistant", "content": follow_msg})
            else:
                # No function call: print assistant text directly
                if assistant_text:
                    print("\nChatGPT:", assistant_text)
                    messages.append({"role": "assistant", "content": assistant_text})
                else:
                    print("No assistant text returned.")

        except Exception as e:
            print("API error:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
