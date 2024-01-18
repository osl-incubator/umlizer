"""Main module template with example functions."""
from __future__ import annotations

import os

from pathlib import Path

import typer

from typer import Context, Option
from typing_extensions import Annotated

from umlizer import __version__, class_graph

app = typer.Typer()


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


@app.callback(invoke_without_command=True)
def main(
    ctx: Context,
    version: bool = Option(
        None,
        '--version',
        '-v',
        is_flag=True,
        help='Show the version and exit.',
    ),
) -> None:
    """Run umlizer."""
    if version:
        typer.echo(f'Version: {__version__}')
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app.command('class')
def class_(
    source: Annotated[
        Path,
        typer.Option(
            ..., help='Source path for the project that would be scanned.'
        ),
    ] = Path('.'),
    target: Annotated[
        Path,
        typer.Option(
            ..., help='Target path where the UML graph will be generated.'
        ),
    ] = Path('/tmp/'),
    verbose: Annotated[
        bool, typer.Option(help='Active the verbose mode.')
    ] = False,
) -> None:
    """Run the command for class graph."""
    source = make_absolute(source)
    target = make_absolute(target) / 'class_graph'

    g = class_graph.create_class_diagram_from_source(source, verbose=verbose)
    g.format = 'png'
    g.render(target)


if __name__ == '__main__':
    app()
