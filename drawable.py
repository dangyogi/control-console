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
    >>> _ = a_line.init()            # safest to do this after the screen (pyray) has been initialized,
    ...                              # but we'll cheat here...
    >>> a_line.draw()
    draw vert line from (11, 30) to (11, 49), width 3 and color BLACK

4. Using the same shape in multiple locations is done by copying it.  This should always be done, even
   though you don't need to change any of its attributes in case sprites are involved.  The copy must
   be done before the object's init method is run.

    >>> a_line = vline(x_pos=S(10), y_pos=S(30), length=20)
    >>> b_line = a_line.copy(length=30, width=5)
    >>> _ = b_line.init()
    >>> b_line.draw()
    draw vert line from (12, 30) to (12, 59), width 5 and color BLACK

5.  See the composite module for combining several shapes into one drawable.


The `shapes` module defines a set of subclasses of Drawable for general use.

'''

from copy import copy, deepcopy
from alignment import *
from exp import Exp, eval_exp


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

    dynamic_attrs = ('x_pos', 'y_pos', 'color')

    trace = False
    exp_trace = False

    @property
    def x_pos(self):
        raw = self._x_pos
        ans = eval_exp(raw, self, self.exp_trace)
        #print(f"{self}.getter.x_pos: {raw=}, {ans=}")
        return ans

    @x_pos.setter
    def x_pos(self, value):
        #print(f"{self}.setter.x_pos got {value=}")
        self._x_pos = value

    @property
    def y_pos(self):
        return eval_exp(self._y_pos, self, self.exp_trace)

    @y_pos.setter
    def y_pos(self, value):
        self._y_pos = value

    @property
    def color(self):
        return eval_exp(self._color, self, self.exp_trace)

    @color.setter
    def color(self, value):
        self._color = value

    @property
    def x_left(self):
        x_pos = self.x_pos
        if isinstance(x_pos, S):
            return x_pos
        return x_pos.S(self.width)

    @property
    def x_center(self):
        x_pos = self.x_pos
        if isinstance(x_pos, C):
            return x_pos
        return x_pos.C(self.width)

    @property
    def x_right(self):
        x_pos = self.x_pos
        if isinstance(x_pos, E):
            return x_pos
        return x_pos.E(self.width)

    @property
    def y_upper(self):
        y_pos = self.y_pos
        if isinstance(y_pos, S):
            return y_pos
        return y_pos.S(self.height)

    @property
    def y_mid(self):
        y_pos = self.y_pos
        if isinstance(y_pos, C):
            return y_pos
        return y_pos.C(self.height)

    @property
    def y_lower(self):
        y_pos = self.y_pos
        if isinstance(y_pos, E):
            return y_pos
        return y_pos.E(self.height)

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
        >>> _ = my_a.init()

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
        >>> _ = my_b.init()
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
    is done with the set_kwargs method.

        >>> class my_inst(Drawable):
        ...     width = 9
        ...
        ...     def my_method(self, **kwargs):              # generally same arguments to all methods!
        ...         self.set_kwargs(**kwargs)               # generally always exactly the same!
        ...         print(f"{self.x_pos=}, {self.width=}")
        ...         # and @property values see these changes:
        ...         print(f"{self.x_left=}")

        >>> my_a = my_inst()
        >>> _ = my_a.init()
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

    def __init__(self, **kwargs):
        self.save_kwargs(**kwargs)
        if self.trace:
            print(f"{self}.__init__: {self.trace=}, {kwargs=}")

    def __repr__(self):
        if hasattr(self, 'aka'):
            return f"<{self.__class__.__name__}: {self.aka}@{hex(id(self))}>"
        if hasattr(self, 'name'):
            return f"<{self.__class__.__name__}: {self.name}@{hex(id(self))}>"
        return super().__repr__()

    def save_kwargs(self, **kwargs):
        self._kwargs = kwargs
        for name in ('name', 'aka', 'init_order', 'trace', 'exp_trace'):
            if name in kwargs:
                setattr(self, name, kwargs[name])

    def set_kwargs(self, **kwargs):
        args = kwargs.copy()
        while args:
            keys = []
            for key, value in args.items():
                if key in self.dynamic_attrs or not isinstance(value, Exp):
                    setattr(self, key, value)
                    keys.append(key)
                else:
                    try:
                        setattr(self, key, eval_exp(value, self, self.exp_trace))
                    except AttributeError:
                        continue
                    keys.append(key)
            if not keys:
                raise ValueError(f"{self}.set_kwargs: could not evaluate {args}")
            for key in keys:
                del args[key]

    #def get_cooked_attr(self, name):
    #    return eval_exp(getattr(self, name), self, trace=self.exp_trace)

    def init(self):
        if not self.initialized:
            self.x_pos = S(100)
            self.y_pos = S(100)
            self.set_kwargs(**self._kwargs)
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
        return self

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
        assert not self.initialized, f"{self}.copy2: init done before copy"
        ans = deepcopy(self)
        ans.save_kwargs(**(ans._kwargs | kwargs))
        if self.trace:
            assert ans.trace
            print(f"copy2: {self=} becomes {ans=}, {kwargs=}")
        return ans

    def draw(self, retattr=None, **kwargs):
        if self.trace:
            print(f" = = = = = = = = = = = {self}.draw: {kwargs=}")
        self.set_kwargs(**kwargs)
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
