# tests.py

from pyray import *

from exp import *
from alignment import *
from composite import Composite
from composites import *
import screen
from shapes import *
import traffic_cop
from commands import ControlChange, Channels
import midi_io


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
    r1 = rect(y_pos=E(300), height=80, width=200, as_sprite=True).init()
    r2 = rect(y_pos=E(700), height=200, width=80).init()
    border = False
    border_width = 0
    for x in range(100, 1701, 100):
        #print("drawing x", x)
        with screen.Screen.update():
            r1.draw(x_pos=S(x), border=border, border_width=border_width)
            r2.draw(x_pos=S(x), border=border, border_width=border_width)
        border = True
        border_width += 1
        traffic_cop.run(1)
    traffic_cop.run(5)

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
        c_x_center = cir1.draw('x_center', x_pos=C(100), color=WHITE,
                               border=True, border_width=10, diameter=41)
        t1.draw(x_pos=c_x_center, text="WHITE")
        c_x_center = cir1.draw('x_center', x_pos=C(200), color=YELLOW,
                               border=True, border_width=9, diameter=39)
        t1.draw(x_pos=c_x_center, text="YELLOW")
        c_x_center = cir1.draw('x_center', x_pos=C(300), color=ORANGE,
                               border=True, border_width=8, diameter=37)
        t1.draw(x_pos=c_x_center, text="ORANGE")
        c_x_center = cir1.draw('x_center', x_pos=C(400), color=PINK,
                               border=True, border_width=7, diameter=35)
        t1.draw(x_pos=c_x_center, text="PINK")
        c_x_center = cir1.draw('x_center', x_pos=C(500), color=RED,
                               border=True, border_width=6, diameter=33)
        t1.draw(x_pos=c_x_center, text="RED")
        c_x_center = cir1.draw('x_center', x_pos=C(600), color=GREEN,
                               border=True, border_width=5, diameter=31)
        t1.draw(x_pos=c_x_center, text="GREEN")
        c_x_center = cir1.draw('x_center', x_pos=C(700), color=LIME,
                               border=True, border_width=4, diameter=29)
        t1.draw(x_pos=c_x_center, text="LIME")
        c_x_center = cir1.draw('x_center', x_pos=C(800), color=SKYBLUE,
                               border=True, border_width=3, diameter=27)
        t1.draw(x_pos=c_x_center, text="SKYBLUE")
        c_x_center = cir1.draw('x_center', x_pos=C(900), color=BLUE,
                               border=True, border_width=2, diameter=25)
        t1.draw(x_pos=c_x_center, text="BLUE")
        c_x_center = cir1.draw('x_center', x_pos=C(1000), color=PURPLE,
                               border=True, border_width=1, diameter=23)
        t1.draw(x_pos=c_x_center, text="PURPLE")
        c_x_center = cir1.draw('x_center', x_pos=C(1100), border=False, color=VIOLET)
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
    traffic_cop.run(8)

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
    Slider_vknob.init()
    with screen.Screen.update():
        x_pos = C(900)
        y_pos = C(500)
        Slider_vknob.draw(x_pos=x_pos, y_pos=y_pos)
    traffic_cop.run(1)

def slider(profile=False):
    if profile:
        import cProfile
        import time
        pr = cProfile.Profile(time.perf_counter)
    sc = Slider_control.copy(label="testing...").init()
    midi_io.Trace = True
    ControlChange(0, 0x10, Channels(1,3,5), sc.guts.slider, trace=True)
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

def buttons():
    re = rect(width=200, height=100).init()
    radio = text(text="radio").init()
    r1 = button(type="radio", border=True).init()
    r2 = button(type="radio", border=True).init()
    r3 = button(type="radio", border=True).init()
    toggle = text(text="toggle").init()
    t = button(type="toggle", border=True).init()
    mom = text(text="mom").init()
    m = button(type="mom", border=True).init()
    start_stop = text(text="start-stop").init()
    ss = button(type="start-stop", border=True).init()
    with screen.Screen.update():
        x_pos = C(300)
        text_y = E(140)
        b_y_pos = S(160)
        re_y_pos = S(110)
        re.draw(x_pos=x_pos, y_pos=re_y_pos)
        radio.draw(x_pos=x_pos, y_pos=text_y)
        r1.draw(x_pos=x_pos-60, y_pos=b_y_pos)
        r2.draw(x_pos=x_pos, y_pos=b_y_pos)
        r3.draw(x_pos=x_pos+60, y_pos=b_y_pos)
        toggle.draw(x_pos=C(500), y_pos=text_y)
        t.draw(x_pos=C(500), y_pos=b_y_pos)
        mom.draw(x_pos=C(600), y_pos=text_y)
        m.draw(x_pos=C(600), y_pos=b_y_pos)
        start_stop.draw(x_pos=C(700), y_pos=text_y)
        ss.draw(x_pos=C(700), y_pos=b_y_pos)
    traffic_cop.run(10)



if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", "-p", default=False, action="store_true")
    parser.add_argument("test", nargs='?',
                        choices=("group", "rect_as_sprite", "circle_colors", "lines", "scales",
                                 "knob", "slider", "buttons"))

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
            case "buttons": buttons()
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
                time.sleep(2)
                screen.Screen.clear()
                buttons()

