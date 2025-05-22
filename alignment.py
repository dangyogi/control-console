# alignment.py

r'''
The alignment module is not dependent on any other module here.  So it is always safe to do:

    from alignment import *

areas have x_left, x_center, x_right and y_upper, y_mid, y_lower

    >>> width = 9                  # odd numbers put the center on a pixel (not between two).
    >>> x_left = S(10)
    >>> x_left                     # x_left is always marked as S (start).
    S(10)
    >>> x_left.i                   # get the integer
    10
    >>> x_center = x_left.C(width) # Use C to convert whatever you have to a C.
    >>> x_center                   # x_center is always marked as C (center)
    C(14)
    >>> x_center.i                 # get the integer
    14
    >>> x_right = x_left.E(width)  # Use E to convert whatever you have to an E.
    >>> x_right
    E(18)
    >>> x_center.E(width)          # Or you could have converted the C to an E.
    E(18)
    >>> x_right.i                  # get the integer
    18

    Do the same things for y_upper (always an S), y_mid (always a C), and y_lower (always an E).
    This is an exercise left to the reader.

Now we have B with a different width.

    >>> width = 5

and we want to link B's x position to A (the values above).  We do that by setting B.x_pos:

    >>> x_pos = x_left             # pretending x_pos is B and x_left is A.x_left

Once x_pos is set, we can
calculate B's x_left/center/right from that as follows:

    >>> x_pos.S(width)  # x_left
    S(10)
    >>> x_pos.C(width)  # x_center
    C(12)
    >>> x_pos.E(width)  # x_right
    E(14)

How to get different alignments with A by setting B'x x_pos to different things.

    to left align B to A:

        >>> x_left            # remember, x_left will always be an "S" object
        S(10)
        >>> x_pos = x_left    # this is the same as A's x_left, i.e., left aligned!

        >>> x_pos.S(width)    # B.x_left based on B's width
        S(10)
        >>> x_pos.C(width)    # B.x_center based on B's width
        C(12)
        >>> x_pos.E(width)    # B.x_right based on B's width
        E(14)

    to center align B to A:

        >>> x_center          # remember, x_center will always be a "C" object
        C(14)
        >>> x_pos = x_center  # this is the same as A's x_center, i.e., center aligned!

        >>> x_pos.S(width)    # B.x_left based on B's width
        S(12)
        >>> x_pos.C(width)    # B.x_center based on B's width
        C(14)
        >>> x_pos.E(width)    # B.x_right based on B's width
        E(16)

    to right align B to A:

        >>> x_right           # remember, x_right will always be an "E" object
        E(18)
        >>> x_pos = x_right   # this is the same as A's x_right, i.e., right aligned!

        >>> x_pos.S(width)    # B.x_left based on B's width
        S(14)
        >>> x_pos.C(width)    # B.x_center based on B's width
        C(16)
        >>> x_pos.E(width)    # B.x_right based on B's width
        E(18)


Now B can use whichever of these makes sense to it.  And areas downstream of B can link to these values
just like above.

You do the same thing for the y axis...
'''

import math


__all__ = ('S', 'C', 'E', 'Si', 'Ci', 'Ei')


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

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __add__(self, i):
        return self.__class__(self.i + i)

    def __sub__(self, i):
        return self.__class__(self.i - i)

    def as_S(self):
        return S(self.i)

    def as_C(self):
        return C(self.i)

    def as_E(self):
        return E(self.i)

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


def Si(some_pos, length):
    r'''Returns the start (S) position of some_pos relative to length.

    >>> Si(4, 9)       # integers are returned unchanged
    4
    >>> Si(C(10), 9)   # any pos is converted to an S
    6
    >>> Si(E(10), 9)   # any pos is converted to an S
    2
    >>> Si(S(10), 9)   # any pos is converted to an S
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.S(length).i
    else:
        return some_pos

def Ci(some_pos, length):
    r'''Returns the center (C) position of some_pos relative to length.

    >>> Ci(4, 9)       # integers are returned unchanged
    4
    >>> Ci(S(10), 9)   # any pos is converted to an C
    14
    >>> Ci(E(10), 9)   # any pos is converted to an C
    6
    >>> Ci(C(10), 9)   # any pos is converted to an C
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.C(length).i
    else:
        return some_pos

def Ei(some_pos, length):
    r'''Returns the end (E) position of some_pos relative to length.

    >>> Ei(4, 9)       # integers are returned unchanged
    4
    >>> Ei(S(10), 9)   # any pos is converted to an E
    18
    >>> Ei(C(10), 9)   # any pos is converted to an E
    14
    >>> Ei(E(10), 9)   # any pos is converted to an E
    10
    '''
    if isinstance(some_pos, pos):
        return some_pos.E(length).i
    else:
        return some_pos



if __name__ == "__main__":
    import doctest
    doctest.testmod()
