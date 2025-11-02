# dump_yaml.py

import sys
from yaml import safe_load, dump


def read_yaml(filename):
    with open(filename, "r") as file:
        return safe_load(file)

def dump_yaml(document):
    #sys.stdout.write(dump(document))
    dump(document, sys.stdout)
    #dump(document, sys.stdout, default_flow_style=True)

def print_list(document):
    for str in document:
        print(repr(str))

def print_dict(document):
    for key, value in document.items():
        print(repr(key), repr(value))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--print-list", "-l", action="store_true", default=False)
    parser.add_argument("--print-dict", "-d", action="store_true", default=False)
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    if args.print_list:
        print_list(read_yaml(args.yaml_file))
    if args.print_dict:
        print_dict(read_yaml(args.yaml_file))
    else:
        dump_yaml(read_yaml(args.yaml_file))
