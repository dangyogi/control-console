# compiler.py

import argparse

from yaml import safe_load_all

from indenter import indenter
from widgets import *


def read_yaml(yaml_filename, trace_widgets):
    with open(yaml_filename, "r") as yaml_file:
        for document in safe_load_all(yaml_file):
            process(document, trace_widgets)

def process(document, trace_widgets):
    if 'module' in document:
        filename = document['module'] + '.py'
        print()
        print("module", filename)
        with open(filename, 'w') as out_file:
            output = indenter(out_file, width=94)
            output.print("#", filename)
            output.print()
            if 'import' in document:
                for imp in document['import']:
                    output.print(imp)
                output.print()
                output.print()
            if 'include' in document:
                text = document['include'].rstrip()
                output.print(text)
                output.print()
            if 'widget_stubs' in document:
                for name, args in document['widget_stubs'].items():
                    Widgets[name] = widget_stub(name, layout=args.get('layout', ()),
                                                      appearance=args.get('appearance', ()))
            words = compile(document, output, trace_widgets)
            output.print()
            output.print_head(f"__all__ = (", first_comma=False)
            for word in words + document.get('add_to_all', []):
                output.print_arg(f'"{word}"')
            output.print_tail(')')
            output.print()

def compile(document, output, trace_widgets):
    words = []
    for name in document.keys():
        if name not in 'module import include add_to_all widget_stubs'.split():
            spec = document[name]
            if spec.get('skip', False):
                continue
            trace = name in trace_widgets  # turns on trace: from yaml
            print("  compiling", name)
            spec_copy = spec.copy()
            for cls in Widget_types:
                cls_name = cls.__name__
                if cls_name in spec_copy:
                    widget = cls(name, spec_copy, output, trace)
                    break
            else:
                raise ValueError(f"compile: unknown spec type for {name=}")
            widget.generate_widget()
            if not widget.skip:
                words.append(name)
    return words


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", '-t', nargs='+', default=(), help="list of widgets to trace")
    parser.add_argument("yaml_file")

    args = parser.parse_args()
    print("args", args)

    read_yaml(args.yaml_file, args.trace)



if __name__ == "__main__":
    run()
