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
        super().__init__(components=components, **kwargs)

    def copy(self):
        new_kwargs = self._kwargs.copy()
        components = new_kwargs['components'].copy(new_kwargs)
        new_kwargs['components'] = components
        new_obj = self.__class__(**new_kwargs)
        for component in components:
            component.parent = new_obj
        return new_obj

    def init2(self):
        r'''Calls component inits and sets self.width and self.height.
        ''' 
        if self.trace:
            print(f"{self}.init2")
        self.push_overrides()
        self.components.init_components()
        self.set_width_height()

    def push_overrides(self):
        for name, value in self._kwargs.items():
            if "__" in name:
                obj_name, root = name.split("__", 1)
                value = eval_exp(value, self, self.exp_trace)
                if self.trace:
                    print(f"push_overrides: {obj_name=}, {root=}, {value=}")
                if hasattr(self, obj_name):
                    obj = getattr(self, obj_name)
                else:
                    obj = self.components.find_by_class(obj_name)
                obj._kwargs[root] = value

    def set_width_height(self):
        self.width, self.height = self.components.size()

    def draw2(self):
        if self.trace:
            print(f"{self}.draw2: {self.trace=}, {self.x_pos=}, {self.y_pos=}")
        self.components.draw(self.x_pos, self.y_pos)


class Components:
    r'''Combines multiple components.

    The x/y_align should be to_S/to_C/to_E to control alignment where all components share the same
    x/y_pos.  See comments on subclasses.

    Three subclasses: Column, Row, Stack.

    These may not be nested.
    '''
    def __init__(self, *components, x_align=to_C, y_align=to_C, trace=False):
        self.components = components
        self.x_align = x_align
        self.y_align = y_align
        self.trace = trace

    def __iter__(self):
        return iter(self.components)

    def copy(self, new_kwargs):
        components = [x.copy() for x in self.components]
        new_obj = self.__class__(*components,
                                 x_align=self.x_align, y_align=self.y_align, trace=self.trace)
        new_obj.assign_named_components(new_kwargs)
        return new_obj

    def assign_named_components(self, new_kwargs):
        for component in self.components:
            if hasattr(component, "name"):
                if self.trace:
                    print(f"assign_named_components({new_kwargs=}): name={component.name}, {component=}")
                new_kwargs[component.name] = component

    def find_by_class(self, class_name):
        obj_found = None
        for obj in self.components:
            if class_name == obj.__class__.__name__:
                if obj_found is not None:
                    raise AssertionError(f"find_by_class({class_name=}): multiple matches")
                obj_found = obj
        if obj_found is None:
            raise AssertionError(f"find_by_class({class_name=}): not found")
        return obj_found

    def init_components(self):
        if self.trace:
            print(f"{self}.init_components with", len(self.components), "components")
        # identify first and last
        first = []  # (index, component), those with init_order < 100
        last = []   # (index, component), those with init_order >= 100
        for i, component in enumerate(self.components):
            if hasattr(component, 'init_order'):
                if component.init_order >= 100:
                    last.append((i, component))
                else:
                    first.append((i, component))

        # first do components with init_order < 100:
        if self.trace:
            print(f"{self}.init_components: first", first)
        for i, component in sorted(first, key=lambda x: x[1].init_order):
            if self.trace:
                print(f"{self}.init_components calling {component}.init {i=} with init_order",
                      component.init_order)
            component.init1() 

        # then the ones without an init_order:
        for i, component in enumerate(self.components):
            if not hasattr(component, 'init_order'):
                if self.trace:
                    print(f"{self}.init_components calling {component}.init {i=}")
                component.init1() 

        # then the ones an init_order >= 100:
        if self.trace:
            print(f"{self}.init_components: first", first)
        for i, component in sorted(last, key=lambda x: x[1].init_order):
            if self.trace:
                print(f"{self}.init_components calling {component}.init {i=} with init_order",
                      component.init_order)
            component.init1() 

class Column(Components):
    r'''Components are arranged vertically in a column.

    Only x_align is used to align the components in the column (left/center/right).
    '''
    def size(self):
        width = 0
        height = 0
        for i, component in enumerate(self.components, 1):
            try:
                width = max(width, component.width)
                height += component.height
            except AttributeError as e:
                print(f"Column.size: {e} on {component=}")
                raise
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
