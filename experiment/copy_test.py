# copy_test.py

from copy import copy, deepcopy
import copyreg

class foo:
    def __init__(self, a):
        self.a = a

    def __copy__(self):   # takes precedence over copyreg
        print("foo.__copy__", self.a)
        return foo(self.a)

    #def __deepcopy__(self, memo):    # takes precedence over copyreg
    #    print("foo.__deepcopy__", self.a)
    #    return foo(deepcopy(self.a, memo))

    def __deepcopy__(self, memo):    # takes precedence over copyreg
        print("foo.__deepcopy__", self.a)
        return super().__deepcopy__(memo)

def pickle_foo(f):
    print("pickle_foo", f)
    return foo, (f.a,)

#copyreg.pickle(foo, pickle_foo)

f = foo(4)
g = foo(f)
f.a = g

copy(f)

g2 = deepcopy(g)
print(f"{g=}, {g.a=}, {g.a.a=}")
print(f"{g2=}, {g2.a=}, {g2.a.a=}")
