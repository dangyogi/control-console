# steps.py

from math import ceil
import os.path
from pyray import *

from exp import *
from alignment import *
from context import base, instance, template_base, context
import screen
from sprite import Sprite

area = base(x_left=I.x_pos.S(I.width), x_center=I.x_pos.C(I.width), x_right=I.x_pos.E(I.width),
            y_top=I.y_pos.S(I.height), y_middle=I.y_pos.C(I.height), y_bottom=I.y_pos.E(I.height),
            x_next=I.x_right.as_S(), y_next=I.y_bottom.as_S(), as_sprite=False, dynamic_capture=False)

line_base = area(width=3, color=BLACK)

vline_base = line_base(height=I.length)

class vline(instance):
    base = vline_base
    def draw(self, template=None, **kwargs):
        attrs = context(self, template, **kwargs)
        draw_line_ex((attrs.x_center, attrs.y_top),
                     ({attrs.x_center}, {attrs.y_bottom}),
                     {attrs.width}, {attrs.color})


hline_base = line_base()

class hline(instance):
    base = hline_base

    def init(self, template=None):
        attrs = context(self, template)
        width = attrs.width
        self.width = attrs.length
        self.height = width

    def draw(self, template=None, **kwargs):
        attrs = context(self, template, **kwargs)
        draw_line_ex((attrs.x_left.i, attrs.y_middle.i),
                     (attrs.x_right.i, attrs.y_middle.i),
                     attrs.height, attrs.color)



Font_dir = "/usr/share/fonts/truetype/dejavu"

Fonts = []   # Serif, Serif-Bold, Sans, Sans-Bold
Font_names = []

@screen.register_init
def init_fonts(screen):
    # This must run _after_ init_window is called!

    global Fonts, Font_names
    # Load Fonts:
    for name in 'Serif', 'Sans':
        for bold in False, True:
            font_name = "DejaVu" + name
            if bold:
                font_name += '-Bold'
            path = os.path.join(Font_dir, font_name + ".ttf")
            Font_names.append(font_name)
            font = load_font(path)
            #print(f"{font=}, {is_font_valid(font)=}")
            Fonts.append(font)

text_base = area(max_text=None, size=20, sans=False, bold=False, color=BLACK, spacing=0)

class as_dict(dict):
    def __init__(self, attrs):
        self.attrs = attrs

    def __getitem__(self, key):
        try:
            return getattr(self.attrs, key)
        except AttributeError:
            raise KeyError(key)

class text(instance):
    r'''Draw text.

    The text (but not the max_text), has .format_map called on it with the current instance passed as a
    dict.  If there are no formatting directives ({...}) in the text, no harm done.  This provides a
    way to pass parameters into the text message.

    If you are using the text in a group, you must specify max_text so that it can calculate a width.

    The calculated height of the text comes out the same as the size.  This includes room for
    descenders on the chars, even if there're not any.  To make the text appear more lined up with
    other things on the same line, add about 6% of the height to the Y pos, no matter what the Y
    alignment.
    '''
    base = text_base

    def init(self, template=None):
        attrs = context(self, template)
        self.font = Fonts[2 * self.sans + self.bold]
        if attrs.max_text is not None:
            msize = measure_text_ex(attrs.font, attrs.max_text, attrs.size, attrs.spacing)
            self.width = int(ceil(msize.x))
            self.height = int(ceil(msize.y))
            print("text.init: width", self.width, "height", self.height)
            if attrs.as_sprite:
                self.sprite = Sprite(self.width, self.height, attrs.dynamic_capture)
        elif attrs.as_sprite:
            raise AssertionError("text.init: must specify max_text with as_sprite")

    def draw(self, template=None, **kwargs):
        attrs = context(self, template, **kwargs)
        attrs_as_dict = as_dict(attrs)
        text = attrs.text.format_map(attrs_as_dict)
        if attrs.max_text is not None:
            width = attrs.width
            height = attrs.height
        else:
            mtext = attrs.text.format_map(attrs_as_dict)
            msize = measure_text_ex(font, mtext, attrs.size, attrs.spacing)
            width = int(ceil(msize.x))
            height = int(ceil(msize.y))
        # x, y for draw is upper left
        x = attrs.x_pos.S(width).i
        y = attrs.y_pos.S(height).i
        print("text.draw to", x, y)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        draw_text_ex(attrs.font, text, (x, y), attrs.size, attrs.spacing, attrs.color)


rect_base = area(color=WHITE)

class rect(instance):
    base = rect_base
    def init(self, template=None):
        attrs = context(self, template)
        if attrs.as_sprite:
            self.sprite = Sprite(self.width, self.height, attrs.dynamic_capture)

    def draw(self, template=None, **kwargs):
        attrs = context(self, template, **kwargs)
        x = attrs.x_pos.S(attrs.width)
        y = attrs.y_pos.S(attrs.height)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        draw_rectangle(x.i, y.i, attrs.width, attrs.height, attrs.color)


tbase = template_base(area)

def test_1():
    with screen.Screen_class():
        message="Hello gjpqy!"
        t = tbase(t=text(x_pos=E(1000), y_pos=E(600), size=80, text=message, max_text=message),
                  r=rect(x_pos=T.t.x_next, y_pos=E(600), height=80, width=300),
                  h=hline(x_pos=T.r.x_next, y_pos=E(600), length=40))
                  #r=rect(x_pos=F.S(I.t.x_right), y_pos=I.t.y_bottom, height=80, width=300),
                  #h=hline(x_pos=F.S(I.r.x_right), y_pos=I.r.y_bottom, length=40))
        t.components = (t.t, t.h, t.r)
        t.init()
        with screen.Screen.update():
            t.draw()
        screen.Screen.draw_to_screen()
        time.sleep(5)


def test_2():
    with screen.Screen_class():
        message="Hello gjpqy!"
        r = rect(y_pos=E(600), height=80, width=300, as_sprite=True)
        r.init()
        for x in range(100, 801, 100):
            print("drawing x", x)
            with screen.Screen.update():
                r.draw(x_pos=S(x))
            screen.Screen.draw_to_screen()
            time.sleep(1)


if __name__ == "__main__":
    import time

    #test_1()
    test_2()
