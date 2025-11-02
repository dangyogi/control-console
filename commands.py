# commands.py

import time

import screen
import midi_io
import traffic_cop

from spp_helpers import get_spp_control


__all__ = "set_tempo set_dynamics set_channel set_transpose set_volume " \
          "ControlChange SystemCommon CannedEvent Start Stop Continue_ SongSelect " \
          "SaveSpp IncSpp Replay Loop Quit SetScreen".split()


Running = False
First_start = True

Tempo_touch = None
Dynamics_touch = None
Channel_touch = None
Transpose_touch = None
Volume_touch = None

def set_tempo(touch):
    global Tempo_touch
    Tempo_touch = touch

def set_dynamics(touch):
    global Dynamics_touch
    Dynamics_touch = touch

def set_channel(touch):
    global Channel_touch
    Channel_touch = touch

def set_transpose(touch):
    global Transpose_touch
    Transpose_touch = touch

def set_volume(touch):
    global Volume_touch
    Volume_touch = touch

def init_player():
    print(f"init_player: {Channel_touch.value=}, {Transpose_touch.value=}, {Tempo_touch.value=}")
    midi_io.send_midi_event(midi_io.SystemEvent(0xF4, Tempo_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x57, Dynamics_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x55, Channel_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x56, Transpose_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x07, Volume_touch.value))
    midi_io.send_midi_event(midi_io.ControlChangeEvent(1, 0x27, 0))

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
        self.spp_control = None

    def act(self):
        r'''Returns True if screen changed.
        '''
        global Running, First_start
        if self.spp_control is None:
            self.spp_control = get_spp_control("spp")
        if not Running:
            if First_start:
                init_player()
                First_start = False
            super().act()
            Running = True
            return self.spp_control.set_spp(0)
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
    def __init__(self, target_control):
        self.target_control = target_control
        self.spp_control = get_spp_control("spp")

    def act(self):
        r'''Copies spp_control to self.target_control

        Returns True if screen changed.
        '''
        self.target_control.capture(self.spp_control)
        return self.target_control.update_spp_display()

class IncSpp(Command):
    def __init__(self, sign, multiplier):
        self.sign = sign  # 1 or -1
        self.multiplier = multiplier  # touch_cycle

    def args(self, mark_end):
        self.mark_end = mark_end                     # touch_cycle
        self.spps = get_spp_control("mark"), get_spp_control("end")

    def act(self):
        r'''Returns True if screen changed.
        '''
        target = self.spps[self.mark_end.index]
        multiplier = self.multiplier.choice()
        if multiplier == 0.1:
            if self.sign > 1:
                target.inc_beat()
            else:
                target.dec_beat()
        else:
            target.inc_measure(self.sign * multiplier)
        return target.update_spp_display()

class Replay(Command):
    def init(self):
        self.spp_control = get_spp_control("spp")
        self.mark_spp = get_spp_control("mark")
        self.end_spp = get_spp_control("end")

    def act(self):
        r'''Returns True if screen changed.
        '''
        global Running

        def step2():
            r'''Return True if screen changed.
            '''
            spp = self.mark_spp.spp
            midi_io.send_midi_event(midi_io.SongPositionPointerEvent(0, spp))
            screen_changed = self.spp_control.set_spp(spp)
            if self.end_spp.spp:
                midi_io.end_spp_fn(self.end_spp.spp, self.end_fn)
            traffic_cop.set_alarm(0.01, step3)
            return screen_changed

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
        return False

class SetScreen(Command):
    def __init__(self, name):
        self.name = name

    def act(self):
        screen.new_screen(self.name)
        return False
