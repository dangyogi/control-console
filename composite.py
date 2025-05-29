# composite.py

r'''Defines the Composite class:

# FIX this mess
build a base template
with template(...) as foo:  # also sets Under_construction global var
    foo.a = comp_a(...)          # no foo
    foo.b = comp_b(bar=t.a.foo)  # creates a dynamic reference to foo rather than raise AttributeError
                                 # because we're Under_construction!
    .
    .
    .
    class foo_instance(Drawable):
        base = foo

# create an instance of the composite
foo_1 = foo_instance(...)
foo_2 = foo_instance(...)

foo_1.draw(...)   # foo_1 passed as parameter, not global variable
'''

from pyray import *

#import texture
from alignment import *
from exp import *
from drawable import Drawable
from shapes import *


__all__ = ("Composite", "Column", "Row", "Stack")


class Composite(Drawable):
    def __init__(self, components, **kwargs):
        super().__init__(**kwargs)
        self.components = components
        for component in components:
            component.parent = self
            if hasattr(component, 'name'):
                setattr(self, component.name, component)

    def copy(self, **kwargs):
        if hasattr(self, 'aka'):
            parts = self.aka.split('.', 1)
            if len(parts) == 2:
                aka, suffix = parts
                if suffix.isdigit():
                    return self.copy2(aka=f"{aka}.{int(suffix)+1}", **kwargs)
            return self.copy2(aka=f"{self.aka}.1", **kwargs)
        return self.copy2(**kwargs)

    def init2(self):
        r'''Calls component inits and sets self.width and self.height.
        ''' 
        if self.trace:
            print(f"{self}.init2")
        self.components.init_components()
        self.set_width_height()

    def set_width_height(self):
        self.width, self.height = self.components.size()

        #x_left = 10000000
        #x_right = -10000000
        #if hasattr(self, 'x_pos'):
        #    x_pos = self.x_pos
        #    if isinstance(x_pos, S):
        #        x_left = x_pos.i
        #    elif isinstance(x_pos, E):
        #        x_right = x_pos.i
        #y_upper = 10000000
        #y_lower = -10000000
        #if hasattr(self, 'y_pos'):
        #    y_pos = self.y_pos
        #    if isinstance(y_pos, S):
        #        y_upper = y_pos.i
        #    elif isinstance(y_pos, E):
        #        y_lower = y_pos.i
        #for i, component in enumerate(self.components, 1):
        #    if self.trace:
        #        print(f"{self}.set_width_height getting pos's from component {i} = {component}")
        #    #print(f"set_width_height: {i=}, {component=}, {component.x_pos=}, "
        #    #      f"{component.__dict__.keys()=}")
        #    xl = component.x_left.i
        #    if xl < x_left: 
        #        x_left = xl
        #    xr = component.x_right.i
        #    if xr > x_right:
        #        x_right = xr
        #    yu = component.y_upper.i
        #    if yu < y_upper:
        #        y_upper = yu
        #    yl = component.y_lower.i
        #    if yl > y_lower:
        #        y_lower = yl
        #self.width = x_right - x_left + 1
        #assert isinstance(self.width, int), \
        #       f"Composite.set_width_height got non-integer width {self.width}"
        #self.height = y_lower - y_upper + 1
        #assert isinstance(self.height, int), \
        #       f"Composite.set_width_height got non-integer height {self.height}"
        #if self.trace:
        #    print(f"{self}.set_width_height: {x_left=}, {x_right=}, {self.width=}, "
        #          f"{y_upper=}, {y_lower=}, {self.height=}")

    def draw2(self):
        if self.trace:
            print(f"{self}.draw2: {self.trace=}, {self.x_pos=}, {self.y_pos=}")
        self.components.draw(self.x_pos, self.y_pos)


class Components:
    r'''Combines multiple components.

    The x/y_align should be to_S/to_C/to_E to control alignment where all components share the same
    x/y_pos.  See comments on subclasses.

    Three subclasses: Column, Row, Stacked.

    These may not be nested.
    '''
    def __init__(self, *components, x_align=to_C, y_align=to_C, trace=False):
        self.components = components
        self.x_align = x_align
        self.y_align = y_align
        self.trace = trace

    def __iter__(self):
        return iter(self.components)

    def init_components(self):
        # first do all components with an init_order:
        if self.trace:
            print(f"{self}.init_components with", len(self.components), "components")
        first = []
        for i, component in enumerate(self.components, 1):
            if hasattr(component, 'init_order'):
                first.append((i, component))
        if self.trace:
            print(f"{self}.init_components: first", first)
        for i, component in sorted(first, key=lambda x: x[1].init_order):
            if self.trace:
                print(f"{self}.init_components calling {component}.init {i=} with init_order",
                      component.init_order)
            component.init() 

        # then the ones without an init_order:
        for i, component in enumerate(self.components, 1):
            if not hasattr(component, 'init_order'):
                if self.trace:
                    print(f"{self}.init_components calling {component}.init {i=}")
                component.init() 

class Column(Components):
    r'''Components are arranged vertically in a column.

    Only x_align is used to align the components in the column (left/center/right).
    '''
    def size(self):
        width = 0
        height = 0
        for i, component in enumerate(self.components, 1):
            width = max(width, component.width)
            height += component.height
        self.width = width
        self.height = height
        return width, height

    def draw(self, x_pos, y_pos):
        x_pos = self.x_align(x_pos, self.width)
        y_pos = y_pos.S(self.height)
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.draw doing {component}.draw {i}")
            component.draw(x_pos=x_pos, y_pos=y_pos)
            y_pos += component.height

class Row(Components):
    r'''Components are arranged horizontally in a row.

    Only y_align is used to align the components in the row (upper/mid/lower).
    '''
    def size(self):
        width = 0
        height = 0
        for i, component in enumerate(self.components, 1):
            width += component.width
            height = max(height, component.height)
        self.width = width
        self.height = height
        return width, height

    def draw(self, x_pos, y_pos):
        x_pos = x_pos.S(self.width)
        y_pos = self.y_align(y_pos, self.height)
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.draw doing {component}.draw {i}")
            component.draw(x_pos=x_pos, y_pos=y_pos)
            x_pos += component.width

class Stack(Components):
    r'''Components are stacked on top of each other, all occupying the same space.

    Both x_align and y_align are used to align the components.
    '''
    def size(self):
        width = 0
        height = 0
        for i, component in enumerate(self.components, 1):
            width = max(width, component.width)
            height = max(height, component.height)
        self.width = width
        self.height = height
        return width, height

    def draw(self, x_pos, y_pos):
        x_pos = self.x_align(x_pos, self.width)
        y_pos = self.y_align(y_pos, self.height)
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.draw doing {component}.draw {i}")
            component.draw(x_pos=x_pos, y_pos=y_pos)



if __name__ == "__main__":
    import doctest
    doctest.testmod()
