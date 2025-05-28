# property_test.py


class foo:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def bar(self):    # setting f.bar raises:
                      #   AttributeError: property 'bar' of 'foo' object has no setter
        return 4

    def baz(self):    # setting f.baz hides this method
        return 5

    @property         # setting f.bogus raises:
                      #   RecursionError: maximum recursion depth exceeded
    def bogus(self):
        return 6

    @bogus.setter
    def bogus(self, value):
        self.bogus = value

    @property
    def bingo(self):  # also gets RecursionError 
        return 7

    @bogus.setter
    def bingo(self, value):
        super().__setattr__('bingo', value)

    @property
    def bob(self):
        print("getter bob")
        return self._bob

    @bob.setter
    def bob(self, value):
        print("setter bob")
        self._bob = value

f = foo()

print(f.baz)
f.baz = 8
print(f.baz)

#print(f.bogus)
#f.bogus = 9     # fails
#print(f.bogus)

#print(f.bar)
#f.bar = 10      # fails
#print(f.bar)

#print(f.bingo)  # fails
#f.bingo = 11
#print(f.bingo)

f.bob = 12
print(f.bob)

g = foo(bob=77)
print(g.bob)
