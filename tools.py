#!/usr/bin/env python3
"""Utility tools for the project.

This module provides small helper functions used by example scripts.
"""
from datetime import datetime
import json
import yaml
import os
import paramiko
import re
from netmiko import ConnectHandler
from helpers import debug_print

__all__ = ["getCurrentDateAndTime", "getTopologyInformation", "getDeviceConfiguration", "executeCommandsOnDevice"]

# Declare available tools (ensure this is in-scope for the chat calls)
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "getCurrentDateAndTime",
            "description": "Return the current local date and time formatted using a strftime string",
            "parameters": {
                "type": "object",
                "properties": {
                    "fmt": {"type": "string", "description": "strftime format string"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getTopologyInformation",
            "description": "Read and return the network topology information from the topology.clab.yaml file converted to JSON format",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getDeviceConfiguration",
            "description": "Retrieve the running configuration or network information from a target device via SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "The target device name (e.g., 'cisco1', 'ubuntu1')"}
                },
                "required": ["target"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "executeCommandsOnDevice",
            "description": "Execute arbitrary commands on a target device via SSH after user approval",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "The target device name (e.g., 'cisco1', 'ubuntu1')"},
                    "commands": {"type": "string", "description": "Commands to execute on the target; newline-separated or semicolon-separated"},
                    "expected_string": {"type": "string", "description": "Optional regex/string that describes the expected prompt/string after command execution (used as an expect_string)"}
                },
                "required": ["target", "commands"]
            },
        },
    }
]

def getCurrentDateAndTime(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return the current local date and time as a formatted string.

    Args:
        fmt: A `strftime` format string (default: "%Y-%m-%d %H:%M:%S").

    Returns:
        A string with the current local date and time formatted by `fmt`.

    Example:
        >>> getCurrentDateAndTime()
        '2025-12-11 14:23:01'
    """
    print("Tool executed called: getCurrentDateAndTime with fmt =", fmt)
    now = datetime.now()
    return now.strftime(fmt)


def getTopologyInformation(internal_call: bool = False) -> str:
    """Read the network topology from topology.clab.yaml and ansible-inventory.yml, 
    convert to JSON and merge them.

    Args:
        internal_call: If True, suppresses the tool execution print message (used for internal calls).

    Returns:
        A JSON string containing the merged topology and ansible inventory information.
        Returns an error message if the files cannot be read or parsed.

    Example:
        >>> topology_json = getTopologyInformation()
        >>> import json
        >>> data = json.loads(topology_json)
    """
    if not internal_call:
        print("Tool executed called: getTopologyInformation")
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        topology_file = os.path.join(script_dir, "topology_docs", "topology.clab.yaml")
        ansible_inventory_file = os.path.join(script_dir, "topology_docs", "clab-lab_topology", "ansible-inventory.yml")
        
        # Read the YAML topology file
        with open(topology_file, 'r') as f:
            topology_data = yaml.safe_load(f)
        
        # Read the Ansible inventory file
        with open(ansible_inventory_file, 'r') as f:
            ansible_data = yaml.safe_load(f)
        
        # Merge the data - add ansible inventory under a new key
        merged_data = {
            "topology": topology_data,
            "ansible_inventory": ansible_data
        }
        
        # Convert to JSON string (compact format without whitespace)
        
        topology_json = json.dumps(merged_data, separators=(',', ':'))
        #print("DEBUG: Topology JSON that will be returned.")  
        #json_dict = json.loads(topology_json)  
        #print("DEBUG: " + json.dumps(json_dict, indent=2))         
        return topology_json
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})
    except yaml.YAMLError as e:
        error_msg = f"Error parsing YAML file: {str(e)}"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})
    except Exception as e:
        error_msg = f"Unexpected error reading topology: {str(e)}"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})


def getDeviceConfiguration(target: str) -> str:
    """Retrieve the running configuration or network information from a target device via SSH.

    Args:
        target: The target device name (e.g., 'cisco1', 'ubuntu1')

    Returns:
        A JSON string containing the device configuration/network information.
        Returns an error message if the device cannot be found or accessed.

    Example:
        >>> config_json = getDeviceConfiguration('cisco1')
        >>> import json
        >>> config = json.loads(config_json)
    """
    print(f"Tool executed called: getDeviceConfiguration with target = {target}")
    try:
        # Get topology information
        topology_json = getTopologyInformation(internal_call=True)
        topology_data = json.loads(topology_json)
        
        # Search for the target device in the ansible inventory
        ansible_inventory = topology_data.get("ansible_inventory", {})
        all_children = ansible_inventory.get("all", {}).get("children", {})
        
        device_info = None
        device_type = None
        
        # Search through all device groups
        for group_name, group_data in all_children.items():
            hosts = group_data.get("hosts", {})
            
            # Check if target matches (with or without clab prefix)
            for hostname, host_data in hosts.items():
                if target in hostname or hostname.endswith(f"-{target}"):
                    device_info = host_data
                    device_type = group_name
                    break
            
            if device_info:
                break
        
        if not device_info:
            error_msg = f"Target device '{target}' not found in topology"
            print(f"Error: {error_msg}")
            return json.dumps({"error": error_msg})
        
        # Extract connection parameters
        management_ip = device_info.get("ansible_host")
        ansible_user = all_children[device_type].get("vars", {}).get("ansible_user")
        ansible_password = all_children[device_type].get("vars", {}).get("ansible_password")
        
        # Print debug output
        debug_print(f"DEBUG: target = {target}")
        debug_print(f"DEBUG: management_ip = {management_ip}")
        debug_print(f"DEBUG: ansible_user = {ansible_user}")
        debug_print(f"DEBUG: ansible_password = {ansible_password}")
        debug_print(f"DEBUG: device_type = {device_type}")
        
        # Determine if Cisco (ios) or Linux (generic_vm)
        if device_type == "cisco_iol":
            # SSH to Cisco device using Netmiko
            device_params = {
                "device_type": "cisco_ios",
                "host": management_ip,
                "username": ansible_user,
                "password": ansible_password,
                "port": 22,
                "timeout": 10,
                "auth_timeout": 10,
            }
            
            print(f"Connecting to Cisco device at {management_ip} to execute 'show running-configuration'")
            connection = ConnectHandler(**device_params)
            
            # Get running configuration
            output = connection.send_command("show run")
            connection.disconnect()
            
            result = {
                "target": target,
                "management_ip": management_ip,
                "device_type": device_type,
                "command": "show running-configuration",
                "output": output
            }
        
        elif device_type == "generic_vm":
            # SSH to Linux device using Paramiko
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"Connecting to Linux device at {management_ip} to execute 'ip addr' and 'ip route'")
            ssh_client.connect(management_ip, username=ansible_user, password=ansible_password, timeout=10)
            
            # Get IP address information
            stdin, stdout, stderr = ssh_client.exec_command("ip addr")
            ip_addr_output = stdout.read().decode("utf-8")
            
            # Get routing information
            stdin, stdout, stderr = ssh_client.exec_command("ip route")
            ip_route_output = stdout.read().decode("utf-8")
            
            ssh_client.close()
            
            result = {
                "target": target,
                "management_ip": management_ip,
                "device_type": device_type,
                "commands": {
                    "ip_addr": ip_addr_output,
                    "ip_route": ip_route_output
                }
            }
        
        else:
            error_msg = f"Unknown device type: {device_type}"
            print(f"Error: {error_msg}")
            return json.dumps({"error": error_msg})
        
        # Convert result to JSON (compact format)
        result_json = json.dumps(result, separators=(',', ':'))
        debug_print(f"DEBUG: Device {target} configuration result:")
        debug_output = json.dumps(result, indent=2).replace('\\n', '\n')
        debug_print("DEBUG: " + debug_output)
        return result_json
    
    except Exception as e:
        error_msg = f"Error retrieving device configuration: {str(e)}"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})


def executeCommandsOnDevice(target: str, commands: str, expected_string: str = None) -> str:
    """Execute arbitrary commands on a target device via SSH after human approval.

    Args:
        target: The target device name as in the inventory (e.g., 'cisco1', 'ubuntu1').
        commands: A string containing commands to execute (newline-separated or semicolon-separated).

    Returns:
        JSON string with the command outputs, or an error message.
    """
    print(f"Tool executed called: executeCommandsOnDevice target={target}")
    try:
        # Get topology and inventory
        topology_json = getTopologyInformation(internal_call=True)
        topology_data = json.loads(topology_json)
        ansible_inventory = topology_data.get("ansible_inventory", {})
        all_children = ansible_inventory.get("all", {}).get("children", {})

        device_info = None
        device_type = None

        for group_name, group_data in all_children.items():
            hosts = group_data.get("hosts", {})
            for hostname, host_data in hosts.items():
                if target in hostname or hostname.endswith(f"-{target}"):
                    device_info = host_data
                    device_type = group_name
                    break
            if device_info:
                break

        if not device_info:
            error_msg = f"Target device '{target}' not found in topology"
            print(f"Error: {error_msg}")
            return json.dumps({"error": error_msg})

        management_ip = device_info.get("ansible_host")
        ansible_user = all_children[device_type].get("vars", {}).get("ansible_user")
        ansible_password = all_children[device_type].get("vars", {}).get("ansible_password")

        debug_print(f"DEBUG: target = {target}")
        debug_print(f"DEBUG: management_ip = {management_ip}")
        debug_print(f"DEBUG: ansible_user = {ansible_user}")
        debug_print(f"DEBUG: ansible_password = {ansible_password}")
        debug_print(f"DEBUG: device_type = {device_type}")

        # Show the commands and request approval
        print("Commands to execute:")
        print(commands)
        approved = input("approved? [yes/no] ").strip().lower()
        if approved != "yes":
            msg = "Execution of these specific commands not approved by user manually, please let's discuss alternatives."
            print(msg)
            return json.dumps({"error": msg})

        # Normalize commands into a list
        if "\n" in commands:
            cmd_list = [c for c in commands.splitlines() if c.strip()]
        elif ";" in commands:
            cmd_list = [c.strip() for c in commands.split(";") if c.strip()]
        else:
            cmd_list = [commands.strip()]

        outputs = {}

        if device_type == "cisco_iol":
            device_params = {
                "device_type": "cisco_ios",
                "host": management_ip,
                "username": ansible_user,
                "password": ansible_password,
                "port": 22,
                "timeout": 10,
                "auth_timeout": 10,
            }
            debug_print(f"DEBUG: Connecting to Cisco device at {management_ip}")
            conn = ConnectHandler(**device_params)
            # If caller provided an explicit expected_string, use it as the
            # expect_string (assumed to be a regex or literal). Otherwise
            # derive a prompt regex from the device prompt (hostname + optional
            # mode suffixes like (config)).
            # Use caller-provided expected_string if it was explicitly supplied
            # (allow empty string if caller intentionally passed it). Treat
            # None as 'not provided'.
            if expected_string is not None:
                prompt_regex = expected_string
            else:
                try:
                    base_prompt = conn.find_prompt().strip()
                    # Extract hostname portion before any '(' e.g. 'cisco1' from 'cisco1(config)#'
                    hostname = re.split(r"[\(]", base_prompt)[0].rstrip('#>')
                    prompt_regex = rf"{re.escape(hostname)}(?:\([^)]+\))?[#>]\s*$"
                except Exception:
                    # Fallback to a generic prompt matcher
                    prompt_regex = r".+[#>]\s*$"

            debug_print(f"DEBUG: Using prompt regex: {prompt_regex}")

            for cmd in cmd_list:
                try:
                    out = conn.send_command(cmd, expect_string=prompt_regex)
                except Exception:
                    # Fallback to timing-based send if expect_string fails
                    out = conn.send_command_timing(cmd)
                outputs[cmd] = out

            conn.disconnect()

        elif device_type == "generic_vm":
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            debug_print(f"DEBUG: Connecting to Linux device at {management_ip}")
            ssh_client.connect(management_ip, username=ansible_user, password=ansible_password, timeout=10)
            for cmd in cmd_list:
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                out = stdout.read().decode("utf-8")
                err = stderr.read().decode("utf-8")
                outputs[cmd] = {"stdout": out, "stderr": err}
            ssh_client.close()

        else:
            error_msg = f"Unknown device type: {device_type}"
            print(f"Error: {error_msg}")
            return json.dumps({"error": error_msg})

        result = {
            "target": target,
            "management_ip": management_ip,
            "device_type": device_type,
            "commands_executed": cmd_list,
            "outputs": outputs,
        }

        print("Outputs obtained from device:")
        print(outputs)

        debug_print(f"DEBUG: Device {target} commands excecution result:")
        debug_print("DEBUG: " + json.dumps(result, indent=2).replace('\\n', '\n'))
        return json.dumps(result, separators=(',', ':'))

    except Exception as e:
        error_msg = f"Error executing commands on device: {str(e)}"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})
