# raylib_test.py

import time
from pyray import *


Delay = 10

width = 1920   # 0 - 1919
height = 1080  # 0 - 1079


Colors = (
    LIGHTGRAY,  # 0
    GRAY,
    DARKGRAY,
    YELLOW,
    GOLD,
    ORANGE,
    PINK,
    RED,        # 7
    MAROON,
    GREEN,      # 9
    LIME,
    DARKGREEN,
    SKYBLUE,
    BLUE,
    DARKBLUE,
    PURPLE,
    VIOLET,
    DARKPURPLE,
    BEIGE,
    BROWN,
    DARKBROWN,  # 20
    MAGENTA,    # 21

    RAYWHITE,
    WHITE,
    BLACK,
    BLANK,
)

Colors2 = (
    YELLOW,
    RED,
    GREEN,
    BLUE,
    MAGENTA,
)

def pick_color(x):
    return Colors2[x % len(Colors2)]

def draw_test(x, y, background=BLACK):
    clear_background(background)
    print("clear_background done")
    draw_text("Hello world", x, y, 20, VIOLET)
    print("draw_text done")

def line_test(thick=3):
    interval = thick + 2
    for y in range(0, height, interval):
        #draw_line_v((0, y), (1000, y), pick_color(y // interval))                     # doesn't work...
        draw_line_ex((0, y), (1000, y), thick, pick_color(y // interval))              # doesn't work...
        draw_rectangle_v((1001, y), (width - 1000, thick), pick_color(y // interval))  # works!

def rect_test():
    rect_width = 50
    rect_height = 50
    for x in range(0, 21):
        for y in range(0, height // rect_height - 1):
            draw_rectangle_v((x * rect_width, y * rect_height),
                             (rect_width, rect_height),
                             pick_color(y + (y + 1)*x))

def coord_test():
    for x in range(0, 1001, 60):
        for y in range(0, height, 15):
            draw_text(f"({x}, {y})", x, y, 10, WHITE)

try: # so finally can close the window
    set_trace_log_level(LOG_WARNING)

    init_window(width, height, "Hello")
    print(f"init_window({width=}, {height=}) done")

    if False:
        begin_drawing()
        draw_test(200, 200, BLACK)    # right-side up!
        end_drawing()
        print("draw_test done directly to screen (with begin_drawing).  Waiting", Delay, "secs.")
        time.sleep(Delay)
        print("sleep done")

    rt = load_render_texture(width, height)
    begin_texture_mode(rt)
    print("begin_texture_mode(rt) done")

    clear_background(BLACK)

    #for y in range(0, height, 3):
    #    draw_line_v((0, y), (width - 1, y), pick_color(y // 3))

    #line_test(thick=3)

    #draw_line_v((0, 0), (width - 1, height - 1), WHITE)    # goes all the way into corner
    #draw_line_v((0, 0), (width + 10, height + 10), WHITE)  # looks like it truncates out of bounds coord

    #draw_test(300, 300, BLACK)

    #rect_test()
    #coord_test()
    draw_rectangle_v((0, 100), (1000, 3), WHITE)  # rect height 3

    draw_rectangle_v((1001, 0), (width - 1002, height - 1), SKYBLUE)

    end_texture_mode()
    print("end_texture_mode done")

    capture = load_render_texture(600, 101)

    # copy rt (450, 50) (600, 101) to capture
    begin_texture_mode(capture)
    print("begin_texture_mode(capture) done")
    clear_background(RED)
    texture = capture.texture
    print(f"capture {texture.width=}, {texture.height=}")


    rt_height = rt.texture.height
    print(f"{rt_height=}")

    # draw_texture_rec(tex, (tex_x, tex_y, width, height), (dest_x, dest_y), WHITE)
    #   tex_x:  offset from tex x_left to left of rect copied from tex
    #   tex_y:  offset from tex y_lower to bottom of rect copied from text
    #           positive raises the copied rect from the bottom of tex,
    #              i.e. cuts that amount off of the bottom of tex, raps around at tex.height
    #           negative lowers the copied rect from tex
    #              i.e. wraps top abs(tex_y) of tex to the bottom of the copied rect
    #   width:  width of area copied from tex  from tex_x to dest_x
    #   height: height of area copied from tex from tex_y to dest_y
    #   dest_x: offset from x_left of dest (texture in begin_texture_mode)
    #   dest_y: offset from y_lower of dest of bottom of copied rect from tex
    #draw_texture_rec(rt.texture, (60, (rt_height - 1) - (texture.height - 1) - 300,
    #                              texture.width - 50, texture.height - 20), (10, 15), WHITE)
    #draw_texture_rec(rt.texture, (450, (rt_height - 1) - (50 + texture.height - 1),
    draw_texture_rec(rt.texture, (450, rt_height - texture.height - 50,
                                  texture.width, texture.height), (0, 0), WHITE)

    end_texture_mode()
    print("end_texture_mode done")

    # copy capture to (1001, 50) on rt
    begin_texture_mode(rt)
    print("begin_texture_mode(rt) done")
    draw_texture_rec(texture, (0, 0, texture.width, texture.height), (1001, 50), WHITE)
    end_texture_mode()
    print("end_texture_mode done")

    # draw rt to screen
    begin_drawing()
    print("begin_drawing() done")
    texture = rt.texture
    print(f"rt {texture.width=}, {texture.height=}")
    draw_texture_rec(texture, (0, 0, texture.width, -texture.height), (0, 0), WHITE)
    #                                               ^
    #                                      flipped vertically
    end_drawing()
    print("end_drawing done")
    print("Waiting", Delay, "secs.")

    time.sleep(Delay)
    print("sleep done")

finally:
    unload_render_texture(rt)
    close_window()

    #init_window(800, 450, "Hello")
    #while not window_should_close():
    #    begin_drawing()
    #    clear_background(WHITE)
    #    draw_text("Hello world", 190, 200, 20, VIOLET)
    #    end_drawing()
    #close_window()
