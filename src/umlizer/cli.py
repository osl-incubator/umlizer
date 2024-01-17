"""Main module template with example functions."""
from __future__ import annotations

from pathlib import Path

import typer

from typer import Context, Option
from typing_extensions import Annotated

from umlizer import __version__, class_graph

app = typer.Typer()


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
    ] = Path('/tmp'),
    verbose: Annotated[
        bool, typer.Option(help='Active the verbose mode.')
    ] = False,
) -> None:
    """Run the command for class graph."""
    g = class_graph.create_class_diagram_from_source(source, verbose=verbose)
    g.format = 'png'
    g.render(target)


if __name__ == '__main__':
    app()
