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

        horz_margin = 5
        vert_margin = 5
        #top_margin = 5
        middle_margin = 2
        #bottom_margin = 57

        # missing horz/vert_margin (both border_width)
        bt = boxed_titled(title=f"wid={border_width}", placeholders=t_placeholders,
                          border_width=border_width,
                          horz_margin=horz_margin, middle_margin=middle_margin,
                          vert_margin=vert_margin)

        print(f"{bt.border.border_width=}, {bt.horz_margin=}, {bt.vert_margin=}")
        print(f"{bt.width=}, {bt.height=}")   # width: 77-136, height: 465-513

        with screen.Screen.update():
            bt.draw(x_pos=S(x), y_pos=S(300))
        border_width += 1
        traffic_cop.run(0.1)
    traffic_cop.run(5)

def rect_margins():
    inner = rect(height=425, width=61, color=LIGHTGRAY)
    t_placeholders = dict(body=[dict(inner=inner)])
    # screen: width=1920, height=1080
    for y_i, y in enumerate(range(18, 1000, 513)):       # 2 iterations
        for x_i, x in enumerate(range(30, 1758, 140)):   # 13 iterations
            #print("drawing x", x)
            i = 13*y_i + x_i  # i ranges 0-25

            horz_margin = 5  # default 5
            vert_margin = 5  # default 5
            middle_margin = 0 + i % 7
            print(f"{y_i=}, {x_i=}, {i=}, {horz_margin=}, {vert_margin=}, {middle_margin=}")

            # missing horz/vert_margin
            bt = boxed_titled(title=f"m{middle_margin}",
                              placeholders=t_placeholders,
                              horz_margin=horz_margin,
                              vert_margin=vert_margin,
                              middle_margin=middle_margin,
                              )

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
    sc = slider(title="Testing", vert_margin=5, middle_margin=1)
    print(f"{sc.width=}, {sc.height=}")
    #midi_io.Trace = True
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
    c_1_label = static_text(text="1")
    print(f"{c_1_label.width=}, {c_1_label.height=}, "
          f"hypot={math.hypot(c_1_label.width, c_1_label.height)}")
    c_1 = circle(label=c_1_label)
    print(f"{c_1.adj_dia=}")
    c_16_label = static_text(text="16")
    print(f"{c_16_label.width=}, {c_16_label.height=}, "
          f"hypot={math.hypot(c_16_label.width, c_16_label.height)}")
    c_16 = circle(label=c_16_label)
    print(f"{c_16.adj_dia=}")
    r_1 = rect(label=static_text(text="1"))
    r_16 = rect(label=static_text(text="16"))
    r_Continue = rect(label=static_text(text="Continue"))

    br = bordered_rect(width=36, height=34)
    print(f"{br.width=}, {br.height=}")
    br2 = bordered_rect(body__width=36, body__height=34)
    print(f"{br2.width=}, {br2.height=}")
    br_1 = bordered_rect(label=static_text(text="1"))
    print(f"{br_1.width=}, {br_1.height=}")
    br_16 = bordered_rect(label=static_text(text="16"))
    print(f"{br_16.width=}, {br_16.height=}")
    br_Continue = bordered_rect(label=static_text(text="Continue"))
    print(f"{br_Continue.width=}, {br_Continue.height=}")

    rrr = rect(width=300, height=100)   # for radio buttons
    rrc = radio_control()
    rr_title = static_text(text="radio_rect")
    rr1 = radio_rect(radio_control=rrc, text="Radio 1")
    rr2 = radio_rect(radio_control=rrc, text="Radio 2")
    rr3 = radio_rect(radio_control=rrc, text="Radio 3")
    tr = toggle_rect(text="Toggle")
    trs = toggle_rect(text="Toggle Split", split=True)
    osr = one_shot_rect(text="One shot")
    ssr = start_stop_rect(text="Start/Stop")

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
        c_1.draw(x_pos=C(950), y_pos=b_y_pos)
        c_16.draw(x_pos=C(1000), y_pos=b_y_pos)

        r_y_pos = b_y_pos + 50   # 210
        r_1.draw(x_pos=C(900), y_pos=r_y_pos)
        r_16.draw(x_pos=C(950), y_pos=r_y_pos)
        r_Continue.draw(x_pos=C(1024), y_pos=r_y_pos)

        br_y_pos = r_y_pos + 50  # 260
        br_1.draw(x_pos=C(900), y_pos=br_y_pos)
        br_16.draw(x_pos=C(950), y_pos=br_y_pos)
        br_Continue.draw(x_pos=C(1024), y_pos=br_y_pos)
        br.draw(x_pos=C(950), y_pos=br_y_pos + 50)
        br2.draw(x_pos=C(950), y_pos=br_y_pos + 100)

        rrr.draw(x_pos=x_pos, y_pos=S(450))   # rect for radio buttons
        rr_title.draw(x_pos=x_pos, y_pos=E(480))
        rr1.draw(x_pos=x_pos-100, y_pos=S(500))
        rr2.draw(x_pos=x_pos, y_pos=S(500))
        rr3.draw(x_pos=x_pos+100, y_pos=S(500))
        tr.draw(x_pos=C(500), y_pos=S(500))
        trs.draw(x_pos=C(500), y_pos=S(550))
        osr.draw(x_pos=C(600), y_pos=S(500))
        ssr.draw(x_pos=C(700), y_pos=S(500))

    traffic_cop.run(10)

def spp():
    ssb = spp_start_stop()
    print(f"spp_start_stop: width={ssb.width}, height={ssb.height}")
    sr = spp_replay()       # title, button__title, gap__margin (3), color
    print(f"spp_replay: width={sr.width}, height={sr.height}")
    print(f"spp_replay: {sr.guts.mark_col.plus.border__diameter=}")
    ch = channel()
    print(f"channel: width={ch.width}, height={ch.height}")
    tr = transpose()
    print(f"transpose: width={tr.width}, height={tr.height}")
    te = tempo()
    print(f"tempo: width={te.width}, height={te.height}")
    cv = channel_volume()
    print(f"channel_volume: width={cv.width}, height={cv.height}")
    p = player()
    print(f"player: width={p.width}, height={p.height}")
    soft = soft_pedal()
    print(f"soft_pedal: width={soft.width}, height={soft.height}")
    sostenuto = sostenuto_pedal()
    print(f"sostenuto_pedal: width={sostenuto.width}, height={sostenuto.height}")
    sustain = sustain_pedal()
    print(f"sustain_pedal: width={sustain.width}, height={sustain.height}")
    n = note()
    print(f"note: width={n.width}, height={n.height}")
    with screen.Screen.update():
        #soft.draw(S(2), S(540))
        #sostenuto.draw(S(61), S(540))
        #sustain.draw(S(170), S(540))
        p.draw(S(2), S(2))      # width 514
        n.draw(S(2), S(540))
        #screenshot = screen.Screen.screenshot()     # must be done before exiting Screen.update()
    traffic_cop.run(205)
    #traffic_cop.run(35)
    #traffic_cop.run(5)
    #image_crop(screenshot, (2, 2, p.width, p.height))
    #export_image(screenshot, "player.png")
   #export_image(screenshot, "screenshot.png")      # much smaller than .bmp!
   #export_image(screenshot, "screenshot.bmp")
   #image = screen.Screen.as_image()                # these are upside down...
   #export_image(image, "as_image.png")
   #export_image(image, "as_image.bmp")



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

    # screen: width=1920 (20.75" == 0.0108"/pixel, height=1080 (11.11/16" == 0.0108"/pixel)
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

