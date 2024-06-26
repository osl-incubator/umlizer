"""A set of utilitary tools."""
import inspect
import os
import re
import subprocess

from pathlib import Path
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


def make_absolute(relative_path: Path) -> Path:
    """
    Convert a relative Path to absolute, relative to the current cwd.

    Parameters
    ----------
    relative_path : Path
        The path to be converted to absolute.

    Returns
    -------
    Path
        The absolute path.
    """
    # Get current working directory
    current_directory = Path(os.getcwd())

    # Return absolute path
    return (
        current_directory / relative_path
        if not relative_path.is_absolute()
        else relative_path
    )


def dot2svg(target: Path) -> None:
    """
    Run the `dot` command to convert a Graphviz file to SVG format.

    Parameters
    ----------
    target : str
        The target Graphviz file to be converted.
    """
    command = f'dot -Tsvg {target} -o {target}.svg'
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f'Error occurred: {e.stderr.decode()}')
