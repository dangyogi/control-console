# alignment.py

r'''
areas have x_left, x_center, x_right and y_top, y_center, y_bottom

    >>> from context import base, instance
    >>> from exp import *

    >>> A = base(width=9)

    >>> A.x_left = S(10)
    >>> A.x_left                  # x_left is always marked as S (start).
    S(10)
    >>> A.x_left.i                # get the integer
    10
    >>> A.x_center = A.x_left.C(A.width) # Use C to convert the S to a C.
    >>> A.x_center                # x_center is always marked as C (center)
    C(14)
    >>> A.x_center.i              # get the integer
    14
    >>> A.x_right = A.x_left.E(A.width)  # Use E to convert the S to an E.
    >>> A.x_right
    E(18)
    >>> A.x_center.E(A.width)              # Or you could have converted the C to an E.
    E(18)
    >>> A.x_right.i               # get the integer
    18

    Do the same things for y_top (always an S), y_middle (always a C), and y_bottom (always an E).
    This is an exercise left to the reader.

Now we have B with a different width.

    >>> B = base(width=5)

and we want to link B's x position to A.  We do that by setting B.x_pos.  Once x_pos is set, we can
calculate B's x_left/center/right from that as follows:

    >>> B.x_left   = I.x_pos.S(I.width)
    >>> B.x_center = I.x_pos.C(I.width)
    >>> B.x_right  = I.x_pos.E(I.width)

We need to set up instances of B to evaluate these:

    >>> class B_inst(instance):
    ...     base = B

How get different alignments with A by setting B'x x_pos to different things.

    to left align B to A:

        >>> B1 = B_inst(x_pos=A.x_left)      # remember, x_left will always be an "S" object
        >>> B1.x_pos                         # this is the same as A's x_left, i.e., left aligned!
        S(10)
        >>> A.x_left
        S(10)

        >>> B1.get('x_left'), B1.get('x_center'), B1.get('x_right')
        (S(10), C(12), E(14))

    to center align B to A:

        >>> B2 = B_inst(x_pos = A.x_center)  # remember, x_center will always be a "C" object
        >>> B2.x_pos                         # this is the same as A's x_center, i.e., center aligned!
        C(14)

        >>> B2.get('x_left'), B2.get('x_center'), B2.get('x_right')
        (S(12), C(14), E(16))

    to right align B to A:

        >>> B3 = B_inst(x_pos = A.x_right)   # remember, x_right will always be an "E" object
        >>> B3.x_pos                         # this is the same as A's x_right, i.e., center aligned!
        E(18)

        >>> B3.get('x_left'), B3.get('x_center'), B3.get('x_right')
        (S(14), C(16), E(18))

Now B can use whichever of these makes sense to it.  And areas downstream of B can link to these values
just like above.

Do the same thing for the y axis...
'''

import math


__all__ = ('S', 'C', 'E', 'as_S', 'as_C', 'as_E')


#              horz    vert
#             ------  ------
START = 1   #  LEFT    TOP
CENTER = 2  # CENTER  MIDDLE
END = 3     #  RIGHT  BOTTOM


def half_length(length):
    r'''Returns half the length, rounding up.

    With a row of, say 3,  pixels, ***, the length is 2 -- adding an offset of 2
    to the position of the first one gets you the position of the last one. 

    So half_length wants (length - 1) / 2.

    But what if length - 1 is odd?  In this case, we want to round up, so (length - 1 + 1) // 2.

    So if length is even, length - 1 is odd and we want length // 2.

    And if length is odd, length - 1 is even and we want (length - 1) // 2.  But is length is odd, this
    is the same as length // 2!

        >>> half_length(3)
        1
        >>> half_length(4)
        2
    '''
    assert not isinstance(length, float), f"half_length got float {length=}"
    #length -= 1
    #if length & 1:  # odd
    #    length += 1
    return length // 2


class pos:
    r'''You can add/sub an integer to/from any pos.  The type of the pos remains the same.

    >>> C(10) + 4
    C(14)
    >>> S(10) - 4
    S(6)
    '''
    def __init__(self, i):
        self.i = i

    def __repr__(self):
        return f"{self.__class__.__name__}({self.i})"

    def __add__(self, i):
        return self.__class__(self.i + i)

    def __sub__(self, i):
        return self.__class__(self.i - i)

class S(pos):
    r'''START pos.

        >>> s = S(10)
        >>> s.S(3)
        S(10)
        >>> s.C(3)
        C(11)
        >>> s.E(3)
        E(12)
        >>> s + 4
        S(14)
        >>> s - 4
        S(6)
    '''
    def S(self, length):
        return self

    def C(self, length):
        ans = self.i + half_length(length)
        if not isinstance(ans, int):
            raise AssertionError(f"S({self.i}).C({length}) is not an integer, got {ans}")
        return C(ans)

    def E(self, length):
        ans = self.i + (length - 1)
        if not isinstance(ans, int):
            raise AssertionError(f"S({self.i}).E({length}) is not an integer, got {ans}")
        return E(ans)

class C(pos):
    r'''CENTER pos.

        >>> c = C(10)
        >>> c.S(3)
        S(9)
        >>> c.C(3)
        C(10)
        >>> c.E(3)
        E(11)
    '''
    def S(self, length):
        ans = self.i - half_length(length)
        if not isinstance(ans, int):
            raise AssertionError(f"C({self.i}).S({length}) is not an integer, got {ans}")
        return S(ans)

    def C(self, length):
        return self

    def E(self, length):
        ans = self.i + half_length(length)
        if not isinstance(ans, int):
            raise AssertionError(f"C({self.i}).E({length}) is not an integer, got {ans}")
        return E(ans)

class E(pos):
    r'''END pos.

        >>> e = E(10)
        >>> e.S(3)
        S(8)
        >>> e.C(3)
        C(9)
        >>> e.E(3)
        E(10)
    '''
    def S(self, length):
        ans = self.i - (length - 1)
        if not isinstance(ans, int):
            raise AssertionError(f"E({self.i}).S({length}) is not an integer, got {ans}")
        return S(ans)

    def C(self, length):
        ans = self.i - half_length(length)
        if not isinstance(ans, int):
            raise AssertionError(f"E({self.i}).C({length}) is not an integer, got {ans}")
        return C(ans)

    def E(self, length):
        return self


def as_S(some_pos, length):
    r'''Returns the start (S) position of some_pos relative to length.

    >>> as_S(4, 9)       # integers are returned unchanged
    4
    >>> as_S(C(10), 9)   # any pos is converted to an S
    6
    >>> as_S(E(10), 9)   # any pos is converted to an S
    2
    >>> as_S(S(10), 9)   # any pos is converted to an S
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.S(length).i
    else:
        return some_pos

def as_C(some_pos, length):
    r'''Returns the center (C) position of some_pos relative to length.

    >>> as_C(4, 9)       # integers are returned unchanged
    4
    >>> as_C(S(10), 9)   # any pos is converted to an C
    14
    >>> as_C(E(10), 9)   # any pos is converted to an C
    6
    >>> as_C(C(10), 9)   # any pos is converted to an C
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.C(length).i
    else:
        return some_pos

def as_E(some_pos, length):
    r'''Returns the end (E) position of some_pos relative to length.

    >>> as_E(4, 9)       # integers are returned unchanged
    4
    >>> as_E(S(10), 9)   # any pos is converted to an E
    18
    >>> as_E(C(10), 9)   # any pos is converted to an E
    14
    >>> as_E(E(10), 9)   # any pos is converted to an E
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.E(length).i
    else:
        return some_pos


# FIX: Do we still need this?
class offset:
    r'''Translates parent pos to child pos.

        >>> o = offset(S, C, 20) # position child C at parent.S + 20
        >>> o.apply(S(10), 5)
        C(30)
        >>> o.apply(C(10), 5)
        C(28)
        >>> o.apply(E(10), 5)
        C(26)
    '''
    def __init__(self, from_alignment, to_alignment, offset=0):
        self.from_alignment = \
          from_alignment.__name__ if isinstance(from_alignment, type) else from_alignment
        self.to_alignment = to_alignment
        self.offset = offset

    def apply(self, pos, width):
        pos_inc = pos + self.offset
        pos_from = getattr(pos_inc, self.from_alignment)(width)
        return self.to_alignment(pos_from.i)



if __name__ == "__main__":
    import doctest
    doctest.testmod()
