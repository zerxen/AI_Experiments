#!/usr/bin/env python3
"""Utility tools for the project.

This module provides small helper functions used by example scripts.
"""
from datetime import datetime
import json
import yaml
import os

__all__ = ["getCurrentDateAndTime", "getTopologyInformation"]

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


def getTopologyInformation() -> str:
    """Read the network topology from topology.clab.yaml and return it as JSON.

    Returns:
        A JSON string containing the topology information from the YAML file.
        Returns an error message if the file cannot be read or parsed.

    Example:
        >>> topology_json = getTopologyInformation()
        >>> import json
        >>> topology = json.loads(topology_json)
    """
    print("Tool executed called: getTopologyInformation")
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        topology_file = os.path.join(script_dir, "topology_docs", "topology.clab.yaml")
        
        # Read the YAML file
        with open(topology_file, 'r') as f:
            topology_data = yaml.safe_load(f)
        
        # Convert to JSON string (compact format without whitespace)
        topology_json = json.dumps(topology_data, separators=(',', ':'))
        return topology_json
    except FileNotFoundError:
        error_msg = f"Topology file not found at {topology_file}"
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
