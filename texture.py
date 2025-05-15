# texture.py

r'''A Texture class, specifically render_textures that can be drawn on the screen.
'''

from contextlib import ContextDecorator
from pyray import *

from alignment import Si
import screen
import sprite


Current_texture = None

class Texture:
    def __init__(self, width, height, fillcolor=BLANK, as_sprite=False, is_screen=False):
        r'''Creates a new render texture.
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
            self.sprite = sprite.Sprite(width, height)

    def draw_on_texture(self, draw_to_framebuffer=False, from_scratch=False):
        r'''Directs all raylib draw_x commands to draw on the texture.

        Can be used as a context manager in a 'with' statement, or as a function decorator.

        If from_scratch is True, it will blank the texture to its fillcolor at the start.

        The draw_to_framebuffer parameter causes the screen's render_template to be drawn to the
        framebuffer.  This can only be used for the texture containing the screen's render_template.
        '''
        class texture_mode_cm(ContextDecorator):
            def __init__(self, texture, draw_to_framebuffer, from_scratch):
                self.texture = texture  # Texture object
                self.draw_to_framebuffer = draw_to_framebuffer
                if draw_to_framebuffer:
                    if not self.texture.is_screen:
                        raise AssertionError("normal Texture (not screen render_texture) called with "
                                             "draw_to_framebuffer")
                    if Current_texture is not None:
                        raise AssertionError("nested Texture.draw_on_texture called with "
                                             "draw_to_framebuffer")
                self.from_scratch = from_scratch

            def __enter__(self):
                global Current_texture
                if self.texture.texture == Current_texture:
                    self.do_end = False
                else:
                    self.do_end = True
                    self.previous_texture = Current_texture
                    if Current_texture is not None:
                        end_texture_mode()  # for Current_texture
                    Current_texture = self.texture.texture
                    begin_texture_mode(self.texture.texture)
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
                if exc[0] is None and self.draw_to_framebuffer:
                    print("draw_on_texture -> screen.Screen.draw_to_framebuffer")
                    # checks in my __init__ prevent this from being called when another
                    # begin_texture_mode is active, or when this is not the screen's render_texture.
                    screen.Screen.draw_to_framebuffer()
                return False
        return texture_mode_cm(self, draw_to_framebuffer, from_scratch)

    def draw_to_screen(self, x_pos=0, y_pos=0):
        r'''Draws texture to the screen's render_texture at x, y.

        x, y are integers for the upper left corner of where to place this on the screen; or it can be
        positions to specify where to place the left/center/right and/or top/middle/bottom rather
        than the upper (top) left (see alignment.py).
        '''
        assert not self.is_screen, "Texture.draw_to_screen called for screen's render_texture"
        texture = self.texture.texture
        x = Si(x_pos, texture.width)
        y = Si(y_pos, texture.height)
        if self.as_sprite:
            self.sprite.save_pos(x, y)
        with screen.Screen.update(draw_to_framebuffer=False):
            # draw texture into screen's render_texture at x, y
            draw_texture(texture, x, y, WHITE)



if __name__ == "__main__":
    import doctest
    doctest.testmod()
