import json
import time
import openai
from tools import getCurrentDateAndTime, getTopologyInformation, tools_definition
from config import MODEL, MAX_TOKEN_COMPLETITION, CONFIG_PATH, OPENAI_API_KEY


def process_tool_calls(resp, messages, tools, model, max_completion_tokens=1024):
    """
    Process `tool_calls` (array) 
    """
    processed_tool = False

    try:

        # Try array-style tool_calls first
        tool_calls = None
        try:
            tool_calls = resp.choices[0].message.get("tool_calls")
        except Exception:
            tool_calls = getattr(resp.choices[0].message, "tool_calls", None)

        if tool_calls and isinstance(tool_calls, (list, tuple)) and len(tool_calls) > 0:     

            # Execute each declared tool and append tool messages
            tool_calls_index = 0
            for tc in tool_calls:
                tool_calls_index += 1
                print("-- tool_calls[",tool_calls_index,"]:\n", tc)

                try:
                    id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    function_object = tc.get("function") if isinstance(tc, dict) else getattr(tc, "function", None)
                    name = function_object.get("name") if isinstance(tc, dict) else getattr(function_object, "name", None)

                except Exception as e:
                    print("Failed to parse tool_call entry:", e)
                    continue

                if name == "getCurrentDateAndTime":
                    print("DEBUG: Enterigg tool: getCurrentDateAndTime")
                    #fmt = function_object.get("arguments", "%Y-%m-%d %H:%M:%S") 
                    arguments_object = function_object.get("arguments") if isinstance(function_object, dict) else getattr(function_object, "arguments", "%Y-%m-%d %H:%M:%S")
                    fmt = arguments_object.get("fmt") if isinstance(arguments_object, dict) else getattr(arguments_object, "fmt", "%Y-%m-%d %H:%M:%S")
                    try:
                        tool_result = getCurrentDateAndTime(fmt)
                        print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                elif name == "getTopologyInformation":
                    print("DEBUG: Entering tool: getTopologyInformation")
                    try:
                        tool_result = getTopologyInformation()
                        print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                else:
                    tool_result = f"Unknown tool: {name}"

                tool_call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                messages.append({"role": "tool", "name": name, "content": tool_result, "tool_call_id": tool_call_id})

                print("-- messages.appeneed after execution")
                print("   ",messages)            

            # Request a follow-up now that all tools executed
            try:
                follow = openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_completion_tokens,
                    tools=tools,
                    tool_choice="auto",
                )
                print("DEBUG of what we recieved from GPT (follow-up): ", follow)
                follow_msg = follow.choices[0].message.content.strip()
                print("\nChatGPT (after tools):", follow_msg)
                messages.append({"role": "assistant", "content": follow_msg})
                print("Tokens used: ")
                print(" - completion_tokens: ", follow.usage.completion_tokens)
                print(" - prompt_tokens: ", follow.usage.prompt_tokens)
                print(" - total_tokens: ", follow.usage.total_tokens)                
            except Exception as e:
                print("API error during follow-up:", e)
                time.sleep(1)

            processed_tool = True
            return messages, True

    except Exception as e:
        print("Tool processing error:", e)

    return messages, processed_tool
