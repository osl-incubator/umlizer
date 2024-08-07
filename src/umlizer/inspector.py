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
from typing import Any, Type

from umlizer.utils import is_function, raise_error


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


def get_full_class_path(cls: Type[Any], root_path: Path) -> str:
    """
    Get the full package path for a given class, including parent packages.

    Parameters
    ----------
    cls : Type[Any]
        The class to inspect.
    root_path : Path
        The root path of the project to determine the full package path.

    Returns
    -------
    str
        The full package path of the class.
    """
    module = cls.__module__
    imported_module = importlib.import_module(module)
    module_file = getattr(imported_module, '__file__', None)

    if module_file is None:
        return _get_fullname(cls)

    root_path_str = str(root_path)

    if not module_file.startswith(root_path_str):
        return _get_fullname(cls)

    relative_path = os.path.relpath(module_file, root_path_str)
    package_path = os.path.splitext(relative_path)[0].replace(os.sep, '.')

    return f'{package_path}.{cls.__qualname__}'


def _get_fullname(entity: Type[Any]) -> str:
    """
    Get the fully qualified name of a given entity.

    Parameters
    ----------
    entity : Type[Any]
        The entity for which the full name is required.

    Returns
    -------
    str
        Fully qualified name of the entity.
    """
    module = getattr(entity, '__module__', '')
    qualname = getattr(entity, '__qualname__', str(entity))

    if module:
        return module + '.' + qualname

    return qualname


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
        base_class
        for base_class in getattr(klass, '__bases__', [])
        if base_class.__name__ != 'object'
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

    # Extract attributes from the `__init__` method if defined there.
    fields.update(_get_init_attributes(klass))

    return ClassDef(
        fields=fields,
        methods=_methods,
    )


def _get_class_structure(klass: Type[Any], root_path: Path) -> ClassDef:
    if dataclasses.is_dataclass(klass):
        class_struct = _get_dataclass_structure(klass)
    elif inspect.isclass(klass):
        class_struct = _get_classic_class_structure(klass)
    else:
        raise Exception('The given class is not actually a class.')

    class_struct.module = klass.__module__
    class_struct.name = get_full_class_path(klass, root_path)

    class_struct.bases = []
    for ref_class in _get_base_classes(klass):
        class_struct.bases.append(get_full_class_path(ref_class, root_path))

    return class_struct


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

    if module_filename.endswith('.py'):
        module_name = module_filename[:-3]
    else:
        module_name = module_filename
    return module_path, module_name


def _get_classes_from_module(module_file_path: str) -> list[Type[Any]]:
    """
    Extract classes from a given module path using importlib.

    Parameters
    ----------
    module_file_path : str
        The path to the module file from which classes are to be extracted.

    Returns
    -------
    list
        A list of class objects.
    """
    module_path, module_name = _extract_module_name(module_file_path)
    original_path = copy.deepcopy(sys.path)

    sys.path.insert(0, module_path)
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, module_file_path
        )
        if spec is None:
            raise ImportError(f'Cannot find spec for {module_file_path}')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore
        sys.path = original_path

        all_classes_exported = []

        if hasattr(module, '__all__'):
            all_classes_exported = [
                getattr(module, name)
                for name in module.__all__
                if inspect.isclass(getattr(module, name))
            ]

        all_classes = [
            getattr(module, name)
            for name in dir(module)
            if inspect.isclass(getattr(module, name))
            and getattr(getattr(module, name), '__module__', None)
            == module.__name__
        ]
    except KeyboardInterrupt:
        raise_error('KeyboardInterrupt', 1)
    except Exception as e:
        short_module_path = '.'.join(module_path.split(os.sep)[-3:])
        print(f' Error loading module {short_module_path} '.center(80, '='))
        print(e)
        print('.' * 80)
        sys.path = original_path
        return []
    return all_classes + all_classes_exported


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
        if exclude:
            exclude_pattern = [
                exclude.strip() for exclude in exclude.split(',')
            ]
        else:
            exclude_pattern = []
        exclude_pattern.append('__pycache__')
        module_files.extend(
            _search_modules(path_str, exclude_pattern=exclude_pattern)
        )
    else:
        module_files.append(path_str)

    for file_path in module_files:
        classes_from_module = _get_classes_from_module(file_path)
        classes_list.extend(classes_from_module)
        if verbose:
            print('=' * 80)
            print(file_path)
            print(classes_from_module)

    return [_get_class_structure(cls, source) for cls in classes_list]


def dict_to_classdef(classes_list: list[dict[str, Any]]) -> list[ClassDef]:
    """Convert class metadata from dict to ClassDef."""
    classes_list_def: list[ClassDef] = []
    for klass_metadata in classes_list:
        classes_list_def.append(ClassDef(**klass_metadata))
    return classes_list_def
