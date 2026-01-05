#!/usr/bin/env python3
"""Utility tools for the project.

This module provides small helper functions used by example scripts.
"""
from datetime import datetime

__all__ = ["getCurrentDateAndTime"]

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
