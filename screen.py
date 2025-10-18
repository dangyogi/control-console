# screen.py

r'''The screen everything is displayed on.

Use screen.register_init(init_fn) to have your init_fn called after the screen is initialized.  Your
function will be passed the new screen object.

Use screen.register_quit(quit_fn) to register your quit_fn (shutdown fn) when the screen is shutdown.
Your function will not be passed any arguments.

Use the screen object as a context manager to close the screen at the end of the with statement.

This module also serves as a top level module that can be safely imported into all of the other modules
and used to get to shared global values.
'''

from operator import itemgetter

from pyray import *

import texture

# pyray calls of interest:
#
# check_collision_point_rec((x, y), self.usable_rect)

# pyray log levels for set_trace_log_level calls:
#    LOG_ALL = 0
#    LOG_TRACE = 1
#    LOG_DEBUG = 2
#    LOG_INFO = 3
#    LOG_WARNING = 4
#    LOG_ERROR = 5
#    LOG_FATAL = 6
#    LOG_NONE = 7

# pyray ConfigFlags:
#
# FLAG_VSYNC_HINT
# FLAG_FULLSCREEN_MODE
# FLAG_WINDOW_RESIZABLE
# FLAG_WINDOW_UNDECORATED
# FLAG_WINDOW_HIDDEN
# FLAG_WINDOW_MINIMIZED
# FLAG_WINDOW_MAXIMIZED
# FLAG_WINDOW_UNFOCUSED
# FLAG_WINDOW_TOPMOST
# FLAG_WINDOW_ALWAYS_RUN
# FLAG_WINDOW_TRANSPARENT
# FLAG_WINDOW_HIGHDPI
# FLAG_WINDOW_MOUSE_PASSTHROUGH
# FLAG_BORDERLESS_WINDOWED_MODE
# FLAG_MSAA_4X_HINT
# FLAG_INTERLACED_HINT


Colors = dict(
    LIGHTGRAY=LIGHTGRAY,
    GRAY=GRAY,
    DARKGRAY=DARKGRAY,
    YELLOW=YELLOW,
    GOLD=GOLD,
    ORANGE=ORANGE,
    PINK=PINK,
    RED=RED,
    MAROON=MAROON,
    GREEN=GREEN,
    LIME=LIME,
    DARKGREEN=DARKGREEN,
    SKYBLUE=SKYBLUE,
    BLUE=BLUE,
    DARKBLUE=DARKBLUE,
    PURPLE=PURPLE,
    VIOLET=VIOLET,
    DARKPURPLE=DARKPURPLE,
    BEIGE=BEIGE,
    BROWN=BROWN,
    DARKBROWN=DARKBROWN,
    WHITE=WHITE,
    BLACK=BLACK,
    BLANK=BLANK,
    MAGENTA=MAGENTA,
    RAYWHITE=RAYWHITE,
)

Color_names = dict((value, key) for key, value in Colors.items())


# For touch_input.py
# Find the input touch device file path
Touch_device_path = "/dev/input/by-id/usb-Siliconworks_SiW_HID_Touch_Controller-event-if00"

# For shapes.py
Font_dir = "/usr/share/fonts/truetype/dejavu"


Inits = []  # Run in ascending prio order
Quits = []  # Run in descending prio order

def register_init(init_fn, prio=1):
    r'''To get around cyclical imports so that anybody can import this module.

    These functions are passed the initialized screen.

    Can be used as a function decorator.
    '''
    Inits.append((prio, init_fn))
    return init_fn

def register_init2(init_fn, prio=2):
    r'''To get around cyclical imports so that anybody can import this module.

    These functions are passed the initialized screen.

    Can be used as a function decorator.

    register_init2 runs after all register_inits are done.
    '''
    Inits.append((prio, init_fn))
    return init_fn

def register_quit(quit_fn, prio=1):
    r'''To get around cyclical imports so that anybody can import this module.

    These functions are not passed any arguments.

    Can be used as a function decorator.
    '''
    Quits.append((prio, quit_fn))
    return quit_fn

def register_quit2(quit_fn, prio=2):
    r'''To get around cyclical imports so that anybody can import this module.

    These functions are not passed any arguments.

    Can be used as a function decorator.

    register_quit2 runs before any register_quits are done.
    '''
    Quits.append((prio, quit_fn))
    return quit_fn


class Screen_class:
    r'''Screen measures 20.75" wide, and 11.11/16" high.  That's 0.0108"/pixel in both dimensions.
    '''
    def __init__(self, width=1920, height=1080, background_color=SKYBLUE, trace=False):
        global Screen
        print(f"{width=}, {height=}")
        self.width = width
        self.height = height
        self.center_x = (width - 1) // 2 + 1
        self.center_y = (height - 1) // 2 + 1
        self.background_color = background_color
        self.trace = trace
        set_trace_log_level(LOG_WARNING)
        init_window(width, height, "Exp_console")  # width height title
        self.render_texture = texture.Texture("Screen", width, height, background_color, is_screen=True)
        #self.draw_to_framebuffer()

        Inits.sort(key=itemgetter(0))
        while Inits:  # So that we call functions added by other init funs.
            init_fn = Inits.pop(0)[1]
            init_fn(self)
        Screen = self

    def close(self):
        if self.trace:
            print("Screen.close")
        Quits.sort(key=itemgetter(0))
        while Quits:
            quit_fn = Quits.pop()[1]
            if self.trace:
                print(f"Screen_class.close running {quit_fn=}")
            quit_fn(self)
        if self.render_texture is not None:
            self.render_texture.close()
            self.render_texture = None
        close_window()

    def __enter__(self):
        pass

    def __exit__(self, *excs):
        self.close()
        return False

    def clear(self):
        with self.update(draw_to_framebuffer=False, from_scratch=True):
            pass

    def update(self, draw_to_framebuffer=True, from_scratch=False):
        r'''Directs all pyray draws to the render_texture.

        Use in 'with' statement, or as function decorator.

        If from_scratch is True, it will first clear the render_texture to the background_color.
        '''
        #print(f"Screen.update calling render_texture.draw_on_texture")
        return self.render_texture.draw_on_texture(draw_to_framebuffer=draw_to_framebuffer,
                                                   from_scratch=from_scratch)

    def draw_to_framebuffer(self):
        r'''Draws the render_texture to the screen.

        This takes ~26 mSec on rasp pi 3 B+.
        '''
        assert texture.Current_texture is None, "screen.draw_to_framebuffer: Current_texture is not None"
        begin_drawing()
        my_texture = self.render_texture.texture.texture
        #draw_texture(my_texture, x, y, WHITE)
        # inverted height here to flip image which reverse openGL flip wrt raylib.
        draw_texture_rec(my_texture, (0, 0, my_texture.width, -my_texture.height), (0, 0), WHITE)
        end_drawing()

    def as_image(self):
        return self.render_texture.as_image()

    def screenshot(self):
        return load_image_from_screen()


import touch_input



if __name__ == "__main__":
    import doctest
    doctest.testmod()
