"""A set of utilitary tools."""
import inspect
import re

from typing import Any

import typer


def blob_to_regex(blob: str) -> str:
    """
    Convert a blob pattern to a regular expression.

    Parameters
    ----------
    blob : str
        The blob pattern to convert.

    Returns
    -------
    str
        The equivalent regular expression.
    """
    # Escape special characters except for * and ?
    blob = re.escape(blob)

    # Replace the escaped * and ? with their regex equivalents
    blob = blob.replace(r'\*', '.*').replace(r'\?', '.')

    # Add start and end line anchors to the pattern
    return '^' + blob + '$'


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


def raise_error(message: str, exit_code: int = 1) -> None:
    """Raise an error using typer."""
    red_text = typer.style(message, fg=typer.colors.RED, bold=True)
    typer.echo(red_text, err=True, color=True)
    raise typer.Exit(exit_code)
