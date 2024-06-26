"""Main module template with example functions."""
from __future__ import annotations

from pathlib import Path

import typer
import yaml

from typer import Context, Option
from typing_extensions import Annotated

from umlizer import __version__, class_graph, inspector
from umlizer.inspector import dict_to_classdef
from umlizer.utils import dot2svg, make_absolute

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
    ] = Path('/tmp/'),
    exclude: Annotated[
        str,
        typer.Option(
            help=(
                'Exclude directories, modules, or classes '
                '(eg. "migrations/*,scripts/*").'
            )
        ),
    ] = '',
    django_settings: Annotated[
        str,
        typer.Option(
            help='Django settings module (eg. "config.settings.dev").'
        ),
    ] = '',
    verbose: Annotated[
        bool, typer.Option(help='Active the verbose mode.')
    ] = False,
    from_yaml: Annotated[
        bool, typer.Option(help='Create the class diagram from a yaml file.')
    ] = False,
) -> None:
    """Run the command for class graph."""
    source = make_absolute(source)
    target = make_absolute(target) / 'class_graph'

    if django_settings:
        from umlizer.plugins import django

        django.setup(django_settings)

    if not from_yaml:
        classes_nodes = inspector.load_classes_definition(
            source, exclude=exclude, verbose=verbose
        )
        classes_metadata = [c.__dict__ for c in classes_nodes]
        with open(f'{target}.yaml', 'w') as f:
            yaml.dump(classes_metadata, f, indent=2, sort_keys=False)
    else:
        with open(source, 'r') as f:
            classes_metadata = yaml.safe_load(f)

    classes_nodes = dict_to_classdef(classes_metadata)

    g = class_graph.create_diagram(classes_nodes, verbose=verbose)
    g.format = 'png'
    g.render(target)

    dot2svg(target)


if __name__ == '__main__':
    app()
