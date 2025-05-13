# texture.py

r'''A texture class
'''

from contextlib import ContextDecorator
from pyray import *

from alignment import as_S
import screen
from sprite import Sprite


Current_texture = None

class texture:
    def __init__(self, width, height, fillcolor=BLANK, as_sprite=False, is_screen=False):
        r'''Creates a new texture.
        '''
        self.texture = load_render_texture(width, height)
        self.fillcolor = fillcolor
        self.is_screen = is_screen
        if fillcolor is not None:
            begin_texture_mode(self.texture)
            clear_background(fillcolor)
            end_texture_mode()
        self.as_sprite = as_sprite
        if as_sprite:
            self.sprite = Sprite(width, height)

    def draw_on_texture(self, to_screen_location=None, from_scratch=False):
        r'''Directs all raylib draw_x commands to draw on the texture.

        Can be used as a context manager in a 'with' statement, or as a function decorator.

        If from_scratch is True, it will blank the texture to its fillcolor at the start.

        The to_screen_location is (x_pos, y_pos) or None.  See my draw_texture method.
        '''
        class texture_mode_cm(ContextDecorator):
            def __init__(self, texture, to_screen_location, from_scratch):
                self.texture = texture
                self.to_screen_location = to_screen_location
                if to_screen_location is not None:
                    if self.texture.is_screen:
                        raise AssertionError("screen texture.draw_on_texture called with "
                                             "to_screen_location")
                    if Current_texture is not None:
                        raise AssertionError("nested texture.draw_on_texture called with "
                                             "to_screen_location")
                self.from_scratch = from_scratch

            def __enter__(self):
                global Current_texture
                texture = self.texture.texture
                if texture == Current_texture:
                    self.do_end = False
                else:
                    self.do_end = True
                    self.previous_texture = Current_texture
                    if Current_texture is not None:
                        end_texture_mode()  # for Current_texture
                    Current_texture = texture
                    begin_texture_mode(texture)
                if from_scratch:
                    clear_background(self.fillcolor)
                return self

            def __exit__(self, *exc):
                global Current_texture
                if self.do_end:
                    end_texture_mode()
                    Current_texture = self.previous_texture
                    if Current_texture is not None:
                        begin_texture_mode(Current_texture)
                if exc[0] is None and to_screen_location is not None:
                    print("draw_on_texture draw to screen")
                    # checks in my __init__ prevent this from being called when another
                    # begin_texture_mode is active, or for the screen's render_texture.
                    self.draw_to_screen(to_screen_location[0], to_screen_location[1])
                return False
        return texture_mode_cm(self, to_screen_location, from_scratch)

    def draw_to_screen(self, x_pos=0, y_pos=0):
        r'''Draws texture to the screen's render_texture at x, y.

        x, y are integers for the upper left corner of where to place this on the screen; or it can be
        positions to specify where to place the left/center/right and/or top/middle/bottom rather
        than the upper (top) left (see alignment.py).
        '''
        assert not self.is_screen, "texture.draw_to_screen called for screen's render_texture"
        texture = self.texture.texture
        x = as_S(x_pos, texture.width)
        y = as_S(y_pos, texture.height)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        with screen.Screen.update(copy_to_screen=False):
            # draw texture into screen's render_texture at x, y
            print("draw_texture: width", texture.width, "height", texture.height)
            draw_texture_rec(texture, (0, 0, texture.width, texture.height), (x, y), WHITE)

