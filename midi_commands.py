# midi_commands.py

from midi_io import register_command, send_midi_event, ControlChangeEvent


class Channels:
    r'''A fixed set of channels.
    '''
    def __init__(self, *channels):
        self.channels = frozenset(channels)
    
    def __contains__(self, ch):
        return ch in self.channels

    def __iter__(self):
        return iter(self.channels)


class ControlChange:
    r'''Knows how to package a change in the value of some user_control into a midi message.

    Currently only accepts one user_control.
    '''
    event = ControlChangeEvent

    def __init__(self, port, param, channels, user_control, trace=False):
        if trace:
            print(f"ControlChange.__init__({port=}, {param=}, {channels=}, {user_control=}")
        self.port = port
        self.param = param
        self.channels = channels
        self.user_control = user_control
        user_control.midi_command = self
        self.trace = trace
        register_command(self)

    def __repr__(self):
        return f"<ControlChange port={self.port} param={self.param}>"

    def key(self):
        return self.port, self.event.type, self.param

    def local_change(self, ignore_channel=None):
        r'''Sends midi output events
        '''
        if self.trace:
            print(f"{self}.local_change: {ignore_channel=}")
        value = self.user_control.get_raw_value()

        for ch in self.channels:
            if ch != ignore_channel:
                event = self.event(ch, self.param, value)
                send_midi_event(self.port, event)

    def remote_change(self, channel, new_value):
        r'''Forwards new_value to self.user_control.

        The user_control doesn't care about channels.

        Returns True if the screen changed and needs a Screen.draw_to_framebuffer() done.
        '''
        if self.trace:
            print(f"{self}.remote_change: {channel=} {new_value=}")
        # FIX: Should any channel be able to change the user_control, or just the lowest value, or ??
        if channel in self.channels:
            # FIX: How to update other channels to match?
            if self.trace:
                print(f"{self}.remote_change: forwarding to user_control")
            return self.user_control.remote_change(channel, new_value)
        if self.trace:
            print(f"{self}.remote_change: ignored, not my channel")
        return False
