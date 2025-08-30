# tests.py

from pyray import *

from alignment import *
import screen
from shapes import *
from slider import *
from containers import *
import traffic_cop
from commands import ControlChange, Channels
import midi_io


def hline(length, width=3):
    return rect(height=width, width=length)

def group():
    message="Hello gjpqy!"
    widgets = (static_text(name='txt', size=80, text=message, trace=True),
               rect(name='r', height=80, width=300),
               circle(name='c', diameter=80),
               hline(length=40),
              )
    with screen.Screen.update():
        x_pos = S(500)
        y_pos = E(600)
        for widget in widgets:
            widget.draw(x_pos=x_pos, y_pos=y_pos)
            x_pos += widget.width
    traffic_cop.run(2)

def rect_as_sprite():
    r1 = rect(height=80, width=200)
    r2 = rect(height=200, width=80)
    border = False
    border_width = 0
    for x in range(100, 1701, 100):
        #print("drawing x", x)
        with screen.Screen.update():
            #r1.draw(x_pos=S(x), y_pos=E(300), border=border, border_width=border_width)
            #r2.draw(x_pos=S(x), y_pos=E(700), border=border, border_width=border_width)
            r1.draw(x_pos=S(x), y_pos=E(300))
            r2.draw(x_pos=S(x), y_pos=E(700))
        border = True
        border_width += 1
        traffic_cop.run(1)
    traffic_cop.run(5)

def circle_colors():
    r = rect(width=1200, height=350)

    def draw_color(x_pos, y_pos, color, border_width, diameter):
        if border_width > 0:
            circle_widget = bordered_circle(border_width=border_width, diameter=diameter)
        else:
            circle_widget = circle()
        circle_widget.draw(x_pos=C(x_pos), y_pos=C(y_pos), color=screen.Colors[color])
        static_text(text=color).draw(x_pos=C(x_pos), y_pos=E(y_pos-50))

    with screen.Screen.update():
        r.draw(x_pos=S(50), y_pos=S(300))

        # LED on:
        for i, color in enumerate("WHITE YELLOW ORANGE PINK RED GREEN LIME SKYBLUE BLUE "
                                  "PURPLE VIOLET MAGENTA".split()):
            draw_color(100 + 100*i, 400, color, 10 - i, 41 - 2*i)

        # LED off:
        for i, color in enumerate("LIGHTGRAY GRAY DARKGRAY BEIGE BROWN DARKBROWN BLACK".split()):
            draw_color(100 + 100*i, 600, color, 0, 41)

    traffic_cop.run(8)

def lines():
    l1 = hline(width=1, length=50)
    l2 = hline(width=2, length=50)
    l3 = hline(width=3, length=50)
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
    l2 = hline(width=1, length=20)
    l3 = hline(width=1, length=23)
    l4 = hline(width=1, length=26)
    l5 = hline(width=1, length=29)
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
    vknob = slider_vknob()
    with screen.Screen.update():
        x_pos = C(900)
        y_pos = C(500)
        vknob.draw(x_pos=x_pos, y_pos=y_pos)
    traffic_cop.run(2)

def slider_test(profile=False):
    if profile:
        import cProfile
        import time
        pr = cProfile.Profile(time.perf_counter)
    sc = slider(title="testing...")
    print(f"{sc.width=}, {sc.height=}")
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
    re = rect(width=200, height=100)
    rc = radio_control()
    radio = text(text="radio")
    r1 = button(type="radio", radio_control=rc, border=True)
    r2 = button(type="radio", radio_control=rc, border=True)
    r3 = button(type="radio", radio_control=rc, border=True)
    toggle = text(text="toggle")
    t = button(type="toggle", border=True)
    mom = text(text="mom")
    m = button(type="mom", border=True)
    start_stop = text(text="start-stop")
    ss = button(type="start-stop", border=True)
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
        print(f"{screen.Screen.width=}, {screen.Screen.height=}")
        match args.test:
            case "group": group()
            case "rect_as_sprite": rect_as_sprite()
            case "circle_colors": circle_colors()
            case "lines": lines()
            case "scales": scales()
            case "knob": knob()
            case "slider": slider_test(args.profile)
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
                slider_test()
                time.sleep(2)
                screen.Screen.clear()
                buttons()

