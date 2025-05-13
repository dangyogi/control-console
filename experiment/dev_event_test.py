# dev_event_test.py

import time

device_path = "/dev/input/by-id/usb-Siliconworks_SiW_HID_Touch_Controller-event-if00"

with open(device_path, 'rb') as f:
    start = time.time()
    len = 0
    print("start", start)
    while True:
        event = f.read(1)
        if time.time() - start < 0.1:
            print(hex(event[0])[2:], end='')
            len += 1
        else:
            print(": len", len)
            start = time.time()
            len = 0
