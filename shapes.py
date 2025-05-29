# shapes.py

r'''A set of classes for different kinds of shapes supported by raylib.
'''

from math import ceil
import os.path
from pyray import *

from alignment import *
from exp import eval_exp
from drawable import Drawable
import screen


# raylib colors:
#
#define LIGHTGRAY  (Color){ 200, 200, 200, 255 }   // Light Gray
#define GRAY       (Color){ 130, 130, 130, 255 }   // Gray
#define DARKGRAY   (Color){ 80, 80, 80, 255 }      // Dark Gray
#define YELLOW     (Color){ 253, 249, 0, 255 }     // Yellow
#define GOLD       (Color){ 255, 203, 0, 255 }     // Gold
#define ORANGE     (Color){ 255, 161, 0, 255 }     // Orange
#define PINK       (Color){ 255, 109, 194, 255 }   // Pink
#define RED        (Color){ 230, 41, 55, 255 }     // Red
#define MAROON     (Color){ 190, 33, 55, 255 }     // Maroon
#define GREEN      (Color){ 0, 228, 48, 255 }      // Green
#define LIME       (Color){ 0, 158, 47, 255 }      // Lime
#define DARKGREEN  (Color){ 0, 117, 44, 255 }      // Dark Green
#define SKYBLUE    (Color){ 102, 191, 255, 255 }   // Sky Blue
#define BLUE       (Color){ 0, 121, 241, 255 }     // Blue
#define DARKBLUE   (Color){ 0, 82, 172, 255 }      // Dark Blue
#define PURPLE     (Color){ 200, 122, 255, 255 }   // Purple
#define VIOLET     (Color){ 135, 60, 190, 255 }    // Violet
#define DARKPURPLE (Color){ 112, 31, 126, 255 }    // Dark Purple
#define BEIGE      (Color){ 211, 176, 131, 255 }   // Beige
#define BROWN      (Color){ 127, 106, 79, 255 }    // Brown
#define DARKBROWN  (Color){ 76, 63, 47, 255 }      // Dark Brown
#
#define WHITE      (Color){ 255, 255, 255, 255 }   // White
#define BLACK      (Color){ 0, 0, 0, 255 }         // Black
#define BLANK      (Color){ 0, 0, 0, 0 }           // Blank (Transparent)
#define MAGENTA    (Color){ 255, 0, 255, 255 }     // Magenta
#define RAYWHITE   (Color){ 245, 245, 245, 255 }   // My own White (raylib logo)


__all__ = ("vline", "hline", "text", "rect", "circle", "hgap", "vgap")


class line(Drawable):
    width = 3
    color = BLACK

class vline(line):
    r'''The line drawing is flakey in raylib.  Consider using rect instead!

    See experiment/raylib_test.py
    '''
    @property
    def height(self):
        return self.length

    def draw2(self):
        draw_line_ex((self.x_center, self.y_upper),
                     (self.x_center, self.y_lower),
                     self.width, self.color)


class hline(line):
    r'''The line drawing is flakey in raylib.  Consider using rect instead!

    See experiment/raylib_test.py
    '''
    def init2(self):
        width = self.width
        self.width = self.length
        self.height = width
        if self.trace:
            print(f"hline.init2: {self.y_pos=}, {kwargs=}")

    def draw2(self):
        if self.trace:
            print(f"hline.draw2: {self.y_pos=}, {self.height=}, {self.y_mid=}")
        draw_line_ex((self.x_left.i, self.y_mid.i),
                     (self.x_right.i, self.y_mid.i),
                     self.height, self.color)



Fonts = []   # Serif, Serif-Bold, Sans, Sans-Bold
Font_names = []

@screen.register_init
def init_fonts(screen_obj):
    # This must run _after_ init_window is called!

    global Fonts, Font_names
    # Load Fonts:
    for name in 'Serif', 'Sans':
        for bold in False, True:
            font_name = "DejaVu" + name
            if bold:
                font_name += '-Bold'
            path = os.path.join(screen.Font_dir, font_name + ".ttf")
            Font_names.append(font_name)
            font = load_font(path)
            #print(f"{font=}, {is_font_valid(font)=}")
            Fonts.append(font)

class as_dict(dict):
    def __init__(self, attrs):
        self.attrs = attrs

    def __getitem__(self, key):
        try:
            return getattr(self.attrs, key)
        except AttributeError:
            raise KeyError(key)

class text(Drawable):
    r'''Draw text.

    The text (but not the max_text), has .format_map called on it with the current instance passed as a
    dict.  If there are no formatting directives ({...}) in the text, no harm done.  This provides a
    way to pass parameters into the text message.

    If you are using the text in a group, you must specify max_text so that it can calculate a width.

    The calculated height of the text comes out the same as the size.  This includes room for
    descenders on the chars, even if there're not any.  To make the text appear more lined up with
    other things on the same line, add about 6% of the height to the Y pos, no matter what the Y
    alignment.

    The text and max_text attributes are automatically converted to strings with str().
    '''
    dynamic_attrs = Drawable.dynamic_attrs + ('text',)

    max_text = None
    size = 20
    sans = False
    bold = False
    spacing = 0
    color = BLACK

    @property
    def text(self):
        return eval_exp(self._text, self, self.exp_trace)

    @text.setter
    def text(self, value):
        self._text = value

    # FIX: move to __init__ with screen.Screen.register_init
    def init2(self):
        font = Fonts[2 * self.sans + self.bold]
        if self.max_text is not None:
            msize = measure_text_ex(font, str(self.max_text), self.size, self.spacing)
            self.width = int(ceil(msize.x))
            self.height = int(ceil(msize.y))
            if self.trace:
                print("text.init: width", self.width, "height", self.height)
        elif self.as_sprite:
            raise AssertionError("text.init2: must specify max_text with as_sprite")
        elif hasattr(self, 'text'):
            msize = measure_text_ex(font, str(self.text), self.size, self.spacing)
            self.width = int(ceil(msize.x))
            self.height = int(ceil(msize.y))
            if self.trace:
                print("text.init: width", self.width, "height", self.height)

    def draw2(self):
        font = Fonts[2 * self.sans + self.bold]
        attrs_as_dict = as_dict(self)
        text = str(self.text).format_map(attrs_as_dict)
        #if self.max_text is not None:
        #    width = self.width
        #    height = self.height
        #    if self.trace:
        #        print(f"text.draw2: got max_text, {self.width=}, {self.height=}")
        #else:
        #    # FIX: not needed if x_pos and y_pos are S types.
        #    msize = measure_text_ex(font, text, self.size, self.spacing)
        #    width = int(ceil(msize.x))
        #    height = int(ceil(msize.y))
        #    if self.trace:
        #        print(f"text.draw2: no max_text, {text=}, {self.width=}, {self.height=}")

        # x, y for draw is upper left
        if isinstance(self.x_pos, S):
            x = self.x_pos.i
            height = self.size
        else:
            msize = measure_text_ex(font, text, self.size, self.spacing)
            width = int(ceil(msize.x))
            height = int(ceil(msize.y))
            if self.trace:
                print(f"text.draw2: measuring text {text=} got {self.width=}, {self.height=}")
            x = self.x_pos.S(width).i
        y = self.y_pos.S(height).i
        if self.trace:
            print(f"text.draw2 to {x=}, {y=}")
        draw_text_ex(font, text, (x, y), self.size, self.spacing, self.color)


class rect(Drawable):
    color = WHITE

    def draw2(self):
        x = self.x_left
        y = self.y_upper
        if self.trace:
            print(f"{self=}.draw2, {x=}, {y=}, {self.width=}, {self.height=}, {self.color=}")
        draw_rectangle(x.i, y.i, self.width, self.height, self.color)


# possibly interesting "on" colors for "LED"s: RED, GREEN, BLUE
# possibly interesting "off" colors for "LED"s: GRAY, DARKGRAY, BROWN, BLACK
# see test_3
class circle(Drawable):
    diameter = 21
    color = WHITE

    @property
    def radius(self):
        if self.diameter & 1:  # odd
            return (self.diameter - 1) // 2
        return (self.diameter - 1) / 2
    
    @property
    def width(self):
        return self.diameter
    
    @property
    def height(self):
        return self.diameter

    def draw2(self):
        x = self.x_pos.C(self.width)
        y = self.y_pos.C(self.height)
        if self.trace:
            print(f"circle.draw2: {x=}, {y=}, {self.radius=}, {self.color=}")
        draw_circle(x.i, y.i, self.radius, self.color)


class gap(Drawable):
    # 0 could cause confusion because (0 - 1) // 2 == -1
    height = 3
    width = 3

    def draw2(self):
        pass

class vgap(gap):
    def __init__(self, height):
        super().__init__(height=height)

class hgap(gap):
    def __init__(self, width):
        super().__init__(width=width)




if __name__ == "__main__":
    import doctest
    doctest.testmod()
