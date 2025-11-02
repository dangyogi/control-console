# sysex_recv.py

import time

from alsa_midi import SequencerClient, SysExEvent, PortCaps, EventType


Client = SequencerClient("sysex_recv")
Port = Client.create_port("sysex_in", PortCaps.WRITE | PortCaps.SUBS_WRITE)


for port in Client.list_ports(input=True):
    print(f"Got port {port.client_name}:{port.name}")
    if port.client_name == "sysex_send":
        print(f"Found sysex_send port", port)
        Client.subscribe_port(port, Port)
        break
else:
    print("Didn't find sysex_send port")


start = time.clock_gettime(time.CLOCK_MONOTONIC)
while time.clock_gettime(time.CLOCK_MONOTONIC) - start < 10:
    event = Client.event_input()
    print("event", event)
    if event.type == EventType.SYSEX:
        print("  event.data", event.data)

