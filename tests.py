# tests.py

from pyray import *

from exp import *
from alignment import *
from context import Template, area
import screen
from shapes import *


def template():
    with screen.Screen_class():
        message="Hello gjpqy!"
        t = Template(t=text(x_pos=E(1000), y_pos=E(600), size=80, text=message, max_text=message),
                     r=rect(x_pos=T.t.x_next, y_pos=E(600), height=80, width=300),
                     c=circle(x_pos=T.r.x_next, y_pos=E(600), diameter=80),
                     h=hline(x_pos=T.c.x_next, y_pos=E(600), length=40))
                     #r=rect(x_pos=F.S(I.t.x_right), y_pos=I.t.y_lower, height=80, width=300),
                     #h=hline(x_pos=F.S(I.r.x_right), y_pos=I.r.y_lower, length=40))
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



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("test", choices=("template", "rect_as_sprite", "circle_colors"))

    args = parser.parse_args()

    match args.test:
        case "template": template()
        case "rect_as_sprite": rect_as_sprite()
        case "circle_colors": circle_colors()

