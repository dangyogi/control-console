# midi_io.py

import sys
import os
import time
from yaml import safe_load
from alsa_midi import (SequencerClient, PortCaps, EventType,
                       StartEvent, StopEvent, ContinueEvent, ClockEvent,
                       SystemEvent,               # (event, result), i.e. (status_byte, data_byte)
                       ControlChangeEvent,        # (channel, param, value)
                       RegisteredParameterChangeEvent,
                       NonRegisteredParameterChangeEvent, NoteOnEvent, NoteOffEvent,
                       SongPositionPointerEvent,  # (channel??, value) set ch=0
                       SongSelectEvent,           # (channel??, value) set ch=0
                      )

import screen
import traffic_cop
from scale_fns import *
from spp_helpers import calibrate_spp

Trace = False

# Event_type_names[event.type] -> name
Event_type_names = {e_value.value: e_value.name for e_value in EventType}

Clocks_per_qtr = 24
Clocks_per_whole = Clocks_per_qtr * 4
Clocks_per_spp = Clocks_per_whole // 16

Client = SequencerClient("Exp Console")
print("Client:", Client.client_id)
Port = Client.create_port("Player Control",
                          PortCaps.READ | PortCaps.SUBS_READ | PortCaps.WRITE | PortCaps.SUBS_WRITE)

# connect to aseqnet
for port_info in Client.list_ports():
    if port_info.client_name == "Net Client" and port_info.port_id == 0:
        Port.connect_to(port_info)
        Port.connect_from(port_info)
        break
else:
    print("Net Client not found -- not connected")


def false(spp):
    return False

# Notify_location_fn called each time location changes (based on Beat_type in time signature).
# It is passed the new spp, and must return True if the screen was updated.
Notify_location_fn = false

# End_spp_fn called when the spp reaches End_spp.
# It is passed the final spp, and must return True if the screen was updated.
End_spp = 1000000000
End_spp_fn = false

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
    r'''fn called with new spp.  Returns True if screen changed.

    This is only called once to set the Notify_location_fn to Spp_control.set_spp.
    It is never set to anything else...
    '''
    global Notify_location_fn
    if Trace:
        print(f"midi_io.notify_location_fn({command})")
    Notify_location_fn = fn
    return False

def end_spp_fn(end_spp, fn):
    r'''fn called with current spp when end_spp is reached.  fn must return True if screen changed.
    '''
    global End_spp, End_spp_fn
    if Trace:
        print(f"midi_io.end_spp_fn({end_spp}, {fn.__name__})")
    End_spp = end_spp
    End_spp_fn = fn

def clear_end_spp():
    global End_spp, End_spp_fn
    if Trace:
        print(f"midi_io.clear_end_spp()")
    End_spp = 1000000000
    End_spp_fn = false

Clock_running = False  # FIX: delete, nobody refers to this...
Clock_count = 0
Beats = 4
Beat_type = 4
Clocks_per_beat_type = Clocks_per_whole // Beat_type
Part_duration_spp = None
Spp_per_beat_type = Clocks_per_beat_type // Clocks_per_spp
Clocks_per_measure = Clocks_per_beat_type * Beats
Spp_per_measure = Spp_per_beat_type * Beats

def get_spp():
    return Clock_count // Clocks_per_spp

def get_midi_events(_fd):
    global Clock_running, Clock_count, Beats, Beat_type, Clocks_per_beat_type, Spp_per_beat_type
    global End_spp, End_spp_fn

    if Trace:
        print("midi_io.get_midi_events")
    start_time = time.time()
    num_pending = Client.event_input_pending(True) # w/False, often 0, but there's still an event.
                                                   # w/True, always at least 1, but often more
    pending_time = time.time()
    #print("event_input_pending took", pending_time - start_time)
    #print(f"{num_pending=}")
    screen_changed = False
    while num_pending:
        num_pending -= 1
       #print("calling Client.event_input()")
        event = Client.event_input()
       #print(f"Client.event_input() -> {Event_type_names[event.type]}")
        input_time = time.time()
       #print("event_input took", input_time - pending_time)
        match event.type:
            case EventType.CLOCK:
                Clock_count += 1
                if Clock_count % Clocks_per_spp == 0:
                    spp = get_spp()
                    if Notify_location_fn(spp):
                        screen_changed = True
                    if spp >= End_spp:
                        fn = End_spp_fn
                        End_spp = 1000000000
                        End_spp_fn = false
                        if fn(spp):
                            screen_changed = True
            case EventType.START:
                # FIX: Not going to see these anymore...
                print("Got", event, "source", event.source)
                Clock_count = 0
                spp = get_spp()
                if Notify_location_fn(spp):
                    screen_changed = True
                if spp >= End_spp:
                    fn = End_spp_fn
                    End_spp = 1000000000
                    End_spp_fn = false
                    if fn(spp):
                        screen_changed = True
                Clock_running = True
            case EventType.STOP:
                # FIX: Not going to see these anymore...
                print("Got", event, "source", event.source, "Clock_count", Clock_count)
                Clock_running = False
            case EventType.CONTINUE:
                # FIX: Not going to see these anymore...
                print("Got", event, "source", event.source)
                Clock_running = True
           #case EventType.SONGPOS:
           #    spp = event.value
           #    set_spp(spp)
           #    screen_changed = True
           #case EventType.SONGSEL:
           #    song_num = event.value
            case EventType.SYSTEM:
                match event.event:
                    case 0xF4:  # tempo
                        bpm = Tempo_scale.scale_rounded(event.result)
                        #print(f"get_midi_events got tempo {bpm=}, {event.source=} -- ignored")
                    case 0xF5:  # time signature
                        Beats, Beat_type = data_to_time_sig(event.result)
                        print("Got time signature", Beats, Beat_type, "source", event.source)
                        Clocks_per_beat_type = Clocks_per_whole // Beat_type
                        Spp_per_beat_type = Clocks_per_beat_type // Clocks_per_spp
                        Clocks_per_measure = Clocks_per_beat_type * Beats
                        Spp_per_measure = Spp_per_beat_type * Beats
                    case _:
                        print(f"Unrecognized SYSTEM event {event.event=}, {event.source=} -- ignored")
           #case EventType.CONTROLLER:
           #    match event.param:
            case EventType.SYSEX:
                measure_info = safe_load(event.data.decode("ASCII"))
                calibrate_spp(measure_info["clocks_per_measure"],
                              measure_info["part_duration_clocks"],
                              measure_info["skips"],
                              measure_info["odd_durations"])
                num_pending = Client.event_input_pending(True)
            case _:
                print(f"Unrecognized event.type {Event_type_names[event.type]}, "
                      f"{event.source=} -- ignored")
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

