# sprite.py

r'''A class to add sprite capability to any rectangular image.

First create the sprite with the width and height to save:

    sprite = Sprite(30, 10)

Then call save_pos each time, just prior to drawing to the screen's render_texture.

    sprite.save_pos(30, 30)
'''

from pyray import *

from alignment import Si
import texture
import screen


class Sprite:
    def __init__(self, width, height, dynamic_capture=False, trace=False):
        r'''Captures and restores the original screen image before its changed by the user of the class.
        '''
        if trace:
            print(f"{self}.__init__, {width=}, {height=}, {dynamic_capture=}")
        self.saved_texture = texture.Texture("Sprite", width, height, fillcolor=None, trace=trace)
        self.texture_saved = False
        self.dynamic_capture = dynamic_capture
        self.trace = trace

    def __deepcopy__(self, memo):
        texture = self.saved_texture.texture.texture
        ans = Sprite(texture.width, texture.height, self.dynamic_capture, self.trace)
        if self.trace:
            print(f"{self}.__deepcopy__ -> {ans=}")
        return ans

    def close(self):
        if self.saved_texture is not None:
            self.saved_texture.close()
            self.saved_texture = None

    def save_pos(self, x_pos=0, y_pos=0):
        r'''Captures the screen image at x, y.

        x, y may be integers for the upper left corner of where to place this on the screen; or
        it can be positions to specify the left/center/right and/or upper/middle/lower rather
        than the upper left (see alignment.py).

        This needs to be called outside of begin_drawing/end_drawing.
        '''
        if self.trace:
            print(f"{self}.save_pos({x_pos=}, {y_pos=})")
        texture = self.saved_texture.texture.texture
        if self.texture_saved:
            # restore the saved image to the screen
            if self.trace:
                print(f"{self}.save_pos texture_saved, "
                      f"calling draw({self.last_x=}, {self.last_y=})")
            self.saved_texture.draw(self.last_x, self.last_y)
            if not self.dynamic_capture:
                # already have the saved_texture loaded
                self.last_x = x_pos
                self.last_y = y_pos
                return
        # not self.texture_saved or self.dynamic_capture
        #
        # capture current image in screen render_texture at x_pos, y_pos
        x_left = x_pos.S(texture.width).i
        y_lower = y_pos.E(texture.height).i
        if self.trace:
            print(f"{self} doing capture, calling saved_texture.draw_on_texture")
        with self.saved_texture.draw_on_texture():
            if self.trace:
                print(f"{self} doing capture, copying screen render_texture "
                      f"({x_left=}, {y_lower=}, {texture.width=}, {texture.height=})")
            screen.Screen.render_texture.draw_rect(x_left, y_lower, texture.width, texture.height)
        self.last_x = x_pos
        self.last_y = y_pos
        self.texture_saved = True

    def reset(self):
        self.texture_saved = False



if __name__ == "__main__":
    import doctest
    doctest.testmod()
