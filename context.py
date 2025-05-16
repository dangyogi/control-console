# context.py

r'''Various contexts

First step, building individual reusable components, like "line":

1. Create any bases that might be shared by multiple components:

    >>> from exp import *         # I, T and F
    >>> from alignment import *   # S, C and E
    >>> from context import Instance, extend

    >>> BLACK = "BLACK"

2. Define an Instance class with the methods:

    >>> class line(Instance):
    ...     width = 3
    ...     color = BLACK
    ...     @property
    ...     def height(self):
    ...         return self.length
    ...
    ...     def draw2(self):
    ...         print(f"draw vert line from ({self.x_center}, {self.y_upper}) "
    ...               f"to ({self.x_center}, {self.y_lower}), "
    ...               f"width {self.width} and color {self.color}")

4. Because no T expressions were used in any of this, this can be run without a template:

    >>> a_line = line(x_pos=S(10), y_pos=S(30), length=20)
    >>> _ = a_line.draw()
    draw vert line from (C(11), S(30)) to (C(11), E(49)), width 3 and color BLACK


# FIX this mess!
build a base template
with template(...) as foo:  # also sets Under_construction global var
    foo.a = comp_a(...)          # no foo
    foo.b = comp_b(bar=t.a.foo)  # creates a dynamic reference to foo rather than raise AttributeError
                                 # because we're Under_construction!
    .
    .
    .
    class foo_instance(Instance):
        base = foo

# create an Instance of the template
foo_1 = foo_instance(...)
foo_2 = foo_instance(...)

foo_1.draw(...)   # foo_1 passed as parameter, not global variable
'''

from copy import copy, deepcopy
from alignment import *
from exp import eval_exp


Trace = False


class Box:
    r'''Provides additional attributes to rectangular boxes.

        >>> from alignment import *

        >>> b = Box()

        # When the box is provided these attributes by the subclass:
        >>> b.width = 9
        >>> b.height = 5
        >>> b.x_pos = C(200)
        >>> b.y_pos = C(100)

        # You get the following for free!
        >>> b.x_left
        S(196)
        >>> b.x_center
        C(200)
        >>> b.x_right
        E(204)
        >>> b.x_next
        S(204)
        >>> b.y_upper
        S(98)
        >>> b.y_middle
        C(100)
        >>> b.y_lower
        E(102)
        >>> b.y_next
        S(102)
    '''

    @property
    def x_left(self):
        return self.x_pos.S(self.width)

    @property
    def x_center(self):
        return self.x_pos.C(self.width)

    @property
    def x_right(self):
        return self.x_pos.E(self.width)

    @property
    def y_upper(self):
        return self.y_pos.S(self.height)

    @property
    def y_middle(self):
        return self.y_pos.C(self.height)

    @property
    def y_lower(self):
        return self.y_pos.E(self.height)

    @property
    def x_next(self):
        return self.x_right.as_S()

    @property
    def y_next(self):
        return self.y_lower.as_S()


class Instance(Box):
    r'''An Instance of something drawable.


        >>> from context import Instance, extend

        >>> class my_inst(Instance):
        ...     width = 9
        ...     height = 19

        >>> my_a = my_inst(x=20, y=200)
        >>> my_a.x
        20
        >>> my_a.width
        9

        >>> my_b = my_inst(x=20, width=15)
        >>> my_b.x
        20
        >>> my_b.width
        15
        >>> my_b.height
        19

    And, we'll need alignments:

        >>> from alignment import *   # S, C and E

        >>> class my_inst(Instance):
        ...     b = 40
        ...
        ...     @property
        ...     def sum(self):
        ...         return self.a + self.b

        >>> my_a = my_inst(a=20)
        >>> my_a.sum          # oops!
        60
        >>> my_a.a
        20
        >>> my_a.b
        40

        >>> my_b = my_inst(a=10)
        >>> my_b.sum   # use get to evaluate expressions
        50

    Finally, the Instance class may have methods on it.  But this presents two problems:

    1. We want the I exp's to have access to the parameters to the method, as if they were attributes
       on the Instance.  But we don't want these values to remain on the Instance after the method call
       completes.

    2. When the method accesses an Instance attribute (through self.X), we want expressions evaluated.

       The solution to both of the problems is to push the parameters temporarily to the Instance
       in a context manager (with statement), and restore them on exit from the with statement.

        >>> class my_inst(Instance):
        ...     @property
        ...     def x_left(self):
        ...         return self.x_pos.S(self.width)
        ...
        ...     width = 9
        ...
        ...     def my_method(self, **kwargs):             # same arguments to all methods!
        ...         with self.push(**kwargs) as setattr:   # this line is always the same!
        ...             # x_pos and width are temporarily set on self.
        ...             print(f"{self.x_pos=}, {self.width=}")
        ...             # and inherited values are evaluated:
        ...             print(f"{self.x_left=}")

        >>> my_a = my_inst()
        >>> my_a.x_pos   # default
        S(100)

        # note that during the call, x_pos and width are set in attrs, while x_left is inherited
        # from self.
        >>> my_a.my_method(x_pos=C(200), width=51)
        self.x_pos=C(200), self.width=51
        self.x_left=S(175)

        # after the call...
        >>> my_a.width   # still the default value
        9
        >>> my_a.x_pos   # still old value
        S(100)

    3. To store permanent values on the Instance, just assign them to self.

        >>> class my_inst(Instance):
        ...     x = 1
        ...     num_calls = 0
        ...
        ...     def my_method(self, **kwargs):            # same arguments to all methods!
        ...         with self.push(**kwargs) as setattr:  # this line is always the same!
        ...             setattr('x', self.x)
        ...             setattr('num_calls', self.num_calls + 1)

        >>> my_a = my_inst()
        >>> my_a.x
        1
        >>> my_a.num_calls
        0
        >>> my_a.my_method(x=7)
        >>> my_a.x
        7
        >>> my_a.num_calls
        1
    '''
    as_sprite = False
    dynamic_capture = False
    initialized = False
    x_pos = S(100)
    y_pos = S(100)
    trace = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if self.trace:
            print(f"{self}.__init__: {self.trace=}, {self.get_raw('x_pos')=}, "
                  f"{self.get_raw('y_pos')=}, {kwargs=}")

    def get_raw(self, name):
        r'''Gets unevaluated value.
        '''
        return super().__getattribute__(name)

    def __getattribute__(self, name):
        raw = super().__getattribute__(name)
        return eval_exp(raw, self)

    def init(self):
        if not self.initialized:
            self.init2()
            if self.as_sprite:
                self.sprite = sprite.Sprite(self.width, self.height, self.dynamic_capture)
            self.initialized = True
            if self.trace:
                print(f"{self}.init: {self.x_pos=}, {self.y_pos=}")

    def init2(self):
        pass

    def push(self, **kwargs):
        return push_cm(self, **kwargs)

    def draw(self, retattr=None, **kwargs):
        if self.trace:
            print(f" = = = = = = = = = = = {self}.draw: {kwargs=}")
        with self.push(**kwargs) as setattr:
            if self.trace:
                print(f"{self}.draw: {self.x_pos=}, {self.y_pos=}")
            if self.as_sprite:
                self.sprite.save_pos(self.x_left, self.y_upper)
            if self.trace:
                print(f" = = = = = = = = = = = {self}.draw: calling {self}.draw2()")
            self.draw2()
            if retattr is not None:
                return getattr(self, retattr)

    def draw2(self):
        pass

    # FIX: Do we still need this?
    #def get(self, name):
    #    if Trace:
    #        print(f"Instance.get {name=}, {self=}, {template=}")
    #    return eval_exp(getattr(self, name), self, template)


class push_cm:
    def __init__(self, inst, **kwargs):
        self.inst = inst
        self.kwargs = kwargs

    def __enter__(self):
        self.deletes = set()
        self.resets = []

        d = self.inst.__dict__
        for key, value in self.kwargs.items():
            if key in d:
                self.resets[key] = d[key]     # save old value to restore at __exit__
            else:
                self.deletes.add(key)         # set of keys to delete at __exit__
            setattr(self.inst, key, value)
        return self.setattr

    def setattr(self, key, value):
        if key in self.deletes:
            self.deletes.remove(key)
        if key in self.resets:
            del self.resets[key]
        setattr(self.inst, key, value)

    def __exit__(self, *excs):
        for key, old_value in self.resets:
            setattr(self.inst, key, old_value)
        for key in self.deletes:
            delattr(self.inst, key)
        return False


def extend(inst, **kwargs):
    r'''Please note that assigning to the copy does not affect the original inst.
    '''
    ans = deepcopy(inst)
    for key, value in kwargs.items():
        setattr(ans, key, value)
    if inst.trace:
        assert ans.trace
        print(f"extend: {inst=} becomes {ans=}, {ans.x_pos=}, {ans.y_pos=}, {kwargs=}")
    return ans


import sprite



if __name__ == "__main__":
    import doctest
    doctest.testmod()
