# widget_test.py

import time
import os.path
from itertools import cycle
from pyray import *

# Monitor size:
#   Max resolution: 1920x1080, 16:9 aspect ratio, projective capacitive 10-point touch
#     viewing area: 527.04mm x 296.46mm (20.75" x 11.6717")  1.7777
#     Resolutions:
#        1920x1080  1.7777
#        1680x1050  1.6
#        1440x900   1.6
#        1366x768   1.7786
#        1360x768   1.7708
#        1280x720   1.7777
#        1024x768   1.3333
#         832x624   1.3333
#         800x600   1.3333
#         720x480   1.5
#         640x480   1.3333
#   width 20.75"
#   height 11.6875"
#   aspect ratio 1.7754
#      800x450

for cf in ConfigFlags:
    print(cf.name)
#time.sleep(2)

#SKIP_FONTS=True
SKIP_FONTS=False

width = 1920
height = 1080
print(f"{width=}, {height=}")
init_window(width, height, "Hello")  # width height title
print("init_window done")

try:
    font_dir = "/usr/share/fonts/truetype/dejavu"
    Fonts = []  # Sans, Sans-Bold, Serif, Serif-Bold

    for name in 'Sans', 'Serif':
        for bold in False, True:
            path = os.path.join(font_dir, "DejaVu" + name)
            if bold:
                path += '-Bold'
            path += '.ttf'
            font = load_font(path)
            print(f"{font=}, {is_font_valid(font)=}")
            Fonts.append(font)

    #assert 0

    if True:
        begin_drawing()  # Setup canvas (framebuffer) to start drawing
        print("begin_drawing done")
        clear_background(DARKBLUE)  # BLUE DARKBLUE SKYBLUE
        print("clear_background done")
        draw_text("(0, 0) default", 0, 0, 20, WHITE)   # text posX posY fontsize color
        # draw_text_ex(font text pos size spacing tint)
        draw_text_ex(Fonts[0], "(1, 20) Sans 0", (1, 20), 20, 0, WHITE)
        draw_text_ex(Fonts[1], "(300, 0) Sans bold 0", (300, 0), 20, 0, WHITE)
        draw_text_ex(Fonts[2], "(0, 300) Serif 0", (0, 300), 20, 0, WHITE)
        draw_text_ex(Fonts[3], "(300, 300) Serif bold 0", (300, 300), 20, 0, WHITE)
        draw_text("(1800, 1060)", 1800, 1060, 20, WHITE)   # text posX posY fontsize color
        draw_text("(900, 1078)", 900, 1078, 20, WHITE)   # text posX posY fontsize color
        draw_rectangle(0, 100, 10, 10, WHITE)
        draw_rectangle(100, 0, 10, 10, WHITE)
        print("draw_text done")
        end_drawing()    # end canvas drawing and swap buffers
        print("end_drawing done")
        time.sleep(20)
        print("sleep done")
    else:
        for x in cycle(range(0, width - 49, 50)):
            if window_should_close():   # should close when ESC key hit
                break
            begin_drawing()
            print("begin_drawing done at", x, x // 2)
            clear_background(WHITE)
            draw_text("Hello world", x, x // 2, 20, VIOLET)
            #draw_fps(10, 10)
            end_drawing()
            time.sleep(2)

finally:
    close_window()    # close window and unload OpenGL context
