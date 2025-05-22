# str_repr_test.py


class str_test:
    def __str__(self):
        return "str_test.__str__"

class repr_test:
    def __repr__(self):
        return "repr_test.__repr__"

class str_repr_test:
    def __str__(self):
        return "str_repr_test.__str__"

    def __repr__(self):
        return "str_repr_test.__repr__"


s = str_test()
print(f"{s=}")

r = repr_test()
print(f"{r=}")

sr = str_repr_test()
print(f"{sr=}")
