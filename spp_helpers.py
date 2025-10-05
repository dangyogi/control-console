# spp_helpers.py

import midi_io


Spp_text = None   # points to spp_text (dynamic_text)

def set_spp_display(spp_text):
    global Spp_text
    Spp_text = spp_text

def update_spp_display(spp):
    Spp_text.text = midi_io.get_location(spp)
    Spp_text.draw()
    return True

