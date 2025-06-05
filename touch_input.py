# touch_input.py

r'''Reads touch SlotEvents using libevdev.

This is designed to keep each touch slot independent so that you can drive multiple unrelated widgets
by touch at the same time.  I.e., it is not designed for multi-touch events (such as "pinch")
for a single widget.

This opens the file in non-blocking mode so that you can alternate between gen_slot_events and calls to
other code.

To use, create an Touch_generator and then repeatedly call gen_slot_events each time the input device
is readable.
'''

import os
import time
from operator import itemgetter
import libevdev
import screen
import traffic_cop

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
        return getattr(self, event.action)(event)

    def touch(self, event):
        if event.slot in self.ignore:
            self.ignore.remove(event.slot)
        if event.slot in self.assignments:
            print("Missed release for slot", event.slot)
            self.assignments[event.slot].release()
            del self.assignments[event.slot]
        for widget in self.widgets:
            if widget.contains(event.x, event.y):
                self.assignments[event.slot] = widget
                return widget.touch(event.x, event.y)
        self.ignore.add(event.slot)
        return False

    def move(self, event):
        if event.slot in self.assignments:
            if event.slot in self.ignore:
                print("Slot", event.slot, "both assigned and ignored!")
                self.ignore.remove(event.slot)
            return self.assignments[event.slot].move_to(event.x, event.y)
        elif event.slot not in self.ignore:
            print("Missed touch for slot", event.slot)
            self.ignore.add(event.slot)
        return False

    def release(self, event):
        if event.slot in self.assignments:
            if event.slot in self.ignore:
                print("Slot", event.slot, "both assigned and ignored!")
                self.ignore.remove(event.slot)
            widget = self.assignments[event.slot]
            del self.assignments[event.slot]
            return widget.release()
        elif event.slot not in self.ignore:
            print("Missed touch for slot", event.slot)
        return False


@screen.register_init2
def init_event_generator(screen_obj):
    screen_obj.Touch_generator = \
      Touch_generator(screen.Touch_device_path, screen_obj.width, screen_obj.height,
                      screen_obj.Touch_dispatcher, screen_obj.trace)

@screen.register_quit2
def close_event_generator(screen_obj):
    if screen_obj.trace:
        print("register_quit2: close_event_generator")
    screen_obj.Touch_generator.close()

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
        traffic_cop.register_read(self.device_fd, self.process_events)
        self.closed = False

    def close(self):
        if not self.closed:
            if self.trace:
                print("Touch_generator.close")
            self.drain_events()
            traffic_cop.unregister_read(self.device_fd)
            self.device_fd.close()
            self.closed = True

    def drain_events(self):
        r'''Drain all events from the input to avoid SYN_DROPPED for the next guy.
        '''
        for _ in self.gen_slot_events(ignore_syn_dropped=True):
            pass

    def process_events(self, file):
        r'''This is registered with the traffic_cop module as the read_fn for self.device_fd.

        It gets all of the touch events that have come in a sends them to the Touch_dispatcher.

        Returns True if the Touch_dispatcher updated the Screen for any of the events.
        The traffic_cop uses this to determine whether to call Screen.draw_to_framebuffer().
        '''
        change_done = False
        for event in self.gen_slot_events():
            change_done |= self.touch_dispatch.dispatch(event)
        return change_done

    def gen_slot_events(self, ignore_syn_dropped=False):
        last_moves = {} # {slot: move_event}
        events_generated = 0
        events_skipped = 0
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
                    match slot_event.action:
                        case "move":
                            if slot_event.slot in last_moves:
                                events_skipped += 1
                            last_moves[slot_event.slot] = slot_event
                        case _:
                            if slot_event.slot in last_moves:
                                yield last_moves.pop(slot_event.slot)
                                events_generated += 1
                            yield slot_event
                            events_generated += 1
                self.last_slot = self.slot = event.value
                self.sec = event.sec + event.usec / 1000000
            elif code == 'SYN_REPORT':
                if event.value != 0:
                    print(f"Expected value == 0 on SYN_REPORT, got {event.value}")
                slot_event = self.get_slotevent()
                if slot_event is not None:
                    if self.trace:
                        print("*************************")
                    match slot_event.action:
                        case "move":
                            if slot_event.slot in last_moves:
                                events_skipped += 1
                            last_moves[slot_event.slot] = slot_event
                        case _:
                            if slot_event.slot in last_moves:
                                yield last_moves.pop(slot_event.slot)
                                events_generated += 1
                            yield slot_event
                            events_generated += 1
            elif code == 'SYN_DROPPED':
                if not ignore_syn_dropped:
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
        events_generated += len(last_moves)
        yield from last_moves.values()
        #print(f"gen_slot_events, {events_generated=}, {events_skipped=}")

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
    from collections import Counter
    import argparse

    from alignment import *
    from shapes import *
    from shapes import gap

    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', '-t', action='store_true', default=False)
    parser.add_argument('width', nargs='?', type=int, default=1920)
    parser.add_argument('height', nargs='?', type=int, default=1080)

    args = parser.parse_args()

    class touch(gap):
        def touch(self, x, y):
            print(f"{x=}({abs(x-900)}), {y=}({abs(y-500)})")
            return False

        def move_to(self, x, y):
            return False

        def release(self):
            return False

    with screen.Screen_class():
        print("Screen_class created")
        t = touch(width=500, height=500, x_pos=C(900), y_pos=C(500)).init()
        screen.Screen.Touch_dispatcher.register(t)
        with screen.Screen.update():
            vline = rect(width=1, height=300).init()
            hline = rect(width=300, height=1).init()
            vline.draw(x_pos=C(900), y_pos=C(500))
            hline.draw(x_pos=C(900), y_pos=C(500))
        traffic_cop.run(5)

    '''
    try:
        traffic_cop.init(None)

        # Open the device
        gen = Touch_generator(screen.Touch_device_path, args.width, args.height, Touch_dispatcher(),
                              args.trace)

        start_time = last_time = time.time()
        last_event = None
        while time.time() - start_time < 5:
            # Read events from the device
            for slot_event in gen.gen_slot_events():
                now = time.time()
                print(f"{slot_event.action}(x={slot_event.x}, y={slot_event.y}), "
                      f"delta_t={(now - last_time)*1000} ms")
                last_time = now
                if slot_event.action == 'move':
                    if last_event is not None:
                        print("delta x", slot_event.x - last_event.x,
                              "delta y", slot_event.y - last_event.y)
                    last_event = slot_event
                if False:
                    if slot_event.slot == 0:
                        match slot_event.action:
                            case 'touch': 
                                x_counter = Counter()
                                y_counter = Counter()
                            case 'move': 
                                x_counter[slot_event.x] += 1
                                y_counter[slot_event.y] += 1
                            case 'release': 
                                print("x results:")
                                for x, count in sorted(x_counter.items(), key=itemgetter(0)):
                                    print(x, count)
                                print("y results:")
                                for y, count in sorted(y_counter.items(), key=itemgetter(0)):
                                    print(y, count)
            #print("break")
            time.sleep(0.1)
    finally:
        gen.close()
        traffic_cop.close()
    '''

