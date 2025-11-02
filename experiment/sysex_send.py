# sysex_send.py

import time

from alsa_midi import SequencerClient, SysExEvent, PortCaps


Test_msg_file = "measures.yaml"


Client = SequencerClient("sysex_send")
Port = Client.create_port("sysex_out", PortCaps.READ | PortCaps.SUBS_READ)

with open(Test_msg_file, "rt") as test_msg:
    Test_msg = test_msg.read().encode("ASCII")


for port in Client.list_ports(output=True):
    print(f"Got port {port.client_name}:{port.name}")
    if port.client_name == "sysex_recv":
        print(f"Found sysex_recv port", port)
        Client.subscribe_port(Port, port)
        break
else:
    print("Didn't find sysex_recv port")

print(f"{Test_msg=}")

Client.event_output(SysExEvent(Test_msg), port=Port)
Client.drain_output()

time.sleep(20)
