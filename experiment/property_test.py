# property_test.py


class foo:
    @property
    def bar(self):
        return 4


f = foo()
print(f.bar)
f.bar = 7
print(f.bar)
