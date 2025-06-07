# composites.py

r'''A set of classes for different kinds of Composite drawings.
'''

from pyray import *

from alignment import *
from exp import *
from shapes import *
from drawable import Drawable
from composite import *
import screen


Slider_vknob = Composite(Stack(rect(width=49, height=19, x_pos=P.x_center, y_pos=P.y_mid, color=BLACK),
                               rect(width=61, height=5, x_pos=P.x_center, y_pos=P.y_mid, color=GRAY)),

                         #width=61,
                         #height=19,
                         as_sprite=True,
                         aka='Slider_vknob',
                        #trace=True
                        )

class Slider(Drawable):
    r'''Includes full range of knob.
    '''
    tick = 3   # num pixels knob moves per unit change in tick_value
    low_value = 0
    high_value = 127
    tick_value = 0
    scale_fn = staticmethod(lambda x: x)
    text_display = None
    midi_command = None
    aka = 'Slider'

    @property
    def value(self):
        return self.scale_fn(self.tick_value)

    def init2(self):
        self.num_ticks = (self.high_value - self.low_value) + 1
        self.slide_height = (self.num_ticks - 1) * self.tick   # default 381 at tick=3, num_ticks=128
        if len(str(self.scale_fn(self.low_value))) > len(str(self.scale_fn(self.high_value))):
            self.max_text = str(self.scale_fn(self.low_value))
        else:
            self.max_text = str(self.scale_fn(self.high_value))
        self.text0 = self.scale_fn(self.low_value)
        if self.trace:
            print(f"{self}.init2: {self.num_ticks=}, {self.slide_height=}, {self.max_text=}, "
                  f"{self.text0=}")

        # init self.knob:
        self.knob.parent = self
        self.knob.init()
        self.height = self.slide_height + self.knob.height - 1 # default 399
        self.width = self.knob.width
        if self.trace:
            print(f"{self}.init2: {self.knob.height=}, {self.knob.width=}")
        if not self.knob.trace:
            self.knob.trace = self.trace

        # create centerline:
        self.centerline = rect(name='centerline', width=3, height=self.height, color=BLACK)
        self.centerline.init()

    def draw2(self):
        super().draw2()
        self.slide_y_upper_c = (self.y_upper + (self.knob.height - 1) // 2).as_C()
        self.slide_y_lower_c = (self.y_lower - (self.knob.height - 1) // 2).as_C()
        if self.trace:
            print(f"{self}.draw2: {self.slide_y_upper_c=}, {self.slide_y_lower_c=}")
        self.centerline.draw(x_pos=self.x_center, y_pos=self.y_upper)
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
            return self.move_to(x, y)
        # do incremental moves from this starting position, maintaining the offset of the touch
        # point to the knob's position.

        # self.knob.y_mid = y + self.offset
        self.offset = self.knob.y_mid.i - y
        if self.trace:
            print(f"{self}.touch({x=}, {y=}): incremental movement {self.offset=}")
        return False

    def move_to(self, x, y):
        if self.trace:
            print(f"{self}.move_to({x=}, {y=})")
        knob_y = y + self.offset
        # clamp knob_y to the interval [self.slide_y_upper_c, self.slide_y_lower_c]
        knob_y = min(max(knob_y, self.slide_y_upper_c.i), self.slide_y_lower_c.i)
        pixel_movement = self.knob.y_mid.i - knob_y        # positive up
        _, remainder = divmod(pixel_movement, self.tick)
        if remainder * 2 == self.tick:  # don't count the half-way point
            tick_change = int(pixel_movement / self.tick)
        else:
            tick_change = round(pixel_movement / self.tick)
        if tick_change:
            self.tick_value += tick_change
            if self.trace:
                print(f"{self}.move_to: {knob_y=}, {pixel_movement=}, {tick_change=}, "
                      f"{self.tick_value=}")
            if self.midi_command is not None:
                self.midi_command.local_change()
            self.draw_knob()
            self.update_text()
            return True
        if self.trace:
            print(f"{self}.move_to: no change, {knob_y=}, {pixel_movement=}")
        return False

    def release(self):
        return False

    def get_raw_value(self):
        if self.trace:
            print(f"Slider.get_raw_value {self.tick_value=}")
        return self.tick_value

    def remote_change(self, channel, new_value):
        r'''Called when a MIDI command is received updating the Slider's value.

        The new_value is the raw value, i.e., tick_value.

        Returns True if the screen changed and needs a Screen.draw_to_framebuffer() done.
        '''
        if self.trace:
            print(f"Slider.remote_change {channel=}, {new_value=}")
        if new_value != self.tick_value:
            self.tick_value = new_value
            if self.midi_command is not None:
                self.midi_command.local_change(channel)
            self.draw_knob()
            self.update_text()
            return True
        return False



# Add label and value_text on top of Slider.
Slider_guts = Composite(Column(vgap(P.label_margin),
                               text(name='label_text', text=P.label),
                               vgap(P.value_margin),
                               text(name='value_text',
                                    max_text=P.slider.max_text, text=P.slider.text0,
                                    as_sprite=True),
                               vgap(P.centerline_margin),
                               Slider(name='slider',
                                      low_value=P.low_value,
                                      high_value=P.high_value,
                                      scale_fn=P.scale_fn,
                                      knob=Slider_vknob.copy(),
                                      text_display=P.value_text,
                                     #trace=True,
                                      init_order=1),
                               vgap(P.bottom_margin)),

                        label_margin=5,       # gap between top of outer rect and top of label_text
                        value_margin=3,       # gap between label_text and value_text
                        centerline_margin=5,  # gap between value_text and top of centerline
                        bottom_margin=7,      # gap between Slider and bottom of Slider_guts
                        label=P.label,
                        low_value=P.low_value,
                        high_value=P.high_value,
                        scale_fn=P.scale_fn,
                        aka='Slider_guts',
                       #trace=True
                       )

# Put box around Slider_guts.
Slider_control = Composite(Stack(rect(name='box',
                                      width=P.guts.width + P.extra_width + 2 * P.border_width,
                                      height=P.guts.height + 2 * P.border_width,
                                      border=P.border, border_width=P.border_width),
                                 Slider_guts.copy(name='guts', init_order=1)),

                           aka='Slider_control',
                          #border=True,
                           border=False,
                           border_width=2,
                           extra_width=14,
                           low_value=0,
                           high_value=127,
                           scale_fn=lambda x: x,
                          #trace=True
                          )



if __name__ == "__main__":
    import doctest
    doctest.testmod()
