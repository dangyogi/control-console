# sprite.py

r'''A class to add sprite capability to any rectangular image.

First create the sprite to with the width and height to save:

    sprite = Sprite(30, 10)

Then call save_pos each time, just prior to updating the screen's render_texture.

    sprite.save_pos(30, 30)
'''

from pyray import *

from alignment import as_S
import screen


class Sprite:
    def __init__(width, height):
        r'''Captures and restores the original screen image before its changed by the user of the class.
        '''
        self.saved_texture = load_render_texture(width, height)
        self.texture_saved = False

    def save_pos(self, x_pos=0, y_pos=0):
        r'''Captures the screen image at x, y.

        x, y may be integers for the upper left corner of where to place this on the screen; or it can by
        positions to specify the left/center/right and/or top/middle/bottom rather than the upper (top)
        left (see alignment.py).

        This needs to be called outside of begin_drawing/end_drawing.
        '''
        if self.texture_saved:
            # restore the saved image to the screen
            begin_drawing()  # FIX
            texture = self.saved_texture.texture
            draw_texture_rec(texture,
                             (0, 0, texture.width, -texture.height),
                             (self.last_x, self.last_y),
                             WHITE)
            end_drawing()
        texture = self.saved_texture.texture
        x = as_S(x_pos, texture.width)
        y = as_S(y_pos, texture.height)
        begin_texture_mode(self.saved_texture)  # FIX
        draw_texture_rec(screen.Screen.render_texture.texture.texture,
                         (x, y, texture.width, texture.height), (0, 0), WHITE)
        end_texture_mode()
        self.last_x = x
        self.last_y = y
        self.texture_saved = True

