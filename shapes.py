# shapes.py

from math import ceil
import os.path
from pyray import *

from exp import *
from alignment import *
from context import base, instance, template_base, context
import screen
from sprite import Sprite

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
        return attrs


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
        return attrs



Font_dir = "/usr/share/fonts/truetype/dejavu"

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
            msize = measure_text_ex(attrs.font, mtext, attrs.size, attrs.spacing)
            width = int(ceil(msize.x))
            height = int(ceil(msize.y))
        # x, y for draw is upper left
        x = attrs.x_pos.S(width).i
        y = attrs.y_pos.S(height).i
        print("text.draw to", x, y)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        draw_text_ex(attrs.font, text, (x, y), attrs.size, attrs.spacing, attrs.color)
        return attrs


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
        return attrs


# possibly interesting "on" colors for "LED"s: RED, GREEN, BLUE
# possibly interesting "off" colors for "LED"s: GRAY, DARKGRAY, BROWN, BLACK
# see test_3
circle_base = area(diameter=20, color=WHITE)

class circle(instance):
    base = circle_base
    def init(self, template=None):
        attrs = context(self, template)
        self.width = self.height = attrs.diameter
        if attrs.diameter & 1:  # odd
            self.radius = (self.diameter - 1) // 2
        else:
            self.radius = (self.diameter - 1) / 2
        if attrs.as_sprite:
            self.sprite = Sprite(self.width, self.height, attrs.dynamic_capture)

    def draw(self, template=None, **kwargs):
        attrs = context(self, template, **kwargs)
        x = attrs.x_pos.C(attrs.width)
        y = attrs.y_pos.C(attrs.height)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        draw_circle(x.i, y.i, attrs.radius, attrs.color)
        return attrs



if __name__ == "__main__":
    import time
    import argparse
    import touch_input  # does register_init on Screen

    tbase = template_base(area)

    def template():
        with screen.Screen_class():
            message="Hello gjpqy!"
            t = tbase(t=text(x_pos=E(1000), y_pos=E(600), size=80, text=message, max_text=message),
                      r=rect(x_pos=T.t.x_next, y_pos=E(600), height=80, width=300),
                      c=circle(x_pos=T.r.x_next, y_pos=E(600), diameter=80),
                      h=hline(x_pos=T.c.x_next, y_pos=E(600), length=40))
                      #r=rect(x_pos=F.S(I.t.x_right), y_pos=I.t.y_bottom, height=80, width=300),
                      #h=hline(x_pos=F.S(I.r.x_right), y_pos=I.r.y_bottom, length=40))
            t.components = (t.t, t.r, t.c, t.h)
            t.init()
            with screen.Screen.update():
                t.draw()
            screen.Screen.Touch_generator.run(5)

    def rect_as_sprite():
        with screen.Screen_class():
            message="Hello gjpqy!"
            r = rect(y_pos=E(600), height=80, width=300, as_sprite=True)
            r.init()
            for x in range(100, 801, 100):
                print("drawing x", x)
                with screen.Screen.update():
                    r.draw(x_pos=S(x))
                screen.Screen.Touch_generator.run(1)

    def circle_colors():
        with screen.Screen_class():
            t1 = text(y_pos=E(350))
            cir1 = circle(y_pos=C(400))
            t2 = text(y_pos=E(550))
            cir2 = circle(y_pos=C(600))
            r = rect(width=1200, height=350)
            cir1.init()
            t1.init()
            cir2.init()
            t2.init()
            r.init()
            with screen.Screen.update():
                r.draw(x_pos=S(50), y_pos=S(300))

                # LED on:
                c = cir1.draw(x_pos=C(100), color=WHITE)
                t1.draw(x_pos=c.x_center, text="WHITE")
                c = cir1.draw(x_pos=C(200), color=YELLOW)
                t1.draw(x_pos=c.x_center, text="YELLOW")
                c = cir1.draw(x_pos=C(300), color=ORANGE)
                t1.draw(x_pos=c.x_center, text="ORANGE")
                c = cir1.draw(x_pos=C(400), color=PINK)
                t1.draw(x_pos=c.x_center, text="PINK")
                c = cir1.draw(x_pos=C(500), color=RED)
                t1.draw(x_pos=c.x_center, text="RED")
                c = cir1.draw(x_pos=C(600), color=GREEN)
                t1.draw(x_pos=c.x_center, text="GREEN")
                c = cir1.draw(x_pos=C(700), color=LIME)
                t1.draw(x_pos=c.x_center, text="LIME")
                c = cir1.draw(x_pos=C(800), color=SKYBLUE)
                t1.draw(x_pos=c.x_center, text="SKYBLUE")
                c = cir1.draw(x_pos=C(900), color=BLUE)
                t1.draw(x_pos=c.x_center, text="BLUE")
                c = cir1.draw(x_pos=C(1000), color=PURPLE)
                t1.draw(x_pos=c.x_center, text="PURPLE")
                c = cir1.draw(x_pos=C(1100), color=VIOLET)
                t1.draw(x_pos=c.x_center, text="VIOLET")
                c = cir1.draw(x_pos=C(1200), color=MAGENTA)
                t1.draw(x_pos=c.x_center, text="MAGENTA")

                # LED off:
                c = cir2.draw(x_pos=C(100), color=LIGHTGRAY)
                t2.draw(x_pos=c.x_center, text="LIGHTGRAY")
                c = cir2.draw(x_pos=C(200), color=GRAY)
                t2.draw(x_pos=c.x_center, text="GRAY")
                c = cir2.draw(x_pos=C(300), color=DARKGRAY)
                t2.draw(x_pos=c.x_center, text="DARKGRAY")
                c = cir2.draw(x_pos=C(400), color=BEIGE)
                t2.draw(x_pos=c.x_center, text="BEIGE")
                c = cir2.draw(x_pos=C(500), color=BROWN)
                t2.draw(x_pos=c.x_center, text="BROWN")
                c = cir2.draw(x_pos=C(600), color=DARKBROWN)
                t2.draw(x_pos=c.x_center, text="DARKBROWN")
                c = cir2.draw(x_pos=C(700), color=BLACK)
                t2.draw(x_pos=c.x_center, text="BLACK")
            screen.Screen.Touch_generator.run(10)

    parser = argparse.ArgumentParser()
    parser.add_argument("test", choices=("template", "rect_as_sprite", "circle_colors"))

    args = parser.parse_args()

    match args.test:
        case "template": template()
        case "rect_as_sprite": rect_as_sprite()
        case "circle_colors": circle_colors()

