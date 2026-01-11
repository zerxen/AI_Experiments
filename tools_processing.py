import json
import time
import openai
from tools import getCurrentDateAndTime, getTopologyInformation, getDeviceConfiguration, executeCommandsOnDevice, tools_definition
from config import MODEL, MAX_TOKEN_COMPLETITION, CONFIG_PATH, OPENAI_API_KEY
from helpers import debug_print


def parse_arguments(arguments_raw):
    """
    Safely parse arguments which may come as a JSON string or as a dictionary.
    Returns a dictionary, or an empty dict if parsing fails.
    """
    if isinstance(arguments_raw, dict):
        return arguments_raw
    
    if isinstance(arguments_raw, str):
        try:
            return json.loads(arguments_raw)
        except json.JSONDecodeError as e:
            print(f"WARNING: Failed to parse arguments as JSON: {e}")
            print(f"         Raw arguments: {arguments_raw}")
            return {}
    
    # If it's neither dict nor string, return empty dict
    print(f"WARNING: Arguments is neither dict nor string: {type(arguments_raw)}")
    return {}


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
                debug_print("-- tool_calls[",tool_calls_index,"]:\n", tc)

                try:
                    id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    function_object = tc.get("function") if isinstance(tc, dict) else getattr(tc, "function", None)
                    name = function_object.get("name") if isinstance(tc, dict) else getattr(function_object, "name", None)

                except Exception as e:
                    debug_print("Failed to parse tool_call entry:", e)
                    continue

                if name == "getCurrentDateAndTime":
                    debug_print("DEBUG: Enterigg tool: getCurrentDateAndTime")
                    #fmt = function_object.get("arguments", "%Y-%m-%d %H:%M:%S") 
                    arguments_raw = function_object.get("arguments") if isinstance(function_object, dict) else getattr(function_object, "arguments", {})
                    arguments_object = parse_arguments(arguments_raw)                    
                    #arguments_object = function_object.get("arguments") if isinstance(function_object, dict) else getattr(function_object, "arguments", "%Y-%m-%d %H:%M:%S")
                    fmt = arguments_object.get("fmt") if isinstance(arguments_object, dict) else getattr(arguments_object, "fmt", "%Y-%m-%d %H:%M:%S")
                    try:
                        tool_result = getCurrentDateAndTime(fmt)
                        debug_print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                elif name == "getTopologyInformation":
                    debug_print("DEBUG: Entering tool: getTopologyInformation")
                    try:
                        tool_result = getTopologyInformation()
                        debug_print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                elif name == "getDeviceConfiguration":
                    debug_print("DEBUG: Entering tool: getDeviceConfiguration")
                    arguments_raw = function_object.get("arguments") if isinstance(function_object, dict) else getattr(function_object, "arguments", {})
                    arguments_object = parse_arguments(arguments_raw)
                    target = arguments_object.get("target", None)
                    debug_print("DEBUG: target =", target)
                    try:
                        tool_result = getDeviceConfiguration(target)
                        debug_print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                elif name == "executeCommandsOnDevice":
                    debug_print("DEBUG: Entering tool: executeCommandsOnDevice")
                    arguments_raw = function_object.get("arguments") if isinstance(function_object, dict) else getattr(function_object, "arguments", {})
                    arguments_object = parse_arguments(arguments_raw)
                    target = arguments_object.get("target", None)
                    commands = arguments_object.get("commands", None)
                    expected_string = arguments_object.get("expected_string", None)
                    debug_print("DEBUG: target =", target)
                    debug_print("DEBUG: commands =", commands)
                    try:
                        tool_result = executeCommandsOnDevice(target, commands, expected_string)
                        debug_print("DEBUG: Tool result =", tool_result)
                    except Exception as e:
                        tool_result = f"Error running tool: {e}"
                else:
                    tool_result = f"Unknown tool: {name}"

                tool_call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                messages.append({"role": "tool", "name": name, "content": tool_result, "tool_call_id": tool_call_id})

                print(".. results of tool call provided to the context")
                debug_print("   ",messages)            

            # Request a follow-up now that all tools executed
            try:
                follow = openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_completion_tokens,
                    tools=tools,
                    tool_choice="auto",
                )
                debug_print("DEBUG of what we recieved from GPT (follow-up): ", follow)
                
                # Append the assistant's response (which may contain tool_calls or content)
                assistant_msg = {"role": "assistant"}
                if follow.choices[0].message.content:
                    assistant_msg["content"] = follow.choices[0].message.content.strip()
                    print("\nChatGPT (after tools):", assistant_msg["content"])
                
                # Check if the follow-up response contains tool_calls
                follow_tool_calls = getattr(follow.choices[0].message, "tool_calls", None)
                if follow_tool_calls:
                    assistant_msg["tool_calls"] = follow_tool_calls
                
                messages.append(assistant_msg)
                
                print("Tokens used: ")
                print(" - completion_tokens: ", follow.usage.completion_tokens)
                print(" - prompt_tokens: ", follow.usage.prompt_tokens)
                print(" - total_tokens: ", follow.usage.total_tokens)
                
                # If follow-up contains tool calls, process them recursively
                if follow_tool_calls:
                    print("Follow-up response contains tool_calls, processing recursively...")
                    messages, tool_processed = process_tool_calls(follow, messages, tools, model, max_completion_tokens)
                    return messages, tool_processed
                    
            except Exception as e:
                print("API error during follow-up:", e)
                time.sleep(1)

            processed_tool = True
            return messages, True

    except Exception as e:
        print("Tool processing error:", e)

    return messages, processed_tool
