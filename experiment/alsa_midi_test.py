# alsa_midi_test.py

import sys
import os
import time
import selectors
from alsa_midi import (SequencerClient, ControlChangeEvent, RegisteredParameterChangeEvent,
                       NonRegisteredParameterChangeEvent, NoteOnEvent, NoteOffEvent,
                       SongPositionPointerEvent)


print("My name", sys.argv[1])
client = SequencerClient(sys.argv[1])
#client_dir = dir(client)
#print(f"{client_dir=}")
print(f"{client._fd=}")
#for name in client_dir:
#    if name[0] != '_':
#        print(name, getattr(client, name))
#print("client.get_client_info()", client.get_client_info())
##print("client.get_port_info(0)", client.get_port_info(0))
#print("client.get_system_info()", client.get_system_info())
print()

port0 = client.create_port("port 0")
port1 = client.create_port("port 1")
#port_dir = dir(port)
#print(f"{port_dir=}")
#for name in port_dir:
#    if name[0] != '_':
#        print(name, getattr(port, name))
#print("port.get_info()", port.get_info())
#print()

ports = client.list_ports()
print(f"{ports=}")
print()

def get_midi_events():
    # w/false, often 0, but there's still an event.
    # w/True, always at least 1, but often more
    num_pending = client.event_input_pending(True)
    pending_time = time.time()
    print("pending", pending_time - select_time)
    print(f"{num_pending=}")
    for i in range(1, num_pending + 1):
        print("reading", i)
        event = client.event_input()
        input_time = time.time()
        print(event)

        # dest = Address(my_client_id, my_port_id)
        print(f"{event.source=}, {event.dest=}, {event.dest.port_id=}")

        print("input", input_time - pending_time)

stdin_buffer = ''
os.set_blocking(sys.stdin.fileno(), False)

prompt = "port channel param value"

def get_stdin():
    global stdin_buffer
    stdin_buffer += sys.stdin.read()
    while '\n' in stdin_buffer:
        line, stdin_buffer = stdin_buffer.split('\n', 1)
        print("stdin got line", repr(line))
        port, *params = [int(x) for x in line.split()]
        cc_event = ControlChangeEvent(*params)

        # specifying the port here still gets copied into the event at some point as it's dest
        client.event_output(cc_event, port=port)

        client.drain_output()
    print(prompt)

Sel = selectors.DefaultSelector()
Sel.register(client._fd, selectors.EVENT_READ, get_midi_events)
Sel.register(sys.stdin, selectors.EVENT_READ, get_stdin)

print(prompt)

try:
    last_select_time = None
    while True:
        for sk, sel_event in Sel.select(None):
            select_time = time.time()
            if last_select_time:
                print("time between selects", select_time - last_select_time)
            last_select_time = select_time
            assert sel_event & selectors.EVENT_READ, f"expected EVENT_READ, got {sel_event=}"
            sk.data()

finally:
    Sel.close()
