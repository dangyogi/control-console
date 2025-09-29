# commands.py

import midi_io


__all__ = "ControlChange CannedEvent Cycle SaveSpp".split()


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
        midi_io.send_midi_event(midi_io.ControlChangeEvent(self.channel, self.param, value * self.multiplier))
        return False

class SystemCommon(Command):
    def __init__(self, status):
        self.status = status

    def value_change(self, value):
        r'''Returns True if screen changed.
        '''
        midi_io.send_midi_event(midi_io.SystemEvent(self.status, value))
        return False

class CannedEvent(Command):
    def __init__(self, event):
        self.event = event

    def act(self):
        r'''Returns True if screen changed.
        '''
        midi_io.send_midi_event(self.event)
        return False

class Cycle(Command):
    def __init__(self):
        self.index = 0

    def attach_touch(self, touch):
        super().attach_touch(touch)
        self.widget = touch.widget
        print(f"Cycle.attach_touch: {self.widget.name=}")
        self.choices = self.widget.choices
        print(f"Cycle.act: {self.choices=}")

    def act(self):
        r'''Called before turning on the button.
        '''
        self.index = (self.index + 1) % len(self.choices)
        self.widget.text = str(self.choices(self.index))
        return False  # haven't updated the screen ... yet ...

    def choice(self):
        return self.choices[self.index]

class SaveSpp(Command):
    def __init__(self, display, multiplier):
        self.display = display        # dynamic_text
        self.multiplier = multiplier  # Cycle command
        self.spp = 0

    def act(self):
        r'''Returns True if screen changed.
        '''
        self.spp = midi_io.get_spp()
        return update_display()

    def update_display(self):
        self.display.draw(text=midi_io.get_location(self.spp))
        return True

    def inc(self, sign):
        self.spp += sign * self.inc_amount()
        return update_display()

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
        return self.savespps[self.mark_end.index].inc(self.sign)

class Replay(Command):
    def args(self, mark_savespp, end_savespp):
        self.mark_savespp = mark_savespp
        self.end_savespp = end_savespp

    def act(self):
        # FIX: implement
        print(f"Replay.act() called -- ignored for now...")

class Loop(Replay):
    def act(self):
        # FIX: implement
        print(f"Loop.act() called -- ignored for now...")

