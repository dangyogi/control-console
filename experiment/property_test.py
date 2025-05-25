# property_test.py


class foo:
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


f = foo()

print(f.baz)
f.baz = 8
print(f.baz)

#print(f.bogus)
#f.bogus = 9   # fails
#print(f.bogus)

#print(f.bar)
#f.bar = 10    # fails
#print(f.bar)

print(f.bingo)
f.bingo = 11
print(f.bingo)
