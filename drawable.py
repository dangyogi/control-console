# drawable.py

r'''The Drawable base class for various shapes.

First step, building individual reusable shapes, like "line":

1. Import things we'll need

    >>> from exp import *         # I, P and F
    >>> from alignment import *   # S, C and E
    >>> from drawable import Drawable

    >>> BLACK = "BLACK"           # fake out the pyray color BLACK

2. Define a class derived from Drawable with an optional init2(self) and a draw2(self) method:

    >>> class vline(Drawable):
    ...     width = 3
    ...     color = BLACK
    ...
    ...     @property
    ...     def height(self):
    ...         return self.length
    ...
    ...     def draw2(self):
    ...         print(f"draw vert line from ({self.x_center.i}, {self.y_upper.i}) "
    ...               f"to ({self.x_center.i}, {self.y_lower.i}), "
    ...               f"width {self.width} and color {self.color}")

3. Because no P expressions were used in any of this, this can be used without a Composite:

    >>> a_line = vline(x_pos=S(10), y_pos=S(30), length=20)
    >>> a_line.init()            # safest to do this after the screen (pyray) has been initialized,
    ...                          # but we'll cheat here...
    >>> a_line.draw()
    draw vert line from (11, 30) to (11, 49), width 3 and color BLACK

4. Using the same shape in multiple locations is done by copying it.  This should always be done, even
   though you don't need to change any of its attributes in case sprites are involved.

    >>> b_line = a_line.copy(length=30, width=5)
    >>> b_line.init()
    >>> b_line.draw()
    draw vert line from (12, 30) to (12, 59), width 5 and color BLACK

5.  See the composite module for combining several shapes into one drawable.


The `shapes` module defines a set of subclasses of Drawable for general use.

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
        >>> b.y_mid
        C(100)
        >>> b.y_lower
        E(102)
        >>> b.y_next
        S(102)
    '''

    @property
    def x_left(self):
        if isinstance(self.x_pos, S):
            return self.x_pos
        return self.x_pos.S(self.width)

    @property
    def x_center(self):
        if isinstance(self.x_pos, C):
            return self.x_pos
        return self.x_pos.C(self.width)

    @property
    def x_right(self):
        if isinstance(self.x_pos, E):
            return self.x_pos
        return self.x_pos.E(self.width)

    @property
    def y_upper(self):
        if isinstance(self.y_pos, S):
            return self.y_pos
        return self.y_pos.S(self.height)

    @property
    def y_mid(self):
        if isinstance(self.y_pos, C):
            return self.y_pos
        return self.y_pos.C(self.height)

    @property
    def y_lower(self):
        if isinstance(self.y_pos, E):
            return self.y_pos
        return self.y_pos.E(self.height)

    @property
    def x_next(self):
        return self.x_right.as_S()

    @property
    def y_next(self):
        return self.y_lower.as_S()

    def contains(self, x, y):
        return self.x_left.i <= x <= self.x_right.i \
           and self.y_upper.i <= y <= self.y_lower.i


class Drawable(Box):
    r'''An instance of something drawable.

        >>> from drawable import Drawable
        >>> from alignment import *   # S, C and E

        >>> class my_inst(Drawable):
        ...     # establish defaults:
        ...     width = 9

        # box with x_center at 20, and y_lower at 200
        >>> my_a = my_inst(x_pos=C(20), y_pos=E(200), height=19)

        All instances are boxes with x_left/center/right:
        >>> my_a.x_left
        S(16)
        >>> my_a.x_center
        C(20)
        >>> my_a.x_right
        E(24)

        And y_upper/mid/lower:
        >>> my_a.y_upper
        S(182)
        >>> my_a.y_mid
        C(191)
        >>> my_a.y_lower
        E(200)

        All attributes are set using keyword arguments:
        >>> my_b = my_inst(x_pos=S(20), width=15, bogus="foobar")
        >>> my_b.width
        15
        >>> my_b.bogus
        'foobar'
        >>> my_b.x_right
        E(34)
        >>> my_b.y_lower   # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: 'my_inst' object has no attribute 'height'

    You may want to define methods that allow changing attributes, like the `draw` method does.  This
    is done with the setkwargs method.

        >>> class my_inst(Drawable):
        ...     width = 9
        ...
        ...     def my_method(self, **kwargs):             # generally same arguments to all methods!
        ...         self.setkwargs(**kwargs)               # generally always exactly the same!
        ...         print(f"{self.x_pos=}, {self.width=}")
        ...         # and @property values see these changes:
        ...         print(f"{self.x_left=}")

        >>> my_a = my_inst()
        >>> my_a.x_pos   # default set in Drawable class
        S(100)
        >>> my_a.x_left  # @property value in Drawable class
        S(100)

        # This permanently changes x_pos and width on my_a.
        >>> my_a.my_method(x_pos=C(200), width=51)
        self.x_pos=C(200), self.width=51
        self.x_left=S(175)

        # after the call...
        >>> my_a.width
        51
        >>> my_a.x_pos
        C(200)

    '''
    as_sprite = False
    dynamic_capture = False
    initialized = False
    x_pos = S(100)
    y_pos = S(100)
    trace = False
    exp_trace = False

    def __init__(self, **kwargs):
        self.setkwargs(**kwargs)
        if self.trace:
            print(f"{self}.__init__: {self.trace=}, {self.get_raw('x_pos')=}, "
                  f"{self.get_raw('y_pos')=}, {kwargs=}")

    def __repr__(self):
        if self.has_raw_attr('aka'):
            return f"<{self.__class__.__name__}: {self.aka}@{hex(id(self))}>"
        if self.has_raw_attr('name'):
            return f"<{self.__class__.__name__}: {self.name}@{hex(id(self))}>"
        return super().__repr__()

    def setkwargs(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_raw(self, name):
        r'''Gets unevaluated value.
        '''
        return super().__getattribute__(name)

    def has_raw_attr(self, name):
        try:
            super().__getattribute__(name)
            return True
        except AttributeError:
            return False

    def __getattribute__(self, name):
        raw = super().__getattribute__(name)
        trace = super().__getattribute__('exp_trace')
        return eval_exp(raw, self, trace=trace)

    def init(self):
        if not self.initialized:
            self.init2()
            if self.as_sprite:
                self.sprite = sprite.Sprite(self.width, self.height, self.dynamic_capture, self.trace)
            self.initialized = True
            if self.trace:
                width = 'unknown'
                height = 'unknown'
                try:
                    width = self.width
                except AttributeError:
                    pass
                try:
                    height = self.height
                except AttributeError:
                    pass
                print(f"{self}.init: {self.x_pos=}, {self.y_pos=}, self.{width=}, self.{height=}")

    def init2(self):
        pass

    def copy(self, **kwargs):
        r'''Make a copy of this instance.

        Please note that assigning to the copy does not affect the original inst.
        '''
        if not kwargs and not self.as_sprite:
            # copy generally not necessary (but different for composites)
            return self
        return self.copy2(**kwargs)

    def copy2(self, **kwargs):
        ans = deepcopy(self)
        ans.setkwargs(**kwargs)
        if self.trace:
            assert ans.trace
            print(f"copy2: {self=} becomes {ans=}, "
                  f"{ans.get_raw('x_pos')=}, {ans.get_raw('y_pos')=}, {kwargs=}")
        return ans

    def draw(self, retattr=None, **kwargs):
        if self.trace:
            print(f" = = = = = = = = = = = {self}.draw: {kwargs=}")
        self.setkwargs(**kwargs)
        if self.trace:
            print(f"{self}.draw: {self.x_pos=}, {self.x_left=}, {self.x_right=}, "
                  f"{self.y_pos=}, {self.y_upper=}, {self.y_lower=}")
        if self.as_sprite:
            self.sprite.save_pos(self.x_left, self.y_upper)
        if self.trace:
            print(f" = = = = = = = = = = = {self}.draw: calling {self}.draw2()")
        self.draw2()
        if retattr is not None:
            return getattr(self, retattr)

    def draw2(self):
        pass

import sprite



if __name__ == "__main__":
    import doctest
    doctest.testmod()
