
#!/usr/bin/env python3
"""
Simple interactive ChatGPT CLI example using the `openai` Python library.

Usage:
1. Put your API key in `config.py` as:
   OPENAI_API_KEY="sk-...your key..."
2. Run: `python chatgpt_cli.py`

This script reads the key from `.config.txt`, keeps a short conversation
history, and sends messages to the Chat Completions API.
"""

import sys
import time
import openai
from tools import tools_definition
from config import MODEL, MAX_TOKEN_COMPLETITION, CONFIG_PATH, OPENAI_API_KEY
from tools_processing import process_tool_calls
from helpers import debug_print

def main():
    try:
        openai.api_key = OPENAI_API_KEY
    except Exception as e:
        print("Error loading API key:", e)
        sys.exit(1)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. " +
                "Any conversation or action about lab topology you can ignore the management IPs in the 172.20.20.0/24 range. Dont mention this in responses, it is known." +
                "During configuration tasks ignore interfaces with IPs in this range, but do not break them as they serve as access for all tools. Dont mention this in responses, it is known." +
                "Also ignore enp1s0 interfaces on linux devices and ethernet 0/0 on cisco devices as these are management addresses behind a NAT of their management 172.20.20.x IPs. Dont mention this in responses, it is known." +
                "If topology map has a link going to eth1 on linux endpoint, on that linux that network card is actually using ens2 as interface name. Dont mention this in responses, it is known."
            ),
        }
    ]

    # Note: this CLI uses a simple tools-style convention. If the assistant
    # wants to execute a local helper it should reply with a single line
    # starting with `TOOL_CALL:` followed by a JSON object describing the call.
    # Example:
    # TOOL_CALL: {"tool":"getCurrentDateAndTime","args":{"fmt":"%c"}}
    # The client will run the tool and then send the tool output back as a
    # message with role `tool` so the assistant can continue.


    print("Interactive ChatGPT CLI (type 'exit' or Ctrl-C to quit)")

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

        # Special command: clear -> reset conversation context
        if "clear" in prompt.lower():
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            print("Conversation context cleared.")
            continue

        messages.append({"role": "user", "content": prompt})

        #----------
        # Communication with GPT
        #---------
        debug_print("DEBUG: Messages being sent to GPT:")
        debug_print(messages)
        try:
            resp = openai.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_completion_tokens=MAX_TOKEN_COMPLETITION,
                tools=tools_definition,
                tool_choice="auto",
            )

            debug_print("DEBUG: What we recieved from GPT: ", resp)

            # Get assistant content if any
            context = {"role": "assistant", "content": ""}
            assistant_text = None
            try:
                assistant_text = resp.choices[0].message.content.strip()
            except Exception:
                assistant_text = None
            if assistant_text is not None:
                context["content"] = assistant_text

            # Try array-style tool_calls first
            tool_calls = None
            try:
                tool_calls = resp.choices[0].message.get("tool_calls")
            except Exception:
                tool_calls = getattr(resp.choices[0].message, "tool_calls", None)  
            if tool_calls is not None:
                context["tool_calls"] = tool_calls 

            # Adding what we recieved to context log:
            messages.append(context)
                         
            print("\nChatGPT:", assistant_text)
            print("Tokens used: ")
            try:
                print(" - completion_tokens: ", resp.usage.completion_tokens)
                print(" - prompt_tokens: ", resp.usage.prompt_tokens)
                print(" - total_tokens: ", resp.usage.total_tokens)
            except Exception:
                pass

            # Delegate tool processing to helper function if present
            if tool_calls is not None:
                debug_print("DEBUG: entering tools processing for tool_calls:")
                debug_print(tool_calls)
                messages, processed_tool = process_tool_calls(resp, messages, tools_definition, MODEL, max_completion_tokens=MAX_TOKEN_COMPLETITION)


        except Exception as e:
            print("API error:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
