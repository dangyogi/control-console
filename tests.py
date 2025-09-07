# tests.py

import math

from pyray import *

from alignment import *
import screen
from shapes import *
from slider import *
from containers import *
from buttons import *
from song_position import *
from controls import *
import traffic_cop
from commands import ControlChange, Channels
import midi_io


def hline(length, width=3):
    return rect(height=width, width=length, color=BLACK)

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

def rect_borders():
    inner = rect(height=425, width=61, color=LIGHTGRAY)
    t_placeholders = dict(body=[dict(inner=inner)])
    border_width = 1
    # screen: width=1920, height=1080
    for x in range(30, 1758, 140):  # 12 iterations
        #print("drawing x", x)

        top_margin = 5
        middle_margin = 4
        bottom_margin = 7

        # missing horz/vert_margin (both border_width)
        bt = boxed_titled(title=f"width={border_width}", placeholders=t_placeholders,
                          border_width=border_width,
                          top_margin=top_margin, middle_margin=middle_margin,
                          bottom_margin=bottom_margin)

        print(f"{bt.width=}, {bt.height=}")   # width: 77-136, height: 465-513

        with screen.Screen.update():
            bt.draw(x_pos=S(x), y_pos=S(300))
        border_width += 1
        traffic_cop.run(0.1)
    traffic_cop.run(5)

def rect_margins():
    inner = rect(height=425, width=61, color=LIGHTGRAY)
    t_placeholders = dict(body=[dict(inner=inner)])
    border_width = 5
    # screen: width=1920, height=1080
    for y_i, y in enumerate(range(18, 1000, 513)):       # 2 iterations
        for x_i, x in enumerate(range(30, 1758, 140)):   # 13 iterations
            #print("drawing x", x)
            i = 13*y_i + x_i

            top_margin = 8
            middle_margin = 5 + i // 5
            bottom_margin = 5 + i % 5
            print(f"{y_i=}, {x_i=}, {i=}, {top_margin=}, {middle_margin=}")

            # missing horz/vert_margin (both border_width)
            bt = boxed_titled(title=f"mid={middle_margin} bot={bottom_margin}",
                              placeholders=t_placeholders, border_width=border_width,
                              top_margin=top_margin, middle_margin=middle_margin,
                              bottom_margin=bottom_margin)

            print(f"{bt.width=}, {bt.height=}")   # width: 77-136, height: 465-513

            with screen.Screen.update():
                bt.draw(x_pos=S(x), y_pos=S(y))
            traffic_cop.run(0.1)
    traffic_cop.run(25)

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
    sc = slider(title="Testing...", top_margin=5, middle_margin=5)
    print(f"{sc.width=}, {sc.height=}")
    #midi_io.Trace = True
    #ControlChange(0, 0x10, Channels(1,3,5), sc.guts.slider, trace=True)
    with screen.Screen.update():
        x_pos = C(900)
        y_pos = S(100)
        sc.draw(x_pos=x_pos, y_pos=y_pos)
        print(f"slider: width={sc.width} height={sc.height}")
    if profile:
        pr.enable()
    traffic_cop.run(15)
    if profile:
        pr.disable()
        pr.dump_stats('slider.prof')

def buttons():
    re = rect(width=200, height=100)   # for radio buttons
    rc = radio_control()
    radio = static_text(text="radio")
    r1 = radio_circle(radio_control=rc, label=static_text(text="1"), off_color=GRAY)
    r2 = radio_circle(radio_control=rc, label=static_text(text="2"), off_color=DARKGRAY)
    r3 = radio_circle(radio_control=rc, label=static_text(text="3"))
    toggle = static_text(text="toggle")
    t = toggle_circle()
    one_shot = static_text(text="one-shot")
    os = one_shot_circle()  # blink_time = 0.3
    start_stop = static_text(text="start-stop")
    ss = start_stop_circle()
    c = circle()
    print(f"{c.diameter=}")
    c1_label = static_text(text="1")
    print(f"{c1_label.width=}, {c1_label.height=}, "
          f"hypot={math.hypot(c1_label.width, c1_label.height)}")
    c1 = circle(label=c1_label)
    print(f"{c1.adj_dia=}")
    c16_label = static_text(text="16")
    print(f"{c16_label.width=}, {c16_label.height=}, "
          f"hypot={math.hypot(c16_label.width, c16_label.height)}")
    c16 = circle(label=c16_label)
    print(f"{c16.adj_dia=}")
    with screen.Screen.update():
        x_pos = C(300)
        text_y = E(140)
        b_y_pos = S(160)
        re_y_pos = S(110)
        re.draw(x_pos=x_pos, y_pos=re_y_pos)
        radio.draw(x_pos=x_pos, y_pos=text_y)       # "radio" text
        r1.draw(x_pos=x_pos-60, y_pos=b_y_pos)
        r2.draw(x_pos=x_pos, y_pos=b_y_pos)
        r3.draw(x_pos=x_pos+60, y_pos=b_y_pos)
        toggle.draw(x_pos=C(500), y_pos=text_y)     # "toggle" text
        t.draw(x_pos=C(500), y_pos=b_y_pos)
        one_shot.draw(x_pos=C(600), y_pos=text_y)   # "one_shot" text
        os.draw(x_pos=C(600), y_pos=b_y_pos)
        start_stop.draw(x_pos=C(700), y_pos=text_y) # "start_stop" text
        ss.draw(x_pos=C(700), y_pos=b_y_pos)
        c.draw(x_pos=C(900), y_pos=b_y_pos)
        c1.draw(x_pos=C(950), y_pos=b_y_pos)
        c16.draw(x_pos=C(1000), y_pos=b_y_pos)
    traffic_cop.run(10)

def spp():
    tos = titled_one_shot()     # title, gap__margin (3)
    sd = spp_display()          # title, color
    ssb = spp_start_stop()
    sr = spp_replay()       # title, button__title, gap__margin (3), color
    tr = transpose()
    te = tempo()
    sv = synth_volume()
    p1 = player_row1()
    p2 = player_row2()
    p = player()
    pspp = player_spp()
    #pa = player_all(color=(255, 130, 255))
    pa = player_all()
    with screen.Screen.update():
        #y_pos = S(100)
        #x_pos = S(30)
        #for x, widget in zip(range(30, 1900, 113), (tr, te, sv)):
        #    widget.draw(x_pos, y_pos)
        #    x_pos += widget.width + 29
        #    print(f"{widget.name}: width={widget.width} height={widget.height}")
        #y_pos = S(600)
        #x_pos = S(30)
        #for x, widget in zip(range(30, 1900, 193), (# tos, sd,
        #                                             ssb, sr)):
        #    widget.draw(x_pos, y_pos)
        #    x_pos += widget.width + 29
        #    print(f"{widget.name}: width={widget.width} height={widget.height}")
        pa.draw(S(2), S(2))
        #pa.draw(S(2), S(540))
        print(f"{pa.name}: width={pa.width} height={pa.height}")
        p.draw(S(400), S(2))
        print(f"{p.name}: width={p.width} height={p.height}")
        pspp.draw(S(400), S(540))
        print(f"{pspp.name}: width={pspp.width} height={pspp.height}")
        p.draw(S(800), S(2))
        p.draw(S(800), S(540))
    traffic_cop.run(15)



if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", "-p", default=False, action="store_true")
    parser.add_argument("test", nargs='?',
                        choices=("group", "rect_borders", "rect_margins", 
                                 "circle_colors", "lines", "scales",
                                 "knob", "slider", "buttons", "spp"))

    args = parser.parse_args()

    # screen: width=1920, height=1080
    with screen.Screen_class():
        print(f"{screen.Screen.width=}, {screen.Screen.height=}")
        match args.test:
            case "group": group()
            case "rect_borders": rect_borders()
            case "rect_margins": rect_margins()
            case "circle_colors": circle_colors()
            case "lines": lines()
            case "scales": scales()
            case "knob": knob()
            case "slider": slider_test(args.profile)
            case "buttons": buttons()
            case "spp": spp()
            case None:
                group()
                time.sleep(2)
                screen.Screen.clear()
                rect_borders()
                time.sleep(2)
                rect_margins()
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
                time.sleep(2)
                screen.Screen.clear()
                spp()

