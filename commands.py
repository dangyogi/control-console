# commands.py

import time

import midi_io
import traffic_cop


__all__ = "set_channel set_transpose set_tempo " \
          "ControlChange SystemCommon CannedEvent Start Stop Continue_ Cycle SongSelect " \
          "SaveSpp IncSpp Replay Loop Quit".split()


Running = False
First_start = True
Channel_touch = None
Transpose_touch = None
Tempo_touch = None

def set_channel(touch):
    global Channel_touch
    Channel_touch = touch

def set_transpose(touch):
    global Transpose_touch
    Transpose_touch = touch

def set_tempo(touch):
    global Tempo_touch
    Tempo_touch = touch

def init_player():
    print(f"init_player: {Channel_touch.value=}, {Transpose_touch.value=}, {Tempo_touch.value=}")
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x55, Channel_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x56, Transpose_touch.value))
    midi_io.send_midi_event(midi_io.SystemEvent(0xF4, Tempo_touch.value))

class Command:
    def attach_touch(self, touch):
        self.touch = touch

class ControlChange(Command):
    def __init__(self, channel, param, multiplier=1, send_msb_lsb=False):
       #print(f"ControlChange({channel=}, {param=}, {multiplier=}, {send_msb_lsb=}")
        self.channel = channel
        self.param = param
        self.multiplier = multiplier
        self.send_msb_lsb = send_msb_lsb

    def value_change(self, value):
        r'''Returns True if screen changed.
        '''
       #print(f"sending ControlChangeEvent channel={self.channel}, param={hex(self.param)}, "
       #      f"value={value * self.multiplier}")
        value *= self.multiplier
        if self.send_msb_lsb:
            midi_io.send_midi_event(
              midi_io.ControlChangeEvent(self.channel, self.param, value >> 7))
            midi_io.send_midi_event(
              midi_io.ControlChangeEvent(self.channel, self.param + 0x20, value & 0x7F))
        else:
            midi_io.send_midi_event(
              midi_io.ControlChangeEvent(self.channel, self.param, value))
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

class Start(CannedEvent):
    def __init__(self):
        super().__init__(midi_io.StartEvent())

    def act(self):
        r'''Returns True if screen changed.
        '''
        global Running, First_start
        if not Running:
            if First_start:
                init_player()
                First_start = False
            super().act()
            Running = True
            return midi_io.set_spp(0)
        return False

class Stop(CannedEvent):
    def __init__(self):
        super().__init__(midi_io.StopEvent())

    def act(self):
        r'''Returns True if screen changed.
        '''
        global Running
        if Running:
            Running = False
            midi_io.clear_end_spp()
            return super().act()
        return False

class Continue_(CannedEvent):
    def __init__(self):
        super().__init__(midi_io.ContinueEvent())

    def act(self):
        r'''Returns True if screen changed.
        '''
        global Running
        if not Running:
            Running = True
            return super().act()
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
        global Running, First_start
        #print(f"sending SongSelectEvent channel=4, song={self.songs.index}")
        midi_io.send_midi_event(midi_io.SongSelectEvent(0, self.songs.index))
        Running = False
        First_start = True
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
        global Running

        def step2():
            r'''Return True if screen changed.
            '''
            spp = self.mark_savespp.spp
            midi_io.send_midi_event(midi_io.SongPositionPointerEvent(0, spp))
            midi_io.set_spp(spp)
            if self.end_savespp.spp:
                midi_io.end_spp_fn(self.end_savespp.spp, self.end_fn)
            traffic_cop.set_alarm(0.01, step3)
            return True

        def step3():
            r'''Return True if screen changed.
            '''
            global Running
            midi_io.send_midi_event(midi_io.ContinueEvent())
            Running = True
            return False

        if Running:
            midi_io.send_midi_event(midi_io.StopEvent())
            Running = False
            traffic_cop.set_alarm(0.01, step2)
            return False
        else:
            return step2()

    def end_fn(self, spp):
        r'''Returns True if screen changed.
        '''
        midi_io.send_midi_event(midi_io.StopEvent())
        return False

class Loop(Replay):
    def end_fn(self, spp):
        r'''Returns True if screen changed.
        '''
        return self.act()

class Quit(Command):
    def act(self):
        traffic_cop.stop()

