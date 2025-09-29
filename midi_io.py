# midi_io.py

import sys
import os
import time
import selectors
from alsa_midi import (SequencerClient, PortCaps, EventType,
                       ControlChangeEvent, RegisteredParameterChangeEvent,
                       NonRegisteredParameterChangeEvent, NoteOnEvent, NoteOffEvent,
                       SongPositionPointerEvent)

import screen
import traffic_cop
from scale_fns import *

Trace = False

# Event_type_names[event.type] -> name
Event_type_names = {e_value.value: e_value.name for e_value in EventType}

Clocks_per_qtr = 24
Clocks_per_whole = Clocks_per_qtr * 4
Clocks_per_spp = Clocks_per_whole // 16

Client = SequencerClient("Exp Console")
Port = Client.create_port("Player Control",
                          PortCaps.READ | PortCaps.SUBS_READ | PortCaps.WRITE | PortCaps.SUBS_WRITE)

# fn() each time location changes (based on Beat_type in time signature)
# return True is screen was updated
Notify_location_fn = lambda: False

@screen.register_init2
def init(screen):
    if Trace:
        print("midi_io.init")
    traffic_cop.register_read(Client._fd, get_midi_events)

@screen.register_quit2
def quit(screen):
    if Trace:
        print("midi_io.quit")
    traffic_cop.unregister_read(Client._fd)
    Port.close()
    Client.close()

def notify_location_fn(fn):
    global Notify_location_fn
    if Trace:
        print(f"midi_io.notify_location_fn({command})")
    Notify_location_fn = fn

Clock_running = False
Clock_count = 0
Beats = None
Beat_type = None
Clocks_per_beat_type = None
Spp_per_beat_type = None

def set_spp(spp):
    r'''Returns True if screen changed.
    '''
    global Clock_count
    assert not Clock_running, "set_spp called while clock is running"
    Clock_count = spp * Clocks_per_spp
    if Clock_count % Clocks_per_beat_type == 0:
        return Notify_location_fn()
    return False

def get_spp():
    return Clock_count // Clocks_per_spp

def get_location(spp):
    beats_since_start = spp // Spp_per_beat_type
    measure, beat = divmod(beats_since_start, Beats)
    return f"{measure}.{beat}"

def get_midi_events(_fd):
    # w/false, often 0, but there's still an event.
    # w/True, always at least 1, but often more
    global Clock_running, Clock_count, Beats, Beat_type, Clocks_per_beat_type, Spp_per_beat_type

    if Trace:
        print("midi_io.get_midi_events")
    start_time = time.time()
    num_pending = Client.event_input_pending(True)
    pending_time = time.time()
    print("event_input_pending took", pending_time - start_time)
    print(f"{num_pending=}")
    screen_changed = False
    for i in range(1, num_pending + 1):
        print("reading", i, "of", num_pending)
        event = Client.event_input()
        input_time = time.time()
        print("event_input took", input_time - pending_time)
        print(event)
        match event.type:
            case EventType.CLOCK:
                if Clock_running:
                    Clock_count += 1
                    if Clock_count % Clocks_per_beat_type == 0:
                        if Notify_location_fn():
                            screen_changed = True
            case EventType.START:
                Clock_count = 0
                if Notify_location_fn():
                    screen_changed = True
                Clock_running = True
            case EventType.STOP:
                Clock_running = False
            case EventType.CONTINUE:
                Clock_running = True
           #case EventType.SONGPOS:
           #    spp = event.value
           #case EventType.SONGSEL:
           #    song_num = event.value
            case EventType.SYSTEM:
                match event.event:
                    case 0xF4:  # tempo
                        bpm = Tempo_scale.scale_rounded(event.result)
                        # FIX: do we care about this??
                        print(f"get_midi_events got tempo {bpm=} -- ignored")
                    case 0xF5:  # time signature
                        Beats, Beat_type = data_to_time_sig(event.result)
                        Clocks_per_beat_type = Clocks_per_whole // Beat_type
                        Spp_per_beat_type = Clocks_per_beat_type // Clocks_per_spp
                    case _:
                        print(f"Unrecognized SYSTEM event {event.event=} -- ignored")
           #case EventType.CONTROLLER:
           #    match event.param:
            case _:
                print(f"Unrecognized event.type {Event_type_names[event.type]} -- ignored")
    return screen_changed

def send_midi_event(event):
    r'''Also calls drain_output.
    '''
    Client.event_output(event, port=Port)
    Client.drain_output()


# FIX: Do we need to read from stdin?  If so, move to new module...
stdin_buffer = ''
os.set_blocking(sys.stdin.fileno(), False)

def get_stdin():
    global stdin_buffer
    stdin_buffer += sys.stdin.read()
    events_sent = 0
    while '\n' in stdin_buffer:
        line, stdin_buffer = stdin_buffer.split('\n', 1)
        print("stdin got line", repr(line))     # excludes '\n'
        port, *params = [int(x) for x in line.split()]
        cc_event = ControlChangeEvent(*params)
        Client.event_output(cc_event, port=Port)
        events_sent += 1
    if events_sent:
        Client.drain_output()

