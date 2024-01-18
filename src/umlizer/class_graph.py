"""Create graphviz for classes."""
from __future__ import annotations

import copy
import dataclasses
import glob
import importlib.util
import inspect
import os
import sys
import types

from pathlib import Path
from typing import Any, Type, Union, cast

import graphviz as gv
import typer


def raise_error(message: str, exit_code: int = 1) -> None:
    """Raise an error using typer."""
    red_text = typer.style(message, fg=typer.colors.RED, bold=True)
    typer.echo(red_text, err=True, color=True)
    raise typer.Exit(exit_code)


def _get_fullname(entity: Type[Any]) -> str:
    """
    Get the fully qualified name of a given entity.

    Parameters
    ----------
    entity : types.ModuleType
        The entity for which the full name is required.

    Returns
    -------
    str
        Fully qualified name of the entity.
    """
    return f'{entity.__module__}.{entity.__name__}'


def _get_methods(entity: Type[Any]) -> list[str]:
    """
    Return a list of methods of a given entity.

    Parameters
    ----------
    entity : types.ModuleType
        The entity whose methods are to be extracted.

    Returns
    -------
    list
        A list of method names.
    """
    return [
        k
        for k, v in entity.__dict__.items()
        if not k.startswith('__') and isinstance(v, types.FunctionType)
    ]


def _get_dataclass_structure(
    klass: Type[Any],
) -> dict[str, Union[dict[str, str], list[str]]]:
    fields = {
        k: v.type.__name__ for k, v in klass.__dataclass_fields__.items()
    }
    return {'fields': fields, 'methods': _get_methods(klass)}


def _get_base_classes(klass: Type[Any]) -> list[Type[Any]]:
    return [
        c
        for c in klass.__mro__
        if c.__name__ not in ('object', klass.__name__)
    ]


def _get_annotations(klass: Type[Any]) -> dict[str, Any]:
    return getattr(klass, '__annotations__', {})


def _get_classicclass_structure(
    klass: Type[Any],
) -> dict[str, Union[dict[str, str], list[str]]]:
    _methods = _get_methods(klass)
    fields = {}

    for k in list(klass.__dict__.keys()):
        if k.startswith('__') or k in _methods:
            continue
        value = _get_annotations(klass).get(k, '')
        fields[k] = getattr(value, '__value__', str(value))

    return {
        'fields': fields,
        'methods': _methods,
    }


def _get_class_structure(
    klass: Type[Any],
) -> dict[str, Union[dict[str, str], list[str]]]:
    if dataclasses.is_dataclass(klass):
        return _get_dataclass_structure(klass)
    elif inspect.isclass(klass):
        return _get_classicclass_structure(klass)

    raise Exception('The given class is not actually a class.')


def _get_entity_class_uml(entity: Type[Any]) -> str:
    """
    Generate the UML node representation for a given class entity.

    Parameters
    ----------
    entity : type
        The class entity to be represented in UML.

    Returns
    -------
    str
        A string representation of the class in UML node format.
    """
    # Extract base classes, class structure, and format the class name
    base_classes = ', '.join(
        [_get_fullname(c) for c in _get_base_classes(entity)]
    )
    class_structure = _get_class_structure(entity)
    class_name = f'{entity.__name__}'

    if base_classes:
        class_name += f' ({base_classes})'

    # Formatting fields and methods
    fields_struct = cast(dict[str, str], class_structure['fields'])
    fields = (
        '\\l'.join(
            [
                f'{"-" if k.startswith("_") else "+"} {k}: {v}'
                for k, v in fields_struct.items()
            ]
        )
        + '\\l'
    )
    methods_struct = cast(list[str], class_structure['methods'])
    methods = (
        '\\l'.join(
            [
                f'{"-" if m.startswith("_") else "+"} {m}()'
                for m in methods_struct
            ]
        )
        + '\\l'
    )

    # Combine class name, fields, and methods into the UML node format
    uml_representation = '{' + f'{class_name}|{fields}|{methods}' + '}'
    return uml_representation


def _search_modules(
    target: str, exclude_pattern: list[str] = ['__pycache__']
) -> list[str]:
    """
    Search for Python modules in a given path, excluding specified patterns.

    Parameters
    ----------
    target : str
        Target directory to search for modules.
    exclude_pattern : list, optional
        Patterns to exclude from the search, by default ['__pycache__'].

    Returns
    -------
    list
        A list of module file paths.
    """
    results = []
    for f in glob.glob('{}/**/*'.format(target), recursive=True):
        skip = False
        for x in exclude_pattern:
            if x in f:
                skip = True
                break
        if not skip and f.endswith('.py'):
            results.append(f)

    return results


def _extract_filename(filename: str) -> str:
    return filename.split(os.sep)[-1].split('.')[0]


def _extract_module_name(module_path: str) -> tuple[str, str]:
    """
    Extract the module name from its file path.

    Parameters
    ----------
    module_path : str
        The file path of the module.

    Returns
    -------
    tuple[str, str]
        Returns the module path and the module name.
    """
    # Extract the module name from the path.
    # This needs to be adapted depending on your project's structure.
    # Example: 'path/to/module.py' -> 'path.to.module'
    module_split = module_path.split(os.sep)
    module_path = os.sep.join(module_split[:-1])
    module_filename = module_split[-1]
    module_name = module_filename.rstrip('.py')
    return module_path, module_name


def _get_classes_from_module(module_path: str) -> list[Type[Any]]:
    """
    Extract classes from a given module path using importlib.import_module.

    Parameters
    ----------
    module_path : str
        The path to the module from which classes are to be extracted.

    Returns
    -------
    list
        A list of class objects.
    """
    module_path, module_name = _extract_module_name(module_path)
    original_path = copy.deepcopy(sys.path)
    try:
        sys.path.insert(0, module_path)
        module = importlib.import_module(module_name)
        sys.path = original_path
        classes_list = [
            getattr(module, o)
            for o in dir(module)
            if inspect.isclass(getattr(module, o)) and not o.startswith('__')
        ]
        return classes_list
    except KeyboardInterrupt:
        raise_error('KeyboardInterrupt', 1)
    except Exception as e:
        print(f' Error loading module {module_name} '.center(80, '='))
        print(e)
        print('.' * 80)
        return []
    return classes_list


def create_class_diagram(
    classes_list: list[Type[Any]],
    verbose: bool = False,
) -> gv.Digraph:
    """Create a diagram for a list of classes."""
    g = gv.Digraph(comment='Graph')
    g.attr('node', shape='record', rankdir='BT')

    edges = []
    for c in classes_list:
        g.node(_get_fullname(c), _get_entity_class_uml(c))

        for b in _get_base_classes(c):
            edges.append((_get_fullname(b), _get_fullname(c)))

        if verbose:
            print('[II]', _get_fullname(c), '- included.')

    g.edges(set(edges))
    return g


def create_class_diagram_from_source(
    source: Path, verbose: bool = False
) -> gv.Digraph:
    """
    Create a class diagram from the source code located at the specified path.

    Parameters
    ----------
    source : Path
        The path to the source code.
    verbose : bool, optional
        Flag to enable verbose logging, by default False.

    Returns
    -------
    gv.Digraph
        Graphviz Digraph object representing the class diagram.

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist.
    ValueError
        If the provided path is not a directory.
    """
    classes_list = []

    path_str = str(source)

    if not os.path.exists(path_str):
        raise_error(f'Path "{path_str}" doesn\'t  exist.', 1)
    if os.path.isdir(path_str):
        sys.path.insert(0, path_str)

        for f in _search_modules(path_str):
            classes_list.extend(_get_classes_from_module(f))
    else:
        classes_list.extend(_get_classes_from_module(path_str))
    return create_class_diagram(classes_list, verbose=verbose)
