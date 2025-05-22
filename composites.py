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
                        aka='Slider_knob')

class Slider(Composite):
    tick = 3
    num_ticks = 128
    scale_fn = staticmethod(lambda x: x)
    text_display = None
    knob_drawn = False
    aka = 'Slider'

    @property
    def width(self):
        return self.knob.width

    @property
    def height(self):
        return (self.num_ticks - 1) * self.tick

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

    def init2(self):
        self.init_components()

    def draw2(self):
        super().draw2()
        if not self.knob_drawn:
            self.tick_value = 0
            self.knob.draw(y_pos=self.y_lower.as_C())
            self.knob_drawn = True
            self.update_text()
            screen.Screen.Touch_dispatcher.register(self)

    def update_text(self):
        if self.text_display is not None:
            self.text_display.draw(text=self.scale_fn(self.tick_value))

    def touch(self, x, y):
        if not self.knob.contains(x, y):
            # do a sudden jump to the touch point!
            self.offset = 0
            self.move_to(x, y)
        else:
            # do incremental moves from this starting position, maintaining the offset of the touch
            # point to the knob's position.

            # self.knob.y_center = y + self.offset
            self.offset = self.knob.y_center - y

    def move_to(self, x, y):
        y += self.offset
        y = min(max(y, self.y_upper), self.y_lower)   # clamp y to [self.y_upper, self.y_lower]
        pixel_movement = self.knob.y_center - y
        _, remainder = divmod(pixel_movement, self.tick)
        if remainder * 2 == self.tick:  # don't count the half-way point
            tick_change = int(pixel_movement / self.tick)
        else:
            tick_change = round(pixel_movement / self.tick)
        self.tick_value += tick_change
        y = self.y_lower - self.value * self.tick + self.offset
        self.knob.draw(y_pos=C(y))
        self.update_text()

    def release(self):
        pass

Slider_track = Composite(
                   # centerline
                   rect(name='centerline', width=3, height=P.slider.height + P.knob.height,
                        x_pos=P.x_center, y_pos=P.y_upper),
                   Slider(name='slider', knob=P.knob,
                          x_pos=P.x_center, y_pos=P.y_upper + P.knob.height // 2),
                   knob=Slider_knob.copy(x_pos=P.x_center),
                   max_text=I.slider.max_text,
                   aka='Slider_track')

Slider_guts = Composite(text(name='label_text', text=P.label,
                             x_pos=P.x_center, y_pos=P.y_upper + P.label_margin),
                        text(name='value_text', max_text=P.max_text,
                             x_pos=P.x_center, y_pos=P.label_text.y_next + P.value_margin),
                        Slider_track.copy(name='slider_track',
                             x_pos=P.x_center, y_pos=P.value_text.y_next + P.centerline_margin),
                        label_margin=5,       # gap between top of outer rect and top of label_text
                        value_margin=3,       # gap between label_text and value_text
                        centerline_margin=5,  # gap between value_text and top of centerline
                        max_text=I.slider_track.max_text,
                        label=P.label,
                        aka='Slider_guts',
                       )

Slider_control = Composite(rect(name='box', width=P.guts.width, height=P.guts.height),
                           Slider_guts.copy(name='guts', x_pos=P.x_center, y_pos=P.y_upper),
                           aka='Slider_control',
                          )



if __name__ == "__main__":
    import doctest
    doctest.testmod()
