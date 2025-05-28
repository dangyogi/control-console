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


class Composite(Drawable):
    def __init__(self, *components, **kwargs):
        super().__init__(**kwargs)
        if self.trace:
            print(f"{self}.__init__: {self.trace=}, {self.x_pos=}, "
                  f"{self.y_pos=}, {kwargs=}")
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
            print(f"{self}.init2: {self.x_pos=}, {self.y_pos=}")
        self.init_components()
        self.set_width_height()

    def init_components(self):
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.init_components calling {component}.init {i=}")
            component.init() 

    def set_width_height(self):
        x_left = 10000000
        x_right = -10000000
        if hasattr(self, 'x_pos'):
            x_pos = self.x_pos
            if isinstance(x_pos, S):
                x_left = x_pos.i
            elif isinstance(x_pos, E):
                x_right = x_pos.i
        y_upper = 10000000
        y_lower = -10000000
        if hasattr(self, 'y_pos'):
            y_pos = self.y_pos
            if isinstance(y_pos, S):
                y_upper = y_pos.i
            elif isinstance(y_pos, E):
                y_lower = y_pos.i
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.set_width_height getting pos's from component {i} = {component}, "
                      f"x_left={component.x_left}, x_right={component.x_right}, "
                      f"y_upper={component.y_upper}, y_lower={component.y_lower}")
            #print(f"set_width_height: {i=}, {component=}, {component.x_pos=}, "
            #      f"{component.__dict__.keys()=}")
            xl = component.x_left.i
            if xl < x_left: 
                x_left = xl
            xr = component.x_right.i
            if xr > x_right:
                x_right = xr
            yu = component.y_upper.i
            if yu < y_upper:
                y_upper = yu
            yl = component.y_lower.i
            if yl > y_lower:
                y_lower = yl
        self.width = x_right - x_left + 1
        assert isinstance(self.width, int), \
               f"Composite.set_width_height got non-integer width {self.width}"
        self.height = y_lower - y_upper + 1
        assert isinstance(self.height, int), \
               f"Composite.set_width_height got non-integer height {self.height}"
        if self.trace:
            print(f"{self}.set_width_height: {x_left=}, {x_right=}, {self.width=}, "
                  f"{y_upper=}, {y_lower=}, {self.height=}")

    def draw2(self):
        if self.trace:
            print(f"{self}.draw2: {self.trace=}, {self.x_pos=}, {self.y_pos=}")
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print(f"{self}.draw2 doing {component}.draw {i}")
            component.draw()



if __name__ == "__main__":
    import doctest
    doctest.testmod()
