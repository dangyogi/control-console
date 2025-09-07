# touch.py

r'''These register themselves with the Screen.touch_dispatcher.

    - screen.Screen.Touch_dispatcher.register(self)
    - screen.Screen.Touch_dispatcher.unregister(self)

# all x, y are ints, not alignment objects

The touch_dispatcher calls the following methods on a touch object:

    - contains(x, y) -> bool
    - touch(x, y)   -> bool   # The remaining functions return True if they've changed the screen.
    - move_to(x, y) -> bool
    - release()     -> bool
'''


class SlotEvent:
    def __init__(self, slot, action, x, y, sec):
        self.slot = slot      # touch device assigned slot number
        self.action = action  # "touch", "move", "release"
        self.x = x            # int, abs screen addr in pixels
        self.y = y            # int, abs screen addr in pixels
        self.sec = sec        # not sure why you'd care about this.
                              # This combines the touch sec and usec as a float with microsec
                              # resolution.

import math

import screen
import traffic_cop


__all__ = "touch_slider circle_toggle circle_one_shot circle_start_stop circle_radio " \
          "rect_toggle rect_one_shot rect_start_stop rect_radio radio_control".split()


class touch:
    def __init__(self, name, command, trace=False):
        self.trace = trace
        self.name = name
        self.command = command
        self.active = False

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name})>"

    def attach_widget(self, widget):
        r'''Called at end of widget.__init__ method.  x_pos, y_pos not yet known...
        '''
        self.widget = widget

    def activate(self):
        r'''Called at the end of widget.draw, so x, y positions are now known
        '''
        if not self.active:
            self.active = True
            self.activate2()
            self.contains.update_pos()
            screen.Screen.Touch_dispatcher.register(self)

    def deactivate(self):
        r'''Called by clear.
        '''
        screen.Screen.Touch_dispatcher.unregister(self)
        self.active = False

    def touch(self, x, y):
        return False

    def move_to(self, x, y):
        return False

    def release(self):
        return False


class rect_contains:
    def __init__(self, widget):
        self.widget = widget
        self.width = widget.width
        self.height = widget.height
        self.update_pos()

    def update_pos(self):
        x_pos = self.widget.x_pos
        self.x_left = x_pos.S(self.width).i
        self.x_right = x_pos.E(self.width).i
        y_pos = self.widget.y_pos
        self.y_top = y_pos.S(self.height).i
        self.y_bottom = y_pos.E(self.height).i

    def __call__(self, x, y):
        return self.x_left <= x <= self.x_right \
           and self.y_top <= y <= self.y_bottom


class touch_rect(touch):
    def activate2(self):
        self.contains = rect_contains(self.widget)


class touch_slider(touch_rect):
    r'''This controls a slider_touch widget.

    slider_touch has:
        - knob
        - low_value
        - high_value
        - tick
        - scale_fn
        - num_values
        - slide_height

    Calls command.value_change(value), where value is raw (unscaled) value, used for midi data.
    '''
    def __init__(self, name, display, command, trace=False):
        r'''Called from slider.__init__.
        '''
        super().__init__(name, command, trace)
        self.display = display  # dynamic_text widget to display scaled values.

    def attach_widget(self, widget):
        r'''Called from slider_touch.__init__ with slider_touch widget.
        '''
        super().attach_widget(widget)  # stores widget in self.widget
        self.scale_fn = self.widget.scale_fn
        self.low_value = self.widget.low_value
        self.high_value = self.widget.high_value
        self.starting_value = self.widget.starting_value
        self.value = self.starting_value
        self.tick = self.widget.tick
        self.num_values = self.widget.num_values
        self.slide_height = self.widget.slide_height
        self.knob = widget.knob

    def activate2(self):
        r'''Called at the end of slider_touch.draw.
        '''
        super().activate2()
        self.slide_y_top_C = self.widget.slide_y_top_C
        self.slide_y_bottom_C = self.widget.slide_y_bottom_C
        self.knob_contains = rect_contains(self.widget.knob)

        # no recursion here, these don't call activate; slider_touch does!
        self.draw_knob()
        self.update_text()

    def touch(self, x, y):
        if not self.knob_contains(x, y):
            # do a sudden jump to the touch point!
            if self.trace:
                print(f"{self}.touch({x=}, {y=}): sudden jump!")
            self.offset = 0
            return self.move_to(x, y)
        # do incremental moves from this starting position, maintaining the offset of the touch
        # point to the knob's position.

        # self.knob.y_mid = y + self.offset
        self.offset = self.knob.y_pos.C(self.knob.height).i - y
        if self.trace:
            print(f"{self}.touch({x=}, {y=}): incremental movement {self.offset=}")
        return False

    def move_to(self, x, y):
        if self.trace:
            print(f"{self}.move_to({x=}, {y=})")
        knob_y = y + self.offset
        # clamp knob_y to the interval [self.slide_y_top_C, self.slide_y_bottom_C]
        knob_y = min(max(knob_y, self.slide_y_top_C.i), self.slide_y_bottom_C.i)
        knob_y_middle = self.knob.y_pos.C(self.knob.height).i
        pixel_movement = knob_y_middle - knob_y        # positive up
        _, remainder = divmod(pixel_movement, self.tick)
        if remainder * 2 == self.tick:  # don't count the half-way point
            tick_change = int(pixel_movement / self.tick)   # truncate
        else:
            tick_change = round(pixel_movement / self.tick) # round
        if tick_change:
            self.value += tick_change
            if self.trace:
                print(f"{self}.move_to: {knob_y=}, {pixel_movement=}, {tick_change=}, "
                      f"{self.value=}")
            if self.command is not None:
                self.command.value_change(self.value)
            self.draw_knob()
            self.update_text()
            return True
        if self.trace:
            print(f"{self}.move_to: no change, {knob_y=}, {pixel_movement=}")
        return False

    def draw_knob(self):
        self.knob.draw(y_pos=self.slide_y_bottom_C - (self.value - self.low_value) * self.tick)

    def update_text(self):
        self.display.draw(text=str(self.scale_fn(self.value)))

    def remote_change(self, channel, new_value):  # FIX: Do we really need channel here?
        r'''Called when a MIDI command is received updating the Slider's value.

        The new_value is the raw value, i.e., value.

        Returns True if the screen changed and needs a Screen.draw_to_framebuffer() done.
        '''
        if self.trace:
            print(f"{self}.remote_change {channel=}, {new_value=}")
        if new_value != self.value:
            self.value = new_value
            #if self.command is not None:
            #    self.command.value_change(self.value)
            if self.active:
                self.draw_knob()
                self.update_text()
                return True
        return False

class touch_button(touch):
    r'''Base button class for both rect_button and circle_button.
    '''
    def attach_widget(self, widget):
        r'''Called at end of widget.__init__ method.  x_pos, y_pos not yet known...
        '''
        super().attach_widget(widget)
        self.on_color = self.widget.on_color
        self.off_color = self.widget.off_color
        self.is_on = False

    def activate2(self):
        if self.is_on:
            self.show_on()
        else:
            self.show_off()

    def show_on(self):
        self.widget.draw(color=self.on_color)
        self.is_on = True
        return True

    def show_off(self):
        self.widget.draw(color=self.off_color)
        self.is_on = False
        return True

class rect_button(touch_button):
    def activate2(self):
        self.contains = rect_contains(self.widget)
        super().activate2()

class circle_contains:
    def __init__(self, widget):
        self.widget = widget
        self.width = widget.width
        self.height = widget.height
        self.touch_radius = self.widget.touch_radius
        self.update_pos()

    def update_pos(self):
        x_pos = self.widget.x_pos
        self.x_center = x_pos.C(self.width).i
        y_pos = self.widget.y_pos
        self.y_middle = y_pos.C(self.height).i

    def __call__(self, x, y):
        dist = math.hypot((x - self.x_center), (y - self.y_middle))
        return dist <= self.touch_radius

class circle_button(touch_button):
    def activate2(self):
        self.contains = circle_contains(self.widget)
        super().activate2()

class touch_toggle:
    r'''Calls command.value_change(is_on)
    '''
    def touch(self, x, y):
        if self.is_on:
            return self.turn_off()
        return self.turn_on()

    def turn_on(self):
        r'''Returns True if turned on, False if already on.
        '''
        if not self.is_on:
            self.show_on()
            if self.command is not None:
                self.command.value_change(self.is_on)
            return True
        return False

    def turn_off(self):
        r'''Returns True if turned off, False if already off.
        '''
        if self.is_on:
            self.show_off()
            if self.command is not None:
                self.command.value_change(self.is_on)
            return True
        return False

class touch_one_shot:
    r'''Calls command.act()
    '''
    def __init__(self, name, command, blink_time=0.3, trace=False):
        super().__init__(name, command, trace)
        self.blink_time = blink_time
        #self.is_on not used

    def activate2(self):
        self.is_on = False
        super().activate2()

    def touch(self, x, y):
        self.show_on()
        if self.command is not None:
            self.command.act()
        traffic_cop.set_alarm(self.blink_time, self.show_off)
        return True

class touch_start_stop:
    r'''Calls command.start() and command.stop()
    '''
    def touch(self, x, y):
        self.show_on()
        if self.command is not None:
            self.command.start()
        return True

    def activate2(self):
        self.is_on = False
        super().activate2()

    def release(self):
        self.show_off()
        if self.command is not None:
            self.command.stop()
        return True

class touch_radio(touch_toggle):
    r'''All touch_radio buttons given the same radio_control object are the same group.
    '''
    def __init__(self, name, command, radio_control, trace=False):
        super().__init__(name, command, trace)
        self.radio_control = radio_control

    def turn_on(self):
        if super().turn_on():
            self.radio_control.on(self)
            return True
        return False

    def turn_off(self, tell_radio=True):
        if super().turn_off():
            if tell_radio:
                self.radio_control.off(self)
            return True
        return False

class radio_control:
    def __init__(self):
        self.on_button = None

    def on(self, button):
        if self.on_button is not None:
            self.on_button.turn_off(tell_radio=False)
        self.on_button = button

    def off(self, button):
        if self.on_button == button:
            self.on_button = None

class circle_toggle(touch_toggle, circle_button):
    pass

class circle_one_shot(touch_one_shot, circle_button):
    pass

class circle_start_stop(touch_start_stop, circle_button):
    pass

class circle_radio(touch_radio, circle_button):
    pass

class rect_toggle(touch_toggle, rect_button):
    pass

class rect_one_shot(touch_one_shot, rect_button):
    pass

class rect_start_stop(touch_start_stop, rect_button):
    pass

class rect_radio(touch_radio, rect_button):
    pass

