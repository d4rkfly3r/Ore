import random
from collections import namedtuple


# Colour generation sponsored by https://github.com/davidmerfield/randomColor/blob/master/randomColor.js
# randomColor, for all your random colour needs

class Colour(namedtuple('Colour', ['name', 'hue_range', 'lower_bounds'])):

    @property
    def saturation_range(self):
        return self.lower_bounds[0][0], self.lower_bounds[len(self.lower_bounds)-1][0]

    @property
    def brightness_range(self):
        return self.lower_bounds[0][1], self.lower_bounds[len(self.lower_bounds)-1][1]


class ColourDictionary(dict):

    def register(self, colour):
        self[colour.name] = colour


def build_default_dictionary():
    d = ColourDictionary()

    d.register(Colour(
        'monochrome',
        None,
        [[0, 0], [100, 0]]
    ))

    d.register(Colour(
        'red',
        [-26, 18],
        [[20, 100], [30, 92], [40, 89], [50, 85], [60, 78],
            [70, 70], [80, 60], [90, 55], [100, 50]]
    ))

    d.register(Colour(
        'orange',
        [19, 46],
        [[20, 100], [30, 93], [40, 88], [50, 86],
            [60, 85], [70, 70], [100, 70]]
    ))

    d.register(Colour(
        'yellow',
        [47, 62],
        [[25, 100], [40, 94], [50, 89], [60, 86],
            [70, 84], [80, 82], [90, 80], [100, 75]]
    ))

    d.register(Colour(
        'green',
        [63, 178],
        [[30, 100], [40, 90], [50, 85], [60, 81],
            [70, 74], [80, 64], [90, 50], [100, 40]]
    ))

    d.register(Colour(
        'blue',
        [179, 257],
        [[20, 100], [30, 86], [40, 80], [50, 74], [60, 60],
            [70, 52], [80, 44], [90, 39], [100, 35]]
    ))

    d.register(Colour(
        'purple',
        [258, 282],
        [[20, 100], [30, 87], [40, 79], [50, 70], [60, 65],
            [70, 59], [80, 52], [90, 45], [100, 42]]
    ))

    d.register(Colour(
        'pink',
        [283, 334],
        [[20, 100], [30, 90], [40, 86], [60, 84],
            [80, 80], [90, 75], [100, 73]]
    ))

    return d


class ColourGenerator:

    COLOUR_DICTIONARY = build_default_dictionary()

    def generate(self):
        h = self.pick_hue()
        s = self.pick_saturation(h)
        b = self.pick_brightness(h, s)
        return self.change_format([h, s, b], 'rgbhex')

    def hue_range(self):
        return [0, 360]

    def saturation_range(self, h):
        return self.colour_info(h).saturation_range

    def brightness_range(self, h, s):
        return [self.minimum_brightness(h, s), 100]

    def minimum_brightness(self, h, s):
        r = self.colour_info(h).lower_bounds
        for n in range(len(r)-1):
            s1, v1 = r[n]
            s2, v2 = r[n+1]

            if s1 <= s <= s2:
                m = (v2 - v1)/(s2 - s1)
                b = v1 - m*s1

                return int(m*s + b)

        return 0

    def colour_info(self, h):
        if 334 <= h <= 360:
            h -= 360

        for colour in self.COLOUR_DICTIONARY.values():
            if colour.hue_range and colour.hue_range[0] <= colour.hue_range[1]:
                return colour

        raise Exception('No such colour')

    def pick_hue(self):
        return random.randint(*self.hue_range())

    def pick_saturation(self, h):
        return random.randint(*self.saturation_range(h))

    def pick_brightness(self, h, s):
        return random.randint(*self.brightness_range(h, s))

    def _hsb_to_rgb(self, h, s, v):
        h = min(max(1, h), 359)

        h = h/360
        s = s/100
        v = v/100

        from math import floor
        h_i = floor(h*6)
        f = h*6 - h_i
        p = v*(1-s)
        q = v*(1-f*s)
        t = v*(1-(1-f)*s)
        r = 256
        g = 256
        b = 256

        if h_i == 0:
            r = v; g = t; b = p
        elif h_i == 1: 
            r = q; g = v; b = p
        elif h_i == 2:
            r = p; g = v; b = t
        elif h_i == 3:
            r = p; g = q; b = v
        elif h_i == 4:
            r = t; g = p; b = v
        elif h_i == 5:
            r = v; g = p; b = q

        return floor(r * 255), floor(g * 255), floor(b * 255)

    def _arrhex(self, *comps):
        out = '#'
        for comp in comps:
            out += '%.2x' % (comp,)
        return out

    def change_format(self, hsb, to_format):
        formats = {
            'hsb': lambda h, s, b: [h, s, b],
            'rgb': self._hsb_to_rgb,
            'rgbhex': lambda h, s, b: self._arrhex(*self._hsb_to_rgb(h, s, b)),
        }
        return formats[to_format](*hsb)