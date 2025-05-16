# param_test.py

from itertools import permutations
from random import sample

def foo(**kwargs):
    return list(kwargs.keys())

def test(names):
    kwargs = {n: i for i, n in enumerate(names, 1)}
    result = foo(**kwargs)
    if names != result:
        print("names", names)
        print("result", result)
        print("failed for names", ''.join(names))
        print("got result      ", ''.join(result))
        raise AssertionError

def go_nuts(names):
    for i in range(2, len(names)):
        check_perms(names, i)

def check_perms(names, len):
    for _ in range(10000):
        test(sample(names, len))

letters = 'abcdefghijklmnopqrstuvwxyz'

#print(f"{sample(letters, 4)=}")

go_nuts(letters)
