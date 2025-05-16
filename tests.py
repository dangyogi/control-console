# tests.py

from pyray import *

from exp import *
from alignment import *
from templates import Group
import screen
from shapes import *


def group():
    #with screen.Screen_class():
        message="Hello gjpqy!"
        g = Group(text(name='txt', x_pos=T.x_pos, y_pos=T.y_pos, size=80, text=message,
                       max_text=message),
                  rect(name='r', x_pos=T.txt.x_next, y_pos=T.y_pos, height=80, width=300),
                  circle(name='c', x_pos=T.r.x_next, y_pos=T.y_pos, diameter=80),
                  hline(x_pos=T.c.x_next, y_pos=T.y_pos, length=40))
        g.init()
        with screen.Screen.update():
            g.draw(x_pos=S(500), y_pos=E(600))
        screen.Screen.Touch_generator.run(2)

def rect_as_sprite():
    #with screen.Screen_class():
        message="Hello gjpqy!"
        r = rect(y_pos=E(600), height=80, width=300, as_sprite=True)
        r.init()
        for x in range(100, 801, 100):
            print("drawing x", x)
            with screen.Screen.update():
                r.draw(x_pos=S(x))
            screen.Screen.Touch_generator.run(0.5)

def circle_colors():
    #with screen.Screen_class():
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
            c_x_center = cir1.draw('x_center', x_pos=C(100), color=WHITE)
            t1.draw(x_pos=c_x_center, text="WHITE")
            c_x_center = cir1.draw('x_center', x_pos=C(200), color=YELLOW)
            t1.draw(x_pos=c_x_center, text="YELLOW")
            c_x_center = cir1.draw('x_center', x_pos=C(300), color=ORANGE)
            t1.draw(x_pos=c_x_center, text="ORANGE")
            c_x_center = cir1.draw('x_center', x_pos=C(400), color=PINK)
            t1.draw(x_pos=c_x_center, text="PINK")
            c_x_center = cir1.draw('x_center', x_pos=C(500), color=RED)
            t1.draw(x_pos=c_x_center, text="RED")
            c_x_center = cir1.draw('x_center', x_pos=C(600), color=GREEN)
            t1.draw(x_pos=c_x_center, text="GREEN")
            c_x_center = cir1.draw('x_center', x_pos=C(700), color=LIME)
            t1.draw(x_pos=c_x_center, text="LIME")
            c_x_center = cir1.draw('x_center', x_pos=C(800), color=SKYBLUE)
            t1.draw(x_pos=c_x_center, text="SKYBLUE")
            c_x_center = cir1.draw('x_center', x_pos=C(900), color=BLUE)
            t1.draw(x_pos=c_x_center, text="BLUE")
            c_x_center = cir1.draw('x_center', x_pos=C(1000), color=PURPLE)
            t1.draw(x_pos=c_x_center, text="PURPLE")
            c_x_center = cir1.draw('x_center', x_pos=C(1100), color=VIOLET)
            t1.draw(x_pos=c_x_center, text="VIOLET")
            c_x_center = cir1.draw('x_center', x_pos=C(1200), color=MAGENTA)
            t1.draw(x_pos=c_x_center, text="MAGENTA")

            # LED off:
            c_x_center = cir2.draw('x_center', x_pos=C(100), color=LIGHTGRAY)
            t2.draw(x_pos=c_x_center, text="LIGHTGRAY")
            c_x_center = cir2.draw('x_center', x_pos=C(200), color=GRAY)
            t2.draw(x_pos=c_x_center, text="GRAY")
            c_x_center = cir2.draw('x_center', x_pos=C(300), color=DARKGRAY)
            t2.draw(x_pos=c_x_center, text="DARKGRAY")
            c_x_center = cir2.draw('x_center', x_pos=C(400), color=BEIGE)
            t2.draw(x_pos=c_x_center, text="BEIGE")
            c_x_center = cir2.draw('x_center', x_pos=C(500), color=BROWN)
            t2.draw(x_pos=c_x_center, text="BROWN")
            c_x_center = cir2.draw('x_center', x_pos=C(600), color=DARKBROWN)
            t2.draw(x_pos=c_x_center, text="DARKBROWN")
            c_x_center = cir2.draw('x_center', x_pos=C(700), color=BLACK)
            t2.draw(x_pos=c_x_center, text="BLACK")
        screen.Screen.Touch_generator.run(2)



if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("test", nargs='?', choices=("group", "rect_as_sprite", "circle_colors"))

    args = parser.parse_args()

    with screen.Screen_class():
        match args.test:
            case "group": group()
            case "rect_as_sprite": rect_as_sprite()
            case "circle_colors": circle_colors()
            case None:
                group()
                time.sleep(2)
                screen.Screen.clear()
                rect_as_sprite()
                time.sleep(2)
                screen.Screen.clear()
                circle_colors()

