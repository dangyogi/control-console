# steps.py

from math import ceil
import os.path
from pyray import *

from exp import *
from alignment import *
from context import base, instance
import screen

area = base(x_left=I.x_pos.S(I.width), x_center=I.x_pos.C(I.width), x_right=I.x_pos.E(I.width),
            y_top=I.y_pos.S(I.height), y_middle=I.y_pos.C(I.height), y_bottom=I.y_pos.E(I.height),
            x_next=F.S(I.x_right.i), y_next=F.S(I.y_bottom.i))

line_base = area(width=3, color=BLACK)

vline_base = line_base(height=I.length)

class vline(instance):
    base = vline_base
    def draw(self, template=None, **kwargs):
        with self.store(template, **kwargs) as store_self:
            draw_line_ex((self.x_center, self.y_top),
                         ({self.x_center}, {self.y_bottom}),
                         {self.width}, {self.color})


hline_base = line_base()

class hline(instance):
    base = hline_base

    def init(self, template=None):
        with self.store(template) as store_self:
            width = self.width
            store_self.width = self.length
            store_self.height = width

    def draw(self, template=None, **kwargs):
        with self.store(template, **kwargs) as store_self:
            draw_line_ex((self.x_left.i, self.y_middle.i),
                         (self.x_right.i, self.y_middle.i),
                         self.height, self.color)



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

# FIX: add spite
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
        with self.store(template) as store_self:
            store_self.font = Fonts[2 * self.sans + self.bold]
            if self.max_text is not None:
                msize = measure_text_ex(self.font, self.max_text, self.size, self.spacing)
                store_self.width = int(ceil(msize.x))
                store_self.height = int(ceil(msize.y))
                print("text.init: width", self.width, "height", self.height)

    def draw(self, template=None, **kwargs):
        with self.store(template, **kwargs) as store_self:
            self_as_dict = as_dict(self)
            text = self.text.format_map(self_as_dict)
            if self.max_text is not None:
                width = self.width
                height = self.height
            else:
                mtext = self.text.format_map(self_as_dict)
                msize = measure_text_ex(font, mtext, self.size, self.spacing)
                width = int(ceil(msize.x))
                height = int(ceil(msize.y))
            # x, y for draw is upper left
            x = self.x_pos.S(width).i
            y = self.y_pos.S(height).i
            print("text.draw to", x, y)
            draw_text_ex(self.font, text, (x, y), self.size, self.spacing, self.color)


rect_base = area(color=WHITE)

# FIX: add spite
class rect(instance):
    base = rect_base
    def draw(self, template=None, **kwargs):
        with self.store(template, **kwargs):
            x = self.x_pos.S(self.width).i
            y = self.y_pos.S(self.height).i
            draw_rectangle(x, y, self.width, self.height, self.color)


group_base = area()

# FIX: add spite
class group(instance):
    base = group_base

    def init(self, template=None):
        with self.store(template, x_pos=S(1000), y_pos=S(1000)) as store_self:
            x_left = 10000000
            x_right = -10000000
            y_top = 10000000
            y_bottom = -10000000
            for i, component in enumerate(self.components, 1):
                print("group.init doing component", i)
                component.init(template)
                xl = component.get('x_left', template).i
                if xl < x_left:
                    x_left = xl
                xr = component.get('x_right', template).i
                if xr > x_right:
                    x_right = xr
                yt = component.get('y_top', template).i
                if yt < y_top:
                    y_top = yt
                yb = component.get('y_bottom', template).i
                if yb > y_bottom:
                    y_bottom = yb
            store_self.width = x_right - x_left
            assert isinstance(self.width, int), f"group.init got non-integer width {self.width}"
            store_self.height = y_bottom - y_top
            assert isinstance(self.height, int), f"group.init got non-integer height {self.height}"
            print(f"group.init: {self.width=}, {self.height=}")

    def draw(self, template=None, **kwargs):
        with self.store(template, **kwargs) as store_self:
            store_self.x_left = S(min(component.get('x_left', template).i
                                      for component in self.components))
            store_self.x_right = E(max(component.get('x_right', template).i
                                       for component in self.components))
            store_self.width = self.x_right.i - self.x_left.i
            store_self.x_center = self.x_right.C(self.width)
            store_self.y_top = S(min(component.get('y_top', template).i 
                                     for component in self.components))
            store_self.y_bottom = E(max(component.get('y_bottom', template).i
                                        for component in self.components))
            store_self.height = self.y_bottom.i - self.y_top.i
            store_self.y_middle = self.y_top.C(self.height)
            for i, component in enumerate(self.components, 1):
                print("group.draw doing component", i)
                component.draw(template)


if __name__ == "__main__":
    import time

    with screen.Screen_class():
        message="Hello gjpqy!"
        g = group(t=text(x_pos=E(1000), y_pos=E(600), size=80, text=message, max_text=message),
                  r=rect(x_pos=S(1000), y_pos=E(600), height=80, width=300),
                  h=hline(x_pos=S(1300), y_pos=E(600), length=40))
                  #r=rect(x_pos=F.S(I.t.x_right), y_pos=I.t.y_bottom, height=80, width=300),
                  #h=hline(x_pos=F.S(I.r.x_right), y_pos=I.r.y_bottom, length=40))
        g.components = (g.t, g.h, g.r)
        g.init()
        with screen.Screen.update():
            g.draw()
        screen.Screen.draw_to_screen()
        time.sleep(5)
