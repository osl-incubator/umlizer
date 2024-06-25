"""Create graphviz for classes."""
from __future__ import annotations

import ast
import copy
import dataclasses
import glob
import importlib.util
import inspect
import os
import sys
import textwrap
import types

from pathlib import Path
from typing import Any, Type, cast

import graphviz as gv
import typer

from umlizer.utils import is_function


@dataclasses.dataclass
class ClassDef:
    """Definition of class attributes and methods."""

    name: str = ''
    module: str = ''
    bases: list[str] = dataclasses.field(default_factory=list)
    fields: dict[str, str] = dataclasses.field(default_factory=dict)
    methods: dict[str, dict[str, str]] = dataclasses.field(
        default_factory=dict
    )


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
    if hasattr(entity, '__module__'):
        return f'{entity.__module__}.{entity.__name__}'
    elif hasattr(entity, '__name__'):
        return entity.__name__

    return str(entity)


def _get_method_annotation(method: types.FunctionType) -> dict[str, str]:
    annotations = getattr(method, '__annotations__', {})
    return {k: _get_fullname(v) for k, v in annotations.items()}


def _get_methods(entity: Type[Any]) -> dict[str, dict[str, str]]:
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
    methods = {}

    for k, v in entity.__dict__.items():
        if k.startswith('__') or not is_function(v):
            continue

        methods[k] = _get_method_annotation(v)

    return methods


def _get_dataclass_structure(
    klass: Type[Any],
) -> ClassDef:
    fields = {
        k: getattr(v.type, '__name__', 'Any')
        for k, v in klass.__dataclass_fields__.items()
    }
    return ClassDef(
        name='',
        fields=fields,
        methods=_get_methods(klass),
    )


def _get_base_classes(klass: Type[Any]) -> list[Type[Any]]:
    return [
        c
        for c in klass.__mro__
        if c.__name__ not in ('object', klass.__name__)
    ]


def _get_annotations(klass: Type[Any]) -> dict[str, Any]:
    annotations = getattr(klass, '__annotations__', {})
    return {k: _get_fullname(v) for k, v in annotations.items()}


def _get_init_attributes(klass: Type[Any]) -> dict[str, str]:
    """Extract attributes declared in the __init__ method using `self`."""
    attributes: dict[str, str] = {}
    init_method = klass.__dict__.get('__init__')

    if not init_method or not isinstance(init_method, types.FunctionType):
        return attributes

    source_lines, _ = inspect.getsourcelines(init_method)
    source_code = textwrap.dedent(''.join(source_lines))
    tree = ast.parse(source_code)

    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == 'self'
            ):
                attr_name = target.attr
                attr_type = 'Any'  # Default type if not explicitly typed

                # Try to get the type from the annotation if it exists
                if isinstance(node.value, ast.Name):
                    attr_type = node.annotation.id  # type: ignore[attr-defined]
                elif isinstance(node.value, ast.Call) and isinstance(
                    node.value.func, ast.Name
                ):
                    attr_type = node.value.func.annotation.id  # type: ignore[attr-defined]
                elif isinstance(node.value, ast.Constant):
                    attr_type = type(node.value.value).__name__

                attributes[attr_name] = attr_type

    return attributes


def _get_classic_class_structure(klass: Type[Any]) -> ClassDef:
    """Get the structure of a classic (non-dataclass) class."""
    _methods = _get_methods(klass)
    klass_anno = _get_annotations(klass)
    fields = {}

    for k in list(klass.__dict__.keys()):
        if k.startswith('__') or k in _methods:
            continue
        value = klass_anno.get(k, 'UNKNOWN')
        fields[k] = getattr(value, '__value__', str(value))

    if not fields:
        # Extract attributes from the `__init__` method if defined there.
        fields = _get_init_attributes(klass)

    return ClassDef(
        fields=fields,
        methods=_methods,
    )


def _get_class_structure(
    klass: Type[Any],
) -> ClassDef:
    if dataclasses.is_dataclass(klass):
        class_struct = _get_dataclass_structure(klass)
    elif inspect.isclass(klass):
        class_struct = _get_classic_class_structure(klass)
    else:
        raise Exception('The given class is not actually a class.')

    class_struct.module = klass.__module__
    class_struct.name = _get_fullname(klass)

    class_struct.bases = []
    for ref_class in _get_base_classes(klass):
        class_struct.bases.append(_get_fullname(ref_class))

    return class_struct


def _get_entity_class_uml(klass: ClassDef) -> str:
    """
    Generate the UML node representation for a given class entity.

    Parameters
    ----------
    klass : type
        The class entity to be represented in UML.

    Returns
    -------
    str
        A string representation of the class in UML node format.
    """
    # Extract base classes, class structure, and format the class name
    base_classes = ', '.join(klass.bases)
    class_name = klass.name

    if base_classes:
        if len(base_classes) < 20:  # noqa: PLR2004
            class_name += f' ({base_classes})'
        else:
            class_name += ' (\\n' + base_classes.replace(', ', ',\\n  ') + ')'

    # Formatting fields and methods
    fields_struct = klass.fields
    fields_raw = []
    for a_name, a_type in fields_struct.items():
        a_visibility = '-' if a_name.startswith('_') else '+'
        fields_raw.append(f'{a_visibility} {a_name}: {a_type}')

    fields = '\\l'.join(fields_raw) + '\\l'

    methods_struct = cast(dict[str, dict[str, Any]], klass.methods)
    methods_raw = []
    for m_name, m_metadata in methods_struct.items():
        m_visibility = '-' if m_name.startswith('_') else '+'
        m_type = m_metadata.get('return', 'Any').replace('builtins.', '')
        m_params_raw = [
            f"{k}: {v.replace('builtins.', '')}"
            for k, v in m_metadata.items()
            if k != 'return'
        ]
        m_params = ', '.join(m_params_raw)
        methods_raw.append(f'{m_visibility} {m_name}({m_params}): {m_type}')

    methods = '\\l'.join(methods_raw) + '\\l'

    # Combine class name, fields, and methods into the UML node format
    uml_representation = '{' + f'{class_name}|{fields}|{methods}' + '}'
    return uml_representation


def _search_modules(
    target: str,
    exclude_pattern: list[str] = ['__pycache__'],
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
        sys.path = original_path
        return []
    return classes_list


def create_diagram(
    classes_list: list[ClassDef],
    verbose: bool = False,
) -> gv.Digraph:
    """Create a diagram for a list of classes."""
    g = gv.Digraph(comment='Graph')
    g.attr('node', shape='record', rankdir='BT')

    edges = []
    for klass in classes_list:
        g.node(klass.name, _get_entity_class_uml(klass))

        for b in klass.bases:
            edges.append((b, klass.name))

        if verbose:
            print('[II]', klass.name, '- included.')

    g.edges(set(edges))
    return g


def load_classes_definition(
    source: Path,
    exclude: str,
    verbose: bool = False,
) -> list[ClassDef]:
    """
    Load classes definition from the source code located at the specified path.

    Parameters
    ----------
    source : Path
        The path to the source code.
    exclude: pattern that excludes directories, modules or classes
    verbose : bool, optional
        Flag to enable verbose logging, by default False.

    Returns
    -------
    ClassDef

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist.
    ValueError
        If the provided path is not a directory.
    """
    classes_list = []
    module_files = []

    path_str = str(source)

    if not os.path.exists(path_str):
        raise_error(f'Path "{path_str}" doesn\'t  exist.', 1)
    if os.path.isdir(path_str):
        sys.path.insert(0, path_str)
        exclude_pattern = [exclude.strip() for exclude in exclude.split(',')]
        exclude_pattern.append('__pycache__')
        module_files.extend(
            _search_modules(path_str, exclude_pattern=exclude_pattern)
        )
    else:
        module_files.append(path_str)

    for file_path in module_files:
        classes_list.extend(_get_classes_from_module(file_path))

    return [_get_class_structure(cls) for cls in classes_list]
