# spp_helpers.py

from itertools import pairwise

import midi_io


__all__ = "calibrate_spp Spp_control get_spp_control".split()


Measure_spps = None  # [(spp, measure name, duration_spps, spp_offset), ...] -- in spp order, 0 relative
Part_duration_spps = None

def calibrate_spp(clocks_per_measure, part_duration_clocks, skips, odd_durations):
    r'''skips and odd_durations are sent in yaml format from the player when a song_select is done.

    skips is a list of (measure_number(int), measure name(str)); where measure_number starts at 1
    and increments by 1 for each measure played (counting repeated measures twice).  Measure name
    includes -R suffixes to indicate which Repeat this measure is used in.  The first element of skips
    is always the name of measure 1, generally (1, "1").

    odd_durations is a dict of {"measure name": duration_clocks} for all measures that don't have the
    standard duration for this song.

    Zeroes all spps.

    Returns True if the screen was updated.
    '''
    global Measure_spps, Part_duration_spps

    spps_per_measure = clocks_per_measure // midi_io.Clocks_per_spp

    Part_duration_spps = part_duration_clocks // midi_io.Clocks_per_spp
    if part_duration_clocks % midi_io.Clocks_per_spp:
        Part_duration_spps += 1

    def split(name):
        r'''Splits measure name into num, suffix
        '''
        if '-' in name:
            measure_num, suffix = name.split('-', 1)
            measure_num = int(measure_num)
            suffix = '-' + suffix
        else:
            measure_num = int(name)
            suffix = ''
        return measure_num, suffix

    spp = 0
    Measure_spps = []  # [(spp, measure_name, duration, spp_offset), ...] -- in spp order

    def add(measure):
        r'''Returns next spp.
        '''
        name = f"{measure}{suffix}"
        duration = odd_durations.get(name, clocks_per_measure)
        assert duration % midi_io.Clocks_per_spp == 0, \
               f"{measure=}, {duration=} not divisible by {midi_io.Clocks_per_spp} for SPP"
        duration_spps = duration // midi_io.Clocks_per_spp
        if spp + duration_spps >= Part_duration_spps or duration_spps * 2 >= spps_per_measure:
            spp_offset = 0
        else:
            spp_offset = spps_per_measure - duration_spps
        Measure_spps.append((spp, name, duration_spps, spp_offset))
        print(f"{measure=}: added ({spp=}, {name=}, {duration_spps=}, {spp_offset=})")
        return spp + duration_spps

    for (first_measure, first_name), (second_measure, second_name) in pairwise(skips):
        measure_num, suffix = split(first_name)
        print(f"({first_measure=}, {first_name=}), ({second_measure=}, {second_name=})")
        for measure in range(measure_num, measure_num + (second_measure - first_measure)):
            spp = add(measure)

    measure, suffix = split(second_name)
    print(f" final from {second_name=}, {measure=}, {suffix=}")
    while spp < Part_duration_spps:
        spp = add(measure)
        measure += 1
    print(f"calibrate_spp({clocks_per_measure=}, {part_duration_clocks=}, ...): "
          f"{Part_duration_spps=}")
    print(f"  last measure {Measure_spps[-1]}, {spp=}")
    print(f"  first measure {Measure_spps[0]}")
    screen_updated = False
    for spp in Spp_controls.values():
        if spp.set_spp(0):
            screen_updated = True
    midi_io.set_midi_spp(0)
    return screen_updated


Spp_controls = {}   # {name: Spp}

def get_spp_control(name):
    return Spp_controls[name]

class Spp_control:
    def __init__(self, name, display_text):
        global Spp_controls
        self.name = name
        assert name not in Spp_controls, f"Spp_control({name=}): duplicate name"
        Spp_controls[name] = self
        self.display_text = display_text

    def update_spp_display(self):
        self.display_text.text = self.get_location()
       #print(f"Spp_control({self.name}).update_spp_display: "
       #      f"spp={self.spp}, text={self.display_text.text}")
        self.display_text.draw()
        return True

    def capture(self, name):
        spp = get_spp_control(name)
        for attr in ("spp", "measure_index", "spp_next"):
            setattr(self, attr, getattr(spp, attr))

    def set_spp(self, spp):
        r'''Updates the screen.

        Returns True.
        '''
        # FIX: Speed up when spp changes by +1?
        # FIX: Don't update display when it doesn't change (i.e., beat doesn't change)
       #print(f"Spp_control({self.name}).set_spp({spp=})")
        self.spp = spp
        assert Measure_spps is not None, \
               f"Spp_control({self.name}).set_spp({spp=}): Measure_spps is None"

        i = spp // midi_io.Spp_per_measure
        spp_start, name, duration, spp_offset = Measure_spps[i]
        while spp_start > spp:
            i -= (spp_start - spp) // midi_io.Spp_per_measure or 1
            spp_start, name, duration, spp_offset = Measure_spps[i]
        while i < len(Measure_spps) and spp_start <= spp:
            i += (spp - spp_start) // midi_io.Spp_per_measure or 1
            if i < len(Measure_spps):
                spp_start, name, duration, spp_offset = Measure_spps[i]
        self.measure_index = i - 1
        if i >= len(Measure_spps):
            self.spp_next = Part_duration_spps
        else:
            self.spp_next = spp_start
        return self.update_spp_display()

    def inc_measure(self, num_measures):
        r'''num_measures may be negative.
        '''
        self.measure_index += num_measures
        if self.measure_index >= len(Measure_spps):
            self.measure_index = len(Measure_spps) - 1
        elif self.measure_index < 0:
            self.measure_index = 0
        self.spp, name, duration, spp_offset = Measure_spps[self.measure_index]
        self.spp_next = self.spp + duration

    def inc_beat(self):
       #print(f"Spp_control({self.name}).inc_beat: spp={self.spp}, "
       #      f"Spp_per_beat_type={midi_io.Spp_per_beat_type} "
       #      f"spp_next={self.spp_next}, measure_index={self.measure_index}")
        self.spp += midi_io.Spp_per_beat_type
        while self.spp >= self.spp_next:
            self.measure_index += 1
            if self.measure_index >= len(Measure_spps):
                self.measure_index -= 1
                self.spp -= midi_io.Spp_per_beat_type
                break
            else:
                self.spp, name, duration, spp_offset = Measure_spps[self.measure_index]
                self.spp_next = self.spp + duration
       #print(f"  {self.spp=}, {self.spp_next=}, {self.measure_index=}")

    def dec_beat(self):
       #print(f"Spp_control({self.name}).dec_beat: spp={self.spp}, "
       #      f"Spp_per_beat_type={midi_io.Spp_per_beat_type} "
       #      f"spp_next={self.spp_next}, measure_index={self.measure_index}")
        self.spp -= midi_io.Spp_per_beat_type
        if self.spp < 0:
            self.spp = 0
        while self.measure_index >= len(Measure_spps) or self.spp < Measure_spps[self.measure_index][0]:
            self.measure_index -= 1
            if self.measure_index < 0:
                self.measure_index = 0
            spp, name, duration, spp_offset = Measure_spps[self.measure_index]
            self.spp_next = spp + duration
       #print(f"  {self.spp=}, {self.spp_next=}, {self.measure_index=}")

    def get_location(self):
        if Measure_spps is None:
            return "1.1"
        if self.measure_index >= len(Measure_spps):
            return "End"
        spp_start, name, duration, spp_offset = Measure_spps[self.measure_index]
        beats_since_start = (self.spp - spp_start + spp_offset) // midi_io.Spp_per_beat_type
        return f"{name}.{beats_since_start+1}"

