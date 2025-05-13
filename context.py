# context.py

r'''Various contexts

First step, building individual reusable components, like "line":

1. Create any bases that might be shared by multiple components:

    >>> from exp import *         # I, T and F
    >>> from alignment import *   # S, C and E

    >>> BLACK = "BLACK"

    >>> area = base(x_left=I.x_pos.S(I.width), x_center=I.x_pos.C(I.width), x_right=I.x_pos.E(I.width),
    ...             y_top=I.y_pos.S(I.height), y_middle=I.y_pos.C(I.height), y_bottom=I.y_pos.E(I.height),
    ...             flipped=False)

2. Create a base that has the default settings.  This includes the settings defined in area:

    >>> line_base = area(width=3, color=BLACK, height=I.length)

3. Define an instance class with the methods:

    >>> class line(instance):
    ...     base = line_base
    ...
    ...     def draw(self, template=None, **kwargs):
    ...         with self.store(template, **kwargs):
    ...             if self.flipped:
    ...                 print(f"draw horz line from ({self.x_left}, {self.y_middle}) "
    ...                       f"to ({self.x_right}, {self.y_middle}), "
    ...                       f"width {self.width} and color {self.color}")
    ...             else:
    ...                 print(f"draw vert line from ({self.x_center}, {self.y_top}) "
    ...                       f"to ({self.x_center}, {self.y_bottom}), "
    ...                       f"width {self.width} and color {self.color}")

4. Because no T expressions were used in any of this, this can be run without a template:

    >>> a_line = line(x_pos=S(10), y_pos=S(30), length=20)
    >>> a_line.draw()
    draw vert line from (C(11), S(30)) to (C(11), E(49)), width 3 and color BLACK


build a base template
with template(...) as foo:  # also sets Under_construction global var
    foo.a = comp_a(...)          # no foo
    foo.b = comp_b(bar=t.a.foo)  # creates a dynamic reference to foo rather than raise AttributeError
                               # because we're Under_construction!
    .
    .
    .
    class foo_instance(instance):
        base = foo

# create an instance of the template
foo_1 = foo_instance(...)
foo_2 = foo_instance(...)

foo_1.draw(...)   # foo_1 passed as parameter, not global variable
'''

import exp


Current_template = None

class base_base:
    def __init__(self, parent=None, **values):
        self.parent = parent
        for key, value in values.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        r'''Raises AttributeError if name not set.
        '''
        if self.parent is not None:
            return getattr(self.parent, name)
        raise AttributeError(name)

class base(base_base):
    r'''So we can do obj.attr, rather than obj['attr'].  Just looking for cleaner syntax...

        >>> a = base(width=9, height=19)
        >>> a.width
        9
        >>> a.height
        19
    '''
    def __call__(self, **kwargs):
        r'''Create a specialized base from this base.
        '''
        return base(self, **kwargs)

class instance(base_base):
    r'''An instance of a base object.

    Subclass this and set the class "base" variable to it's base object:

        >>> my_base = base(width=9, height=19)

        >>> class my_inst(instance):
        ...     base = my_base

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

    To place expressions in the base that would apply to each instance, use the exp module:

        >>> from exp import *

    And, we'll need alignments:

        >>> from alignment import *   # S, C and E

    The I in the exp module refers to the instance of the base, which will be defined later:

        >>> my_base = base(sum=I.a + I.b, b=40)

        >>> class my_inst(instance):
        ...     base = my_base

        >>> my_a = my_inst(a=20)
        >>> my_a.sum          # oops!
        I.a + I.b
        >>> my_a.get('sum')   # use get to evaluate expressions
        60
        >>> my_a.get('a')     # you can use get for everything, it leaves non exp's alone
        20
        >>> my_a.get('b')     # you can use get for everything, it leaves non exp's alone
        40

        >>> my_b = my_inst(a=10)
        >>> my_b.get('sum')   # use get to evaluate expressions
        50

    Finally, the instance class may have methods on it.  But this presents two problems:

    1. We want the I exp's to have access to the parameters to the method, as if they were attributes
       on the instance.  But we don't want these values to remain on the instance after the method call
       completes.

    2. When the method accesses an instance attribute (through self.X), we want expressions evaluated.

       The solution to both of the problems is the "store" method on the instance:

        >>> my_base = base(x_left=I.x_pos.S(I.width), width=9)

        >>> class my_inst(instance):
        ...     base = my_base
        ...
        ...     def my_method(self, template=None, **kwargs):           # same arguments to all methods!
        ...         with self.store(template, **kwargs) as store_self:  # this line is always the same!
        ...             # x_pos and width are stored on the instance:
        ...             print(f"{self.x_pos=}, {self.width=}")
        ...             # so that exp's work:
        ...             print(f"{self.x_left=}")

        >>> my_a = my_inst()

        # note that during the call, x_pos is set, and the default value for width have been overridden
        >>> my_a.my_method(x_pos=C(100), width=51)
        self.x_pos=C(100), self.width=51
        self.x_left=S(75)

        # after the call...
        >>> my_a.width   # reverts back to default value
        9
        >>> my_a.x_pos   # no longer set
        Traceback (most recent call last):
        ...
        AttributeError: x_pos

    3. "store_self" is used to store permanent values on the instance that won't go away when the
       method returns.

        >>> my_base = base(x=1, num_calls=0)

        >>> class my_inst(instance):
        ...     base = my_base
        ...
        ...     def my_method(self, template=None, **kwargs):           # same arguments to all methods!
        ...         with self.store(template, **kwargs) as store_self:  # this line is always the same!
        ...             store_self.x = self.x
        ...             store_self.num_calls = self.num_calls + 1       # += doesn't work here!

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
    def __init__(self, **values):
        super().__init__(self.base, **values)

    def __getattr__(self, name):
        try:
            ans = super().__getattr__(name)
        except AttributeError:
            if Under_construction:
                return exp_getattr(self, name)
            raise
        if hasattr(self, '_template'):
            ans = self.eval(ans, self._template)
        return ans

    def init(self, template=None):
        pass

    def store(self_instance, template=None, **kwargs):
        r'''Simulates temporary variables that only live as long as the with statement body.

        It stores the variable as attributes on self.  They can be accessed within the with statement
        simply as: self.foo.
        '''
        class context_manager:
            def __init__(self):
                self._reset = {}
                self._delete = []

            def __enter__(self):
                assert not hasattr(self, '_template'), \
                       f"store called with template already set to {self._template}"
                self._delete.append('_template')
                self_instance._template = template
                for key, value in kwargs.items():
                    if key in self.__dict__:
                        self._reset[key] = self.key
                    else:
                        self._delete.append(key)
                    setattr(self_instance, key, value)

                class setter:
                    def __setattr__(_, name, value):
                        if name in self._delete:
                            self._delete.remove(name)
                        if name in self._reset:
                            del self._reset[name]
                        setattr(self_instance, name, value)
                return setter()

            def __exit__(self, *excs):
                for key, value in self._reset.items():
                    setattr(self_instance, key, value)
                for name in self._delete:
                    delattr(self_instance, name)
                return False
        return context_manager()

    def eval(self, x, template=None):
        if isinstance(x, exp.exp):
            x = x.eval(self, template)
        return x

    def get(self, name, template=None):
        return self.eval(getattr(self, name), template)

    #def do(self, name, template, **attrs):  # Don't know how to implement the attrs...
    #    fn = self.get(name, template)  # This is assumed to be a method on self
    #    fn(self, template)


Under_construction = False

class template(base):
    def __enter__(self):
        global Under_construction
        self.under_construction = Under_construction
        Under_construction = True
        return self

    def __exit__(self, *excs):
        global Under_construction
        Under_construction = self.under_construction
        return False



if __name__ == "__main__":
    import doctest
    doctest.testmod()
