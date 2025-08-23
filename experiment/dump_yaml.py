# dump_yaml.py

import sys
from yaml import safe_load_all, dump


def dump_yaml(filename):
    with open(filename, "r") as file:
        for document in safe_load_all(file):
            sys.stdout.write(dump(document))



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    dump_yaml(args.yaml_file)
