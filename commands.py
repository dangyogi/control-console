# commands.py

import time

import midi_io


__all__ = "ControlChange SystemCommon CannedEvent Cycle SongSelect SaveSpp IncSpp Replay Loop".split()


class Command:
    def attach_touch(self, touch):
        self.touch = touch

class ControlChange(Command):
    def __init__(self, channel, param, multiplier=1):
        self.channel = channel
        self.param = param
        self.multiplier = multiplier

    def value_change(self, value):
        r'''Returns True if screen changed.
        '''
        #print(f"sending ControlChangeEvent channel={self.channel}, param={hex(self.param)}, "
        #      f"value={value * self.multiplier}")
        midi_io.send_midi_event(
          midi_io.ControlChangeEvent(self.channel, self.param, value * self.multiplier))
        return False

class SystemCommon(Command):
    def __init__(self, status):
        self.status = status

    def value_change(self, value):
        r'''Returns True if screen changed.
        '''
        #print(f"sending SystemEvent event={hex(self.status)}, result={hex(value)}")
        midi_io.send_midi_event(midi_io.SystemEvent(self.status, value))
        return False

class CannedEvent(Command):
    def __init__(self, event):
        self.event = event

    def act(self):
        r'''Returns True if screen changed.
        '''
        #print("sending", self.event)
        midi_io.send_midi_event(self.event)
        return False

class Cycle(Command):
    def __init__(self, choices):
        self.choices = choices
        self.index = 0

    def attach_touch(self, touch):
        super().attach_touch(touch)
        self.widget = touch.widget.label

    def act(self):
        r'''Called before turning on the button.

        Returns True if screen changed.
        '''
        self.index = (self.index + 1) % len(self.choices)
        self.widget.text = str(self.choices[self.index])
        return False  # haven't updated the screen ... yet ...

    def choice(self):
        return self.choices[self.index]

class SongSelect(Command):
    def __init__(self, songs):
        self.songs = songs

    def act(self):
        r'''Returns True if screen changed.
        '''
        #print(f"sending SongSelectEvent channel=4, song={self.songs.index}")
        midi_io.send_midi_event(midi_io.SongSelectEvent(0, self.songs.index))
        return False

class SaveSpp(Command):
    def __init__(self, display, multiplier):
        self.display = display        # dynamic_text
        self.multiplier = multiplier  # Cycle command
        self.spp = 0

    def act(self):
        r'''Returns True if screen changed.
        '''
        self.spp = midi_io.get_spp()
        return self.update_display()

    def update_display(self):
        r'''Returns True if screen changed.
        '''
        self.display.draw(text=midi_io.get_location(self.spp))
        return True

    def inc(self, sign):
        r'''Returns True if screen changed.
        '''
        self.spp += sign * self.inc_amount()
        return self.update_display()

    def inc_amount(self):
        multiplier = self.multiplier.choice()
        if multiplier == 0.1:
            return midi_io.Spp_per_beat_type
        return multiplier * midi_io.Spp_per_measure

class IncSpp(Command):
    def __init__(self, sign):
        self.sign = sign  # 1 or -1

    def args(self, mark_end, mark_savespp, end_savespp):
        self.mark_end = mark_end                     # Cycle command
        self.savespps = (mark_savespp, end_savespp)  # SaveSpp commands

    def act(self):
        r'''Returns True if screen changed.
        '''
        return self.savespps[self.mark_end.index].inc(self.sign)

class Replay(Command):
    def args(self, mark_savespp, end_savespp):
        self.mark_savespp = mark_savespp
        self.end_savespp = end_savespp

    def act(self):
        r'''Returns True if screen changed.
        '''
        midi_io.send_midi_event(midi_io.StopEvent())
        time.sleep(0.01)
        spp = self.mark_savespp.spp
        midi_io.send_midi_event(midi_io.SongPositionPointerEvent(0, spp))
        midi_io.set_spp(spp)
        if self.end_savespp.spp:
            midi_io.end_spp_fn(self.end_savespp.spp, self.end_fn)
        time.sleep(0.01)
        midi_io.send_midi_event(midi_io.ContinueEvent())
        return True

    def end_fn(self, spp):
        midi_io.send_midi_event(midi_io.StopEvent())
        return False

class Loop(Replay):
    def end_fn(self, spp):
        return self.act()

