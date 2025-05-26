# composites.py

r'''A set of classes for different kinds of Composite drawings.
'''

from pyray import *

from alignment import *
from exp import *
from shapes import *
from composite import Composite
import screen


Slider_knob = Composite(rect(width=49, height=19, x_pos=P.x_center, y_pos=P.y_mid, color=BLACK),
                        rect(width=61, height=5, x_pos=P.x_center, y_pos=P.y_mid, color=GRAY),

                        width=61,
                        height=19,
                        as_sprite=True,
                        aka='Slider_knob',
                       )

class Slider(Composite):
    r'''Includes full range of knob.
    '''
    tick = 3   # num pixels knob moves per unit change in tick_value
    num_ticks = 128
    tick_value = 0
    scale_fn = staticmethod(lambda x: x)
    text_display = None
    aka = 'Slider'

    @property
    def width(self):
        return self.knob.width

    @property
    def slide_height(self):    # default 381 at tick=3, num_ticks=128
        return (self.num_ticks - 1) * self.tick

    @property
    def height(self):          # default 399
        return self.slide_height + self.knob.height - 1

    @property
    def slide_y_upper_c(self):
        return (self.y_upper + (self.knob.height - 1) // 2).as_C()

    @property
    def slide_y_lower_c(self):
        return (self.y_lower - (self.knob.height - 1) // 2).as_C()

    @property
    def value(self):
        return self.scale_fn(self.tick_value)

    @property
    def max_text(self):
        v_0 = self.scale_fn(0)
        v_max = self.scale_fn(self.num_ticks - 1)
        if len(str(v_0)) > len(str(v_max)):
            return v_0
        return v_max

    @property
    def text0(self):
        sf = self.scale_fn
        return sf(0)

    def init2(self):
        self.knob.parent = self
        self.init_components()
        self.knob.init()
        if not self.knob.trace:
            self.knob.trace = self.trace

    def draw2(self):
        super().draw2()
        self.draw_knob()
        self.update_text()
        screen.Screen.Touch_dispatcher.register(self)

    def draw_knob(self):
        self.knob.draw(x_pos=self.x_center, y_pos=self.slide_y_lower_c - self.tick_value * self.tick)

    def update_text(self):
        if self.text_display is not None:
            self.text_display.draw(text=self.scale_fn(self.tick_value))

    def touch(self, x, y):
        if not self.knob.contains(x, y):
            # do a sudden jump to the touch point!
            if self.trace:
                print(f"{self}.touch({x=}, {y=}): sudden jump!")
            self.offset = 0
            self.move_to(x, y)
        else:
            # do incremental moves from this starting position, maintaining the offset of the touch
            # point to the knob's position.

            # self.knob.y_mid = y + self.offset
            self.offset = self.knob.y_mid.i - y
            if self.trace:
                print(f"{self}.touch({x=}, {y=}): incremental movement {self.offset=}")

    def move_to(self, x, y):
        if self.trace:
            print(f"{self}.move_to({x=}, {y=})")
        knob_y = y + self.offset
        # clamp knob_y to [self.slide_y_upper_c, self.slide_y_lower_c]
        knob_y = min(max(knob_y, self.slide_y_upper_c.i), self.slide_y_lower_c.i)
        pixel_movement = self.knob.y_mid.i - knob_y        # positive up
        _, remainder = divmod(pixel_movement, self.tick)
        if remainder * 2 == self.tick:  # don't count the half-way point
            tick_change = int(pixel_movement / self.tick)
        else:
            tick_change = round(pixel_movement / self.tick)
        self.tick_value += tick_change
        if self.trace:
            print(f"{self}.move_to: {knob_y=}, {pixel_movement=}, {tick_change=}, {self.tick_value=}")
        self.draw_knob()
        self.update_text()

    def release(self):
        pass

Slider_track = Composite(
                   # centerline
                   rect(name='centerline', width=3, height=P.slider.height,
                        x_pos=P.x_center, y_pos=P.y_upper, color=BLACK),
                   Slider(name='slider',
                          knob=Slider_knob.copy(x_pos=P.x_center),
                          text_display=P.text_display,
                          x_pos=P.x_center, y_pos=P.y_upper),

                   max_text=I.slider.max_text,
                   text0=I.slider.text0,
                   aka='Slider_track')

Slider_guts = Composite(text(name='label_text', text=P.label,
                             x_pos=P.x_center, y_pos=P.y_upper + P.label_margin),
                        text(name='value_text', max_text=P.max_text, text=P.text0,
                             x_pos=P.x_center, y_pos=P.label_text.y_next + P.value_margin,
                             as_sprite=True),
                        Slider_track.copy(name='slider_track',
                             x_pos=P.x_center, y_pos=P.value_text.y_next + P.centerline_margin,
                             text_display=P.value_text),
                        gap(height=P.bottom_margin, x_pos=P.x_center, y_pos=P.slider_track.y_next),

                        label_margin=5,       # gap between top of outer rect and top of label_text
                        value_margin=3,       # gap between label_text and value_text
                        centerline_margin=5,  # gap between value_text and top of centerline
                        bottom_margin=7,      # gap between Slider_track and bottom of Slider_guts
                        text0=I.slider_track.text0,
                        max_text=I.slider_track.max_text,
                        label=P.label,
                        aka='Slider_guts',
                       )

Slider_control = Composite(rect(name='box', width=P.guts.width, height=P.guts.height,
                                x_pos=P.x_center, y_pos=P.y_upper),
                           Slider_guts.copy(name='guts', x_pos=P.x_center, y_pos=P.y_upper),

                           aka='Slider_control',
                           x_pos=C(900),
                           y_pos=S(100),
                          )



if __name__ == "__main__":
    import doctest
    doctest.testmod()
