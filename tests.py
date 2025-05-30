# tests.py

from pyray import *

from exp import *
from alignment import *
from composite import Composite
from composites import *
import screen
from shapes import *
import traffic_cop


def group():
    message="Hello gjpqy!"
    g = Composite(Row(text(name='txt', size=80, text=message, max_text=message),
                      rect(name='r', height=80, width=300),
                      circle(name='c', diameter=80),
                      hline(length=40),
                      y_align=to_E))
    g.init()
    with screen.Screen.update():
        g.draw(x_pos=S(500), y_pos=E(600))
    traffic_cop.run(2)

def rect_as_sprite():
    message="Hello gjpqy!"
    r = rect(y_pos=E(600), height=80, width=300, as_sprite=True)
    r.init()
    for x in range(100, 801, 100):
        #print("drawing x", x)
        with screen.Screen.update():
            r.draw(x_pos=S(x))
        traffic_cop.run(0.5)

def circle_colors():
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
    traffic_cop.run(2)

def lines():
    l1 = hline(width=1, length=50)
    l1.init()
    l2 = hline(width=2, length=50)
    l2.init()
    l3 = hline(width=3, length=50)
    l3.init()
    with screen.Screen.update():
        for x in range(100, 901, 400):
            x_pos = S(x)
            for y in range(100, 901, x // 50):
                l1.draw(x_pos=x_pos, y_pos=C(y))
                l2.draw(x_pos=x_pos + 100, y_pos=C(y))
                l3.draw(x_pos=x_pos + 200, y_pos=C(y))
    traffic_cop.run(2)

def scales():
    l1 = hline(width=1, length=15)
    l1.init()
    l2 = hline(width=1, length=20)
    l2.init()
    l3 = hline(width=1, length=23)
    l3.init()
    l4 = hline(width=1, length=26)
    l4.init()
    l5 = hline(width=1, length=29)
    l5.init()
    with screen.Screen.update():
        y_pos = E(1000)
        for step_size in range(3, 8, 1):
            x_pos = S(step_size * 100)
            for y in range(0, 128 * step_size, step_size):
                y_target = y_pos - y
                #if step_size == 7 and y > 100 * step_size:
                #    print(f"{step_size=}, {y=}, {y_target=}")
                l1.draw(x_pos=x_pos, y_pos=y_target)
            for y in range(0, 128 * step_size, step_size * 5):
                l2.draw(x_pos=x_pos, y_pos=y_pos-y)
            for y in range(0, 128 * step_size, step_size * 10):
                l3.draw(x_pos=x_pos, y_pos=y_pos-y)
            for y in range(0, 128 * step_size, step_size * 50):
                l4.draw(x_pos=x_pos, y_pos=y_pos-y)
            for y in range(0, 128 * step_size, step_size * 100):
                l5.draw(x_pos=x_pos, y_pos=y_pos-y)
    traffic_cop.run(2)

def knob():
    Slider_knob.init()
    with screen.Screen.update():
        x_pos = C(900)
        y_pos = C(500)
        Slider_knob.draw(x_pos=x_pos, y_pos=y_pos)
    traffic_cop.run(1)

def slider(profile=False):
    if profile:
        import cProfile
        import time
        pr = cProfile.Profile(time.perf_counter)
    sc = Slider_control.copy(label="testing...")
    sc.init()
    with screen.Screen.update():
        x_pos = C(900)
        y_pos = S(100)
        sc.draw(x_pos=x_pos, y_pos=y_pos)
    if profile:
        pr.enable()
    traffic_cop.run(10)
    if profile:
        pr.disable()
        pr.dump_stats('slider.prof')



if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", "-p", default=False, action="store_true")
    parser.add_argument("test", nargs='?',
                        choices=("group", "rect_as_sprite", "circle_colors", "lines", "scales",
                                 "knob", "slider"))

    args = parser.parse_args()

    with screen.Screen_class():
        match args.test:
            case "group": group()
            case "rect_as_sprite": rect_as_sprite()
            case "circle_colors": circle_colors()
            case "lines": lines()
            case "scales": scales()
            case "knob": knob()
            case "slider": slider(args.profile)
            case None:
                group()
                time.sleep(2)
                screen.Screen.clear()
                rect_as_sprite()
                time.sleep(2)
                screen.Screen.clear()
                circle_colors()
                time.sleep(2)
                screen.Screen.clear()
                lines()
                time.sleep(2)
                screen.Screen.clear()
                scales()
                time.sleep(2)
                screen.Screen.clear()
                knob()
                time.sleep(2)
                screen.Screen.clear()
                slider()

