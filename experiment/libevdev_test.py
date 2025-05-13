# libevdev_test.py

# Example code to read input events from a device file
import os
import time
import libevdev
import sys

#for type in libevdev.types:
#    print(type)
#    print(type.codes)

# Find the device file path (replace with your actual path)
device_path = "/dev/input/by-id/usb-Siliconworks_SiW_HID_Touch_Controller-event-if00"
#device_path = "/dev/input/event4"


class SlotEvent:
    def __init__(self, slot, action, x, y, sec):
        self.slot = slot
        self.action = action  # "touch", "move", "release"
        self.x = x
        self.y = y
        self.sec = sec

    def __str__(self):
        return f"SlotEvent({self.slot}, {self.action}, {self.x}, {self.y}, {self.sec})"
               #+ ', '.join(f"{name}={getattr(self, name)}" for name in sorted(self._attrs)) \
               #+ ")"

class Event_generator:
    def __init__(self, path, width, height, trace):
        self.device_fd = open(device_path, "rb")
        os.set_blocking(self.device_fd.fileno(), False)
        self.device = libevdev.Device(self.device_fd)
        self.x_scale = width / 32767
        self.y_scale = height / 32767
        self.trace = trace
        self.last_slot = 0
        self.slot = self.x = self.y = self.sec = None
        self.action = 'move'

    def close(self):
        self.device_fd.close()

    def get_slotevent(self):
        r'''Returns SlotEvent or None
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
                print("OUCH OUCH OUCH GOT SYN_DROPPED!!!")
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



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', '-t', action='store_true', default=False)
    parser.add_argument('width', nargs='?', type=int, default=1920)
    parser.add_argument('height', nargs='?', type=int, default=1080)

    args = parser.parse_args()

    try:
        # Open the device
        gen = Event_generator(device_path, args.width, args.height, args.trace)
        device_fd = open(device_path, "rb")
        os.set_blocking(device_fd.fileno(), False)
        device = libevdev.Device(device_fd)
        print(f"Opened device: {device_path}")

        while True:
            # Read events from the device
            for slot_event in gen.gen_slot_events():
                print(slot_event)
            print("break")
            time.sleep(0.5)
    finally:
        gen.close()
