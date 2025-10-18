# dump_yaml.py

import sys
from yaml import safe_load_all, dump


def read_yaml(filename, fn):
    with open(filename, "r") as file:
        for document in safe_load_all(file):
            fn(document)

def dump_yaml(document):
    sys.stdout.write(dump(document))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--print", "-p", action="store_true", default=False)
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    if args.print:
        read_yaml(args.yaml_file, print)
    else:
        read_yaml(args.yaml_file, dump_yaml)
