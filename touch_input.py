# touch_input.py

r'''Reads touch SlotEvents using libevdev.

This is designed to keep each touch slot independent so that you can drive multiple unrelated widgets
by touch at the same time.  I.e., it is not designed for multi-touch events (such as "pinch")
for a single widget.

This opens the file in non-blocking mode so that you can alternate between gen_slot_events and calls to
other code.

To use, create an Touch_generator and then repeatedly call gen_slot_events with a sleep between calls
(< 0.5 secs to avoid SYN_DROPPED).
'''

import os
import time
from operator import itemgetter
import libevdev
import screen

#for type in libevdev.types:
#    print(type)
#    print(type.codes)


class Syn_dropped(RuntimeError):
    pass


class SlotEvent:
    def __init__(self, slot, action, x, y, sec):
        self.slot = slot      # touch device assigned slot number
        self.action = action  # "touch", "move", "release"
        self.x = x            # int, abs screen addr in pixels
        self.y = y            # int, abs screen addr in pixels
        self.sec = sec        # not sure why you'd care about this.
                              # This combines the touch sec and usec as a float with microsec
                              # resolution.

    def __str__(self):
        return f"SlotEvent({self.slot}, {self.action}, {self.x}, {self.y}, {self.sec})"
               #+ ', '.join(f"{name}={getattr(self, name)}" for name in sorted(self._attrs)) \
               #+ ")"


@screen.register_init
def init_touch_dispatcher(screen_obj):
    screen_obj.Touch_dispatcher = Touch_dispatcher()

class Touch_dispatcher:
    def __init__(self):
        self.ignore = set()
        self.widgets = []
        self.assignments = {}

    def reset(self):
        self.ignore = set(self.assignments.keys())
        self.assignments = {}
        self.widgets = []

    def register(self, widget):
        self.widgets.append(widget)

    def unregister(self, widget):
        self.widgets.remove(widget)

    def dispatch(self, event):
        getattr(self, event.action)(event)

    def touch(self, event):
        if event.slot in self.ignore:
            self.ignore.remove(event.slot)
        if event.slot in self.assignments:
            print("Missed release for slot", event.slot)
            self.assignments[event.slot].release()
        for widget in self.widgets:
            if widget.contains(event.x, event.y):
                self.assignments[event.slot] = widget
                widget.touch(event.x, event.y)
                break
        else:
            self.ignore.add(event.slot)

    def move(self, event):
        if event.slot in self.assignments:
            if event.slot in self.ignore:
                print("Slot", event.slot, "both assigned and ignored!")
                self.ignore.remove(event.slot)
            self.assignments[event.slot].move_to(event.x, event.y)
        elif event.slot not in self.ignore:
            print("Missed touch for slot", event.slot)
            self.ignore.add(event.slot)

    def release(self, event):
        if event.slot in self.assignments:
            if event.slot in self.ignore:
                print("Slot", event.slot, "both assigned and ignored!")
                self.ignore.remove(event.slot)
            self.assignments[event.slot].release()
        elif event.slot not in self.ignore:
            print("Missed touch for slot", event.slot)


@screen.register_init
def init_event_generator(screen_obj):
    screen_obj.Touch_generator = \
      Touch_generator(screen.Touch_device_path, screen_obj.width, screen_obj.height,
                      screen_obj.Touch_dispatcher, screen_obj.trace)

class Touch_generator:
    r'''width, height in pixels.

    Use gen_slot_events to get all queued events.  Delaying > 0.5 secs between calls may produce
    SYN_DROPPED messages.
    '''
    def __init__(self, path, width, height, touch_dispatch, trace=False):
        self.device_fd = open(path, "rb")
        os.set_blocking(self.device_fd.fileno(), False)
        self.device = libevdev.Device(self.device_fd)
        self.x_scale = width / 32767
        self.y_scale = height / 32767
        self.trace = trace
        self.last_slot = 0
        self.slot = self.x = self.y = self.sec = None
        self.action = 'move'
        self.touch_dispatch = touch_dispatch
        screen.register_quit(self.close)
        self.timers = []

    def close(self):
        self.device_fd.close()

    def add_timer(self, delay, fn):
        trigger_time = time.time() + delay
        self.timers.append((trigger_time, fn))
        self.timers.sort(key=itemgetter(0), reverse=True)

    def run(self, secs=None):
        r'''Runs for secs seconds, or forever if secs is None.
        '''
        if secs is not None:
            end = time.time() + secs
        while secs is None or time.time() < end:
            with screen.Screen.update(draw_to_framebuffer=True):
                saw_events = 0
                while True:
                    for event in self.gen_slot_events():
                        self.touch_dispatch.dispatch(event)
                        saw_events += 1
                    while self.timers and time.time() >= self.timers[-1][0]:
                        fn = self.timers.pop()[1]
                        if self.trace:
                            print("run got timer", fn)
                        fn()
                        saw_events += 1
                    if saw_events or (secs is not None and time.time() > end - 0.1):
                        break  # break out of with to draw_to_framebuffer and re-enter with
                    time.sleep(0.1)

    def gen_slot_events(self):
        for event in self.device.events():
            # event attrs: type, code, value, sec, usec
            if event.code is None:
                code = event.type.name
            else:
                code = event.code.name
            if code == 'ABS_MT_SLOT':
                if self.trace:
                    print("got event", code, event.value)
                slot_event = self.get_slotevent()
                if slot_event is not None:
                    yield slot_event
                self.last_slot = self.slot = event.value
                self.sec = event.sec + event.usec / 1000000
            elif code == 'SYN_REPORT':
                if event.value != 0:
                    print(f"Expected value == 0 on SYN_REPORT, got {event.value}")
                slot_event = self.get_slotevent()
                if slot_event is not None:
                    if self.trace:
                        print("*************************")
                    yield slot_event
            elif code == 'SYN_DROPPED':
                raise Syn_dropped
            else:
                if code == 'ABS_MT_TRACKING_ID':
                    if event.value == -1:
                        self.action = 'release'
                    else:
                        self.action = 'touch'
                elif code == 'ABS_MT_POSITION_X':
                    self.x = event.value
                elif code == 'ABS_MT_POSITION_Y':
                    self.y = event.value
                elif code in {'ABS_X', 'ABS_Y', 'BTN_TOUCH', 'MSC_TIMESTAMP'}:
                    # ignore
                    continue
                else:
                    print(f"!!!!!!!!! Unexpected code: {code}")
                    # ignore
                    continue
                if self.trace:
                    print("got event", code, event.value)
                if self.slot is None:
                    self.slot = self.last_slot
                    self.sec = event.sec + event.usec / 1000000
        assert self.slot is None, "gen_slot_events: expected slot is None on loop exit"

    def get_slotevent(self):
        r'''Checks to see if SlotEvent is soup yet.

        Returns SlotEvent or None.
        '''
        if self.slot is not None:
            if self.sec is None:
                print("!!!!!!!!! missing sec: Internal Error!")
            if self.action == 'release':
                slot_event = SlotEvent(self.slot, self.action, None, None, self.sec)
            else:
                if self.x is None and self.action != 'release':
                    print("!!!!!!!!! missing ABS_MT_POSITION_X")
                if self.y is None and self.action != 'release':
                    print("!!!!!!!!! missing ABS_MT_POSITION_Y")
                slot_event = SlotEvent(self.slot, self.action,
                                       int(round(self.x * self.x_scale)),
                                       int(round(self.y * self.y_scale)),
                                       self.sec)
            self.slot = self.sec = None
            self.action = 'move'
            if self.trace:
                print("get_slotevent -> slotevent")
            return slot_event
        return None




if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', '-t', action='store_true', default=False)
    parser.add_argument('width', nargs='?', type=int, default=1920)
    parser.add_argument('height', nargs='?', type=int, default=1080)

    args = parser.parse_args()

    try:
        # Open the device
        gen = Touch_generator(screen.Touch_device_path, args.width, args.height, Touch_dispatcher(),
                              args.trace)

        while True:
            # Read events from the device
            for slot_event in gen.gen_slot_events():
                print(slot_event)
            print("break")
            time.sleep(0.1)
    finally:
        gen.close()

