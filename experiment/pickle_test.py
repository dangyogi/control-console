# pickle_test.py

from pickle import dumps, loads
from yaml import safe_load


def read_yaml(filename):
    with open(filename, "r") as file:
        return safe_load(file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    data = read_yaml(args.yaml_file)
    print(dumps(data, 0))
