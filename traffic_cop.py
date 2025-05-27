# traffic_cop.py

r'''This listens for ready files and dispatches to registered functions.

No arguments are passed to any of the functions.

register_read(file, fn)
register_write(file, fn)
unregister_read(file)
unregister_write(file)

set_alarm(delay, fn)     # delay in secs.

stop()                   # causes run to terminate

run(secs=None)           # runs for secs (forever if None), or until terminated by stop() or ^C

'''

import time
import selectors
from operator import itemgetter
import screen


def get_time():
    r'''
    '''
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)

@screen.register_init
def init(screen):
    global Sel
    Sel = selectors.DefaultSelector()

@screen.register_quit
def close():
    global Sel
    Sel.close()
    Sel = None

def register_read(file, read_fn):
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

    Alarms can not be cancelled.
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

    while not Stop and (secs is None or get_time() < end):
        while Alarms and get_time() >= Alarms[-1][0]:
            fn = Alarms.pop()[1]
            fn()
        waketime = None
        if Alarms:
            waketime = Alarms[-1][0]
        if secs is not None and (waketime is None or waketime > end):
            waketime = end
        for sk, event in Sel.select(waketime and waketime - get_time()):
            if event & selectors.EVENT_READ:
                sk.data[0]()
            if event & selectors.EVENT_WRITE:
                sk.data[1]()



if __name__ == "__main__":
    for name in "monotonic perf_counter process_time thread_time time".split():
        info = time.get_clock_info(name)
        print(f"{name=}: adj={info.adjustable}, impl={info.implementation}, "
              f"monotonic={info.monotonic}, resolution={info.resolution}")

    init(None)

    print("calling run")
    run(2)

    close()
