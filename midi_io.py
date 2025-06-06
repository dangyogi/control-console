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

Trace = False

client = SequencerClient("Exp Console")
Ports = [
  client.create_port("Player Control",
    PortCaps.READ | PortCaps.SUBS_READ | PortCaps.WRITE | PortCaps.SUBS_WRITE),
  client.create_port("Synth1 Control",
    PortCaps.READ | PortCaps.SUBS_READ | PortCaps.WRITE | PortCaps.SUBS_WRITE),
]

#ports = client.list_ports()
#print(f"{ports=}")
#print()

# Normal ControlChange (EventType.CONTROLLER):
#  CC, param_num, value
#
# Non-Registered Parameter Numbers:
#  CC, 98d, LSB of NRPN (Non-Registered Parameter Number)
#  CC, 99d, MSB of NRPN (Non-Registered Parameter Number)
# Registered Parameter Numbers:
#  CC, 100d, LSB of RPN (Registered Parameter Number)
#  CC, 101d, MSB of RPN (Registered Parameter Number)
# (Non-)Registered Parameter Values:
#  CC, 6d, Data MSB
#  CC, 38d, Data LSB
#  CC, 96d (+1) Data Increment, N/A
#  CC, 97d (-1) Data Decrement, N/A

Port_commands = {}   # port, type, param_num: command

@screen.register_init2
def init(screen):
    if Trace:
        print("midi_io.init")
    traffic_cop.register_read(client._fd, get_midi_events)

def register_command(command):
    if Trace:
        print(f"midi_io.register_command({command}): key={command.key()}")
    Port_commands[command.key()] = command

Control_change_types = frozenset((EventType.CONTROLLER, EventType.NONREGPARAM, EventType.REGPARAM))

def get_midi_events(_fd):
    # w/false, often 0, but there's still an event.
    # w/True, always at least 1, but often more
    if Trace:
        print("midi_io.get_midi_events")
    start_time = time.time()
    num_pending = client.event_input_pending(True)
    pending_time = time.time()
    print("pending", pending_time - start_time)
    print(f"{num_pending=}")
    screen_changed = False
    for i in range(1, num_pending + 1):
        print("reading", i)
        event = client.event_input()
        input_time = time.time()
        print("input", input_time - pending_time)
        print(event.dest.port_id, event)
        if event.type in Control_change_types: 
            key = event.dest.port_id, event.type, event.param
            if Trace:
                print(f"midi_io.get_midi_events got {key=} in Port_commands: {key in Port_commands}")
            if key in Port_commands:
                screen_changed |= Port_commands[key].remote_change(event.channel, event.value)
    return screen_changed


Midi_sent = False

def send_midi_event(port, event):
    r'''Caller should call drain_output after sending all midi_events.
    '''
    global Midi_sent
    client.event_output(event, port=port)
    Midi_sent = True

def drain_output():
    global Midi_sent
    if Midi_sent:
        client.drain_output()
        Midi_sent = False


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
        client.event_output(cc_event, port=port)
        events_sent += 1
    if events_sent:
        client.drain_output()

