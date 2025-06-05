# rtmidi_test.py

import time

import rtmidi


midiout = rtmidi.MidiOut()
print(f"{dir(midiout)=}")
available_ports = midiout.get_ports()
print(f"{available_ports=}")

for i, name in enumerate(available_ports):
    if name.startswith('Net Client:Network '):
        print("found", name, "at", i)
        midiout.open_port(i)
        break
else:
    print("didn't find Net Client:Network, opening virtual port")
    midiout.open_virtual_port("My virtual output")

with midiout:
    for ch in range(16):
        print("channel", ch)
        for note in range(60, 73):
            note_on = [0x90 + ch, note, 112]   # channel 1, middle C, velocity 112
            note_off = [0x80 + ch, note, 0]
            midiout.send_message(note_on)
            time.sleep(0.1)
            midiout.send_message(note_off)
            time.sleep(0.1)

del midiout
