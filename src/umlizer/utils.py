"""A set of utilitary tools."""
import inspect

from typing import Any


def is_function(obj: Any) -> bool:
    """
    Check if the given object is a function, method, or built-in method.

    Parameters
    ----------
    obj : Any
        The object to check.

    Returns
    -------
    bool
        True if the object is a function, method, or built-in method,
        False otherwise.
    """
    return inspect.isroutine(obj)
