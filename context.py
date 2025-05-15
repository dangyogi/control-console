# context.py

r'''Various contexts

First step, building individual reusable components, like "line":

1. Create any bases that might be shared by multiple components:

    >>> from exp import *         # I, T and F
    >>> from alignment import *   # S, C and E
    >>> from context import Base, Instance, Context

    >>> BLACK = "BLACK"

    >>> area = Base(x_left=I.x_pos.S(I.width), x_center=I.x_pos.C(I.width), x_right=I.x_pos.E(I.width),
    ...             y_top=I.y_pos.S(I.height), y_middle=I.y_pos.C(I.height), y_bottom=I.y_pos.E(I.height),
    ...             flipped=False)

2. Create a Base that has the default settings.  This includes the settings defined in area:

    >>> line_base = area(width=3, color=BLACK, height=I.length)

3. Define an Instance class with the methods:

    >>> class line(Instance):
    ...     base = line_base
    ...
    ...     def draw(self, template=None, **kwargs):
    ...         attrs = Context(self, template, **kwargs)
    ...         if attrs.flipped:
    ...             print(f"draw horz line from ({attrs.x_left}, {attrs.y_middle}) "
    ...                   f"to ({attrs.x_right}, {attrs.y_middle}), "
    ...                   f"width {attrs.width} and color {attrs.color}")
    ...         else:
    ...             print(f"draw vert line from ({attrs.x_center}, {attrs.y_top}) "
    ...                   f"to ({attrs.x_center}, {attrs.y_bottom}), "
    ...                   f"width {attrs.width} and color {attrs.color}")

4. Because no T expressions were used in any of this, this can be run without a template:

    >>> a_line = line(x_pos=S(10), y_pos=S(30), length=20)
    >>> a_line.draw()
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

from exp import *


Trace = False


class Base_base:
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

class Base(Base_base):
    r'''So we can do obj.attr, rather than obj['attr'].  Just looking for cleaner syntax...

        >>> a = Base(width=9, height=19)
        >>> a.width
        9
        >>> a.height
        19
    '''
    def __call__(self, **kwargs):
        r'''Create a specialized Base from this Base.
        '''
        return Base(self, **kwargs)

class Instance(Base_base):
    r'''An Instance of a Base object.

    Subclass this and set the class "base" variable to it's Base object:

        >>> from context import Base, Instance, Context

        >>> my_base = Base(width=9, height=19)

        >>> class my_inst(Instance):
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

    To place expressions in the Base that would apply to each Instance, use the exp module:

        >>> from exp import *

    And, we'll need alignments:

        >>> from alignment import *   # S, C and E

    The I in the exp module refers to the Instance of the Base, which will be defined later:

        >>> my_base = Base(sum=I.a + I.b, b=40)

        >>> class my_inst(Instance):
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

    Finally, the Instance class may have methods on it.  But this presents two problems:

    1. We want the I exp's to have access to the parameters to the method, as if they were attributes
       on the Instance.  But we don't want these values to remain on the Instance after the method call
       completes.

    2. When the method accesses an Instance attribute (through self.X), we want expressions evaluated.

       The solution to both of the problems is to create an Context object!  This inherits attrs from
       self and evaluates the inherited expression values.

        >>> my_base = Base(x_left=I.x_pos.S(I.width), width=9)

        >>> class my_inst(Instance):
        ...     base = my_base
        ...
        ...     def my_method(self, template=None, **kwargs):     # same arguments to all methods!
        ...         attrs = Context(self, template, **kwargs)     # this line is always the same!
        ...         # x_pos and width are stored on attrs:
        ...         print(f"{attrs.x_pos=}, {attrs.width=}")
        ...         # and inherited values are evaluated:
        ...         print(f"{attrs.x_left=}")

        >>> my_a = my_inst()

        # note that during the call, x_pos and width are set in the Context, while x_left is inherited
        # from self.
        >>> my_a.my_method(x_pos=C(100), width=51)
        attrs.x_pos=C(100), attrs.width=51
        attrs.x_left=S(75)

        # after the call...
        >>> my_a.width   # still the default value
        9
        >>> my_a.x_pos   # still not set
        Traceback (most recent call last):
        ...
        AttributeError: x_pos

    3. To store permanent values on the Instance, just assign them to self.

        >>> my_base = Base(x=1, num_calls=0)

        >>> class my_inst(Instance):
        ...     base = my_base
        ...
        ...     def my_method(self, template=None, **kwargs):     # same arguments to all methods!
        ...         attrs = Context(self, template, **kwargs)     # this line is always the same!
        ...         self.x = attrs.x
        ...         self.num_calls = attrs.num_calls + 1

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

    def init(self, template=None, **kwargs):
        pass

    def get(self, name, template=None):
        if Trace:
            print(f"Instance.get {name=}, {self=}, {template=}")
        return eval_exp(getattr(self, name), self, template)

    #def do(self, name, template, **attrs):  # Don't know how to implement the attrs...
    #    fn = self.get(name, template)  # This is assumed to be a method on self
    #    fn(self, template)


class Context:
    def __init__(self, inst, template, **kwargs):
        self.inst = inst
        self.template = template
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        r'''Accesses attr from inst.
        '''
        if Trace:
            print(f"Context.__getattr__, {name=}, calling get on {self.inst=}")
        value = getattr(self.inst, name)
        if Trace:
            print(f"... getattr got {value=}")
        templ = self.inst if isinstance(self.inst, Template) else self.template
        if Trace:
            print(f"Context.__getattr__ {name=}, {self.inst=}, {templ=}")
        ans = eval_exp(value, self, templ)
        if Trace:
            print(f"... eval_exp got {ans=}")
        return ans


area = Base(
         x_left=I.x_pos.S(I.width), x_center=I.x_pos.C(I.width), x_right=I.x_pos.E(I.width),
         y_top=I.y_pos.S(I.height), y_middle=I.y_pos.C(I.height), y_bottom=I.y_pos.E(I.height),
         x_next=I.x_right.as_S(), y_next=I.y_bottom.as_S(), as_sprite=False, dynamic_capture=False)

class Template(Instance):
    base = area

    def init(self, template=None, **kwargs):
        r'''Sets width and height
        '''
        super().init(template, **kwargs)
        attrs = Context(self, template, **kwargs)         # I'm only the Template for my components
        print("Template.init", template)
        x_left = 10000000
        x_right = -10000000
        y_top = 10000000
        y_bottom = -10000000
        for i, component in enumerate(attrs.components, 1):
            print("Template.init doing component.init", i)
            component.init(self)
        for i, component in enumerate(attrs.components, 1):
            print("Template.init getting pos's from component", i)
            xl = component.get('x_left', self).i
            if xl < x_left:
                x_left = xl
            xr = component.get('x_right', self).i
            if xr > x_right:
                x_right = xr
            yt = component.get('y_top', self).i
            if yt < y_top:
                y_top = yt
            yb = component.get('y_bottom', self).i
            if yb > y_bottom:
                y_bottom = yb
        self.width = x_right - x_left
        assert isinstance(attrs.width, int), f"Template.init got non-integer width {attrs.width}"
        self.height = y_bottom - y_top 
        assert isinstance(attrs.height, int), f"Template.init got non-integer height {attrs.height}"
        print(f"Template.init: {attrs.width=}, {attrs.height=}")
        if attrs.as_sprite:
            self.sprite = sprite.Sprite(self.width, self.height, attrs.dynamic_capture)

    def draw(self, template=None, **kwargs):
        attrs = Context(self, template, **kwargs)
        #self.x_left = S(min(component.get('x_left', self).i
        #                    for component in attrs.components))
        #self.x_right = E(max(component.get('x_right', self).i
        #                     for component in attrs.components))
        #self.width = self.x_right.i - self.x_left.i
        #self.x_center = attrs.x_right.C(attrs.width)
        #self.y_top = S(min(component.get('y_top', self).i
        #                   for component in attrs.components))
        #self.y_bottom = E(max(component.get('y_bottom', self).i
        #                      for component in attrs.components))
        #self.height = attrs.y_bottom.i - attrs.y_top.i
        #self.y_middle = attrs.y_top.C(attrs.height)
        if self.as_sprite:
            self.sprite.save_pos(attrs.x_left, attrs.y_top)
        for i, component in enumerate(attrs.components, 1):
            print("Template.draw doing component draw", i)
            component.draw(self)

import sprite



if __name__ == "__main__":
    import doctest
    doctest.testmod()
