# scale_fns.py

r'''Each scale class has a scale (exact) and a scale_rounded (for display).
'''

import math


def id(x):
    return x

class linear:
    r'''ans = m*x + b

    m = (max_y - min_y) / (max_x - min_x)
    b = min_y - m*min_x       # m*min_x + b = min_y
    '''
    # so m*max_x + b = max_y
    #    m*max_x + min_y - m*min_x = max_y
    #    m*(max_x - min_x) = max_y - min_y
    #    m = (max_y - min_y) / (max_x - min_x)

    def __init__(self, m, b):
        self.m = m
        self.b = b

        # derivative of log(m, 10) is 1/(m*ln(10)) == 1/(2.3*m), times 1/256 (0.5 in 128) == 1/(589*m)
        self.digits = max(0, int(math.ceil(-math.log(m, 10) - 1/(589*m))))  # after decimal point

        if self.digits <= 0:
            self.scale_rounded = self.scalei
        else:
            self.scale_rounded = self.scalef

    def scale(self, x):
        return self.m * x + self.b

    def scalei(self, x):
        # returns an int
        return round(self.m * x + self.b)

    def scalef(self, x):
        return round(self.m * x + self.b, self.digits)

class exponential:
    r'''ans = min*math.pow(m, x)

    m = math.pow(max_y / min_y, 1/max_x)
    '''
    # min_y*math.pow(m, max_x) = max_y
    # math.pow(m, max_x) = max_y / min_y
    # m = math.pow(max_y / min_y, 1/max_x) # raise each side by 1/max_x

    def __init__(self, m, min):
        r'''min is scaled value when x == 0.
        '''
        self.m = m
        self.min = min

        # after decimal point
        # see derivative comment on linear.
        self.digits_at_min = max(0, int(math.ceil(-math.log(min*(m-1), 10) - 1/(589*(min*(m-1))))))
        self.breakpoints = [math.ceil(math.pow(10, -d) / (m - 1))
                            for d in range(self.digits_at_min, -1, -1)] 
        assert self.breakpoints[0] < min, f"exponential({m=}, {min=}): {self.breakpoints[0]=} >= {min=}"
        del self.breakpoints[0]

    def scale(self, x):
        return self.min * math.pow(self.m, x)

    def scale_rounded(self, x):
        ans = self.min * math.pow(self.m, x)
        i = 0
        while i < len(self.breakpoints) and self.breakpoints[i] < ans:
            i += 1
        digits = self.digits_at_min - i
        if digits <= 0:
            return round(ans)
        return round(ans, digits)

class choices:
    def __init__(self, *choices):
        self.choices = choices

    def scale(self, x):
        return self.choices[x]

    scale_rounded = scale


Transpose_scale = linear(1, -12)                # high_value: 24, [-12:12] (semitones)
Channel_scale = linear(1, 1)                    # high_value: 15, [1:16]
Note_channel_scale = id                         # high_value: 16, [0:16] (0 for no change)
Duration_scale = linear(1.1969, -75)            # [-75:77] (percent change)
Grace_duration_scale = linear(1.1575, 3)        # [3:150] (1/12th of a clock)
Velocity_scale = linear(1.1811, -50)            # [-50:100] (delta, added to starting velocity)

Tempo_scale = exponential(1.01506, 30)          # [30:200] (bpm)

def data_to_time_sig(data):
    r'''Returns beats, beat_type; given the data byte in the midi message.
    '''
    return data >> 4, (data & 0xF) << 1

