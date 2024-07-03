"""Create graphviz for classes."""
from __future__ import annotations

from typing import Any, cast

import graphviz as gv

from umlizer.inspector import ClassDef


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

        if m_params and len(m_params) > 20:  # noqa: PLR2004
            indent = '\\l&nbsp;&nbsp;&nbsp;&nbsp;'
            m_params = indent + m_params.replace(', ', f',{indent}') + '\\l'

        methods_raw.append(f'{m_visibility} {m_name}({m_params}): {m_type}')

    methods = '\\l'.join(methods_raw) + '\\l'

    # Combine class name, fields, and methods into the UML node format
    uml_representation = '{' + f'{class_name}|{fields}|{methods}' + '}'
    return uml_representation


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
