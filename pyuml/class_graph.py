import dataclasses
import inspect
import types
import os
import glob
import importlib.util

import graphviz as gv

def _get_fullname(entity):
    return '{}.{}'.format(entity.__module__, entity.__name__)


def _get_methods(entity) -> list:
    return [
        k for k, v in entity.__dict__.items()
        if not k.startswith('__') and isinstance(v, types.FunctionType)
    ]

def _get_dataclass_structure(klass):
    result = {'fields': {}, 'methods': _get_methods(klass)}

    result['fields'].update({
        k: v.type.__name__
        for k, v in klass.__dataclass_fields__.items()
    })
    return result


def _get_base_classes(klass):
    return [
        c for c in klass.__mro__
        if c.__name__ != 'object' and c.__name__ != klass.__name__
    ]


def _get_classicclass_structure(klass):
    _methods = _get_methods(klass)

    result = {
        'fields': {
            k: klass.__annotations__.get(k, object).__name__
            for k in klass.__dict__.keys()
            if not k.startswith('__') and k not in _methods
        },
        'methods': _methods
    }
    return result


def _get_class_structure(klass):
    if dataclasses.is_dataclass(klass):
        return _get_dataclass_structure(klass)
    elif inspect.isclass(klass):
        return _get_classicclass_structure(klass)


def _get_entity_class_html(entity):
    class_template = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="1" CELLPADDING="1">
      <TR>
        <TD>{}</TD>
      </TR>
      <TR>
        <TD>
          <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">
          {}
          </TABLE>
        </TD>
      </TR>
      <TR>
        <TD>
          <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">
          {}
          </TABLE>
        </TD>
      </TR>
    </TABLE>>'''

    class_name_template = '<BR ALIGN="LEFT" />  <I>{}.{} {}</I> <BR ALIGN="LEFT" />'
    row_key_value_template = '<TR><TD>{}: {}</TD></TR>'
    row_key_template = '<TR><TD>{}</TD></TR>'

    empty_row = '<TR><TD></TD></TR>'
    base_classes = ', '.join([
        _get_fullname(c) for c in _get_base_classes(entity)
    ])

    if base_classes != '':
        base_classes = '({})'.format(base_classes)


    class_structure = _get_class_structure(entity)

    class_name = class_name_template.format(
        entity.__module__, entity.__qualname__, base_classes
    )
    attributes = ''.join([
        row_key_value_template.format(
            k, v
        ) for k, v in class_structure['fields'].items()
    ])

    methods = ''.join([
        row_key_template.format(k)
        for k in class_structure['methods']
    ])

    return class_template.format(
        class_name,
        attributes if attributes else empty_row,
        methods if methods else empty_row
    )


def _search_modules(target: str, exclude_pattern=['__pycache__']) -> list:
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


def _get_classes_from_module(module_path: str) -> list:
    spec = importlib.util.spec_from_file_location(
        _extract_filename(module_path),
        module_path
    )
    module = importlib.util.module_from_spec(spec)

    classes_list = []

    try:
        spec.loader.exec_module(module)
        for o in module.__dir__():
            if o.startswith('__'):
                continue
            klass = getattr(module, o)
            if inspect.isclass(klass):
                classes_list.append(klass)
    except Exception as e:
        print(' {} '.format(module_path).center(80, '='))
        print(e)
        print('.' * 80)
    return classes_list


def create_class_diagram(classes_list):
    g = gv.Digraph(comment='Graph')
    g.attr('node', shape='none', rankdir='BT')

    edges = []
    for c in classes_list:
        g.node(_get_fullname(c), _get_entity_class_html(c))

        for b in _get_base_classes(c):
            edges.append((_get_fullname(b), _get_fullname(c)))

    g.edges(edges)
    return g


def create_class_diagram_from_source(target: str):
    classes_list = []

    if not os.path.exists(target):
        raise Exception('Path "{}" doesn\'t  exist.'.format(target))
    if os.path.isdir(target):
        for f in _search_modules(target):
            classes_list.extend(_get_classes_from_module(f))
    return create_class_diagram(classes_list)
