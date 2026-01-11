"""Helper utilities for the project."""

from config import DEBUG_MODE


def debug_print(*args, **kwargs):
    """
    Conditional debug print function that respects the DEBUG_MODE setting.
    
    Only prints if DEBUG_MODE is enabled in config.py.
    
    Args:
        *args: Positional arguments to pass to print()
        **kwargs: Keyword arguments to pass to print()
    """
    if DEBUG_MODE:
        print(*args, **kwargs)
