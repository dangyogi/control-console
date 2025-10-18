# traffic_cop.py

r'''This listens for ready files and dispatches to registered functions.

Only one write_fn and one read_fn are allowed per file.  But the same write_fn or read_fn may be
registered against multiple files.

The registered functions are passed the file, and must return True if they've changed the Screen.

register_read(file, fn)   # calls fn(file) each time the file is readable
register_write(file, fn)  # calls fn(file) each time the file is writeable
unregister_read(file)
unregister_write(file)

Alarm functions are called with no arguments, and must return True if they've changed the Screen.

set_alarm(delay, fn)     # delay in secs.

stop()                   # causes run to terminate

run(secs=None)           # runs for secs (forever if None), or until terminated by stop() or ^C

'''

import time
import selectors
from operator import itemgetter
import screen
import midi_io


def get_time():
    r'''
    '''
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)

@screen.register_init
def init(screen):
    global Sel
    Sel = selectors.DefaultSelector()

@screen.register_quit
def close(screen):
    global Sel
    Sel.close()
    Sel = None

def register_read(file, read_fn):
    r'''Register a read_fn to be called whenever the select finds the file readable.

    The read_fn is passed the file, and must return True if it has drawn on the Screen's
    render_template.

    Only one read_fn may be registered per file, but the same read_fn may be registered against
    multiple files.
    '''
    try:
        sk = Sel.get_key(file)
    except KeyError:
        Sel.register(file, selectors.EVENT_READ, (read_fn, None))
        return
    if sk.data[0] is not None:
        raise RuntimeError(f"register_read: duplicate read_fn, {read_fn} for {file=}")
    Sel.modify(file, sk.events | selectors.EVENT_READ, (read_fn, sk.data[1]))

def unregister_read(file):
    sk = Sel.get_key(file)
    if sk.data[1] is not None:
        Sel.modify(file, Sel.EVENT_WRITE, (None, sk.data[1]))
    else:
        Sel.unregister(file)

def register_write(file, write_fn):
    r'''Register a write_fn to be called whenever the select finds the file writable.

    The write_fn is passed the file, and must return True if it has changed the Screen's
    render_template.

    Only one write_fn may be registered per file, but the same write_fn may be registered against
    multiple files.
    '''
    try:
        sk = Sel.get_key(file)
    except KeyError:
        Sel.register(file, selectors.EVENT_WRITE, (None, write_fn))
        return
    if sk.data[1] is not None:
        raise RuntimeError(f"register_write: duplicate write_fn, {write_fn} for {file=}")
    Sel.modify(file, sk.events | selectors.EVENT_WRITE, (sk.data[0], write_fn))

def unregister_write(file):
    sk = Sel.get_key(file)
    if sk.data[0] is not None:
        Sel.modify(file, Sel.EVENT_READ, (sk.data[0], None))
    else:
        Sel.unregister(file)

Alarms = []  # reverse sorted list of (time, fn)

def set_alarm(delay, fn):
    r'''Set alarm to call fn() in delay secs.

    The fn is not passed any arguments, and must return True if it has changed the Screen's
    render_template.

    Alarms can not be cancelled.

    Alarms are sorted next to fire last.
    '''
    Alarms.append((get_time() + delay, fn))
    Alarms.sort(reverse=True, key=itemgetter(0))

Stop = False

def stop():
    global Stop
    Stop = True

def run(secs=None):
    r'''Run for secs (forever if None), or until stop() or ^C.
    '''
    if secs is not None:
        end = get_time() + secs

    screen.Screen.Touch_generator.drain_events()

    while not Stop and (secs is None or get_time() < end):
        screen_changed = False
        with screen.Screen.update(draw_to_framebuffer=False):
            waketime = None
            if Alarms:
                waketime = Alarms[-1][0]
            if secs is not None and (waketime is None or waketime > end):
                waketime = end
            for sk, event in Sel.select(waketime and waketime - get_time()):
                if event & selectors.EVENT_READ:
                    screen_changed |= sk.data[0](sk.fileobj)
                if event & selectors.EVENT_WRITE:
                    screen_changed |= sk.data[1](sk.fileobj)
            while Alarms and get_time() >= Alarms[-1][0]:
                fn = Alarms.pop()[1]
                screen_changed |= fn()
        if not load_new_screen() and screen_changed:
            screen.Screen.draw_to_framebuffer()



if __name__ == "__main__":
    for name in "monotonic perf_counter process_time thread_time time".split():
        info = time.get_clock_info(name)
        print(f"{name=}: adj={info.adjustable}, impl={info.implementation}, "
              f"monotonic={info.monotonic}, resolution={info.resolution}")

    with screen.Screen_class():
        print("calling run")
        run(2)

