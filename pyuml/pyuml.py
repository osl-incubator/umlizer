"""Main module template with example functions."""
import argparse

from pyuml import class_graph


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        '--class-diagram',
        dest='is_class_diagram',
        action='store_true',
        help='Generate a class diagram from a target.',
    )
    p.add_argument(
        '--target',
        dest='target',
        type=str,
        help='Specify the target directory/file',
    )
    p.add_argument(
        '--source',
        dest='source',
        type=str,
        help='Specify the source directory/file',
    )
    p.add_argument(
        '--verbose',
        dest='verbose',
        action='store_true',
        help='Print internal messages',
    )
    ns = p.parse_args()

    if ns.is_class_diagram:
        if not ns.target:
            raise Exception(
                '`target` parameter is required to generate the class diagram.'
            )
        if not ns.source:
            raise Exception(
                '`source` parameter is required to generate the class diagram.'
            )

        g = class_graph.create_class_diagram_from_source(
            ns.source, verbose=ns.verbose
        )
        g.format = 'png'
        g.render(ns.target)


if __name__ == '__main__':
    main()
