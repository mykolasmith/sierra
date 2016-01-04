from base import Animation

import math

class Positional(Animation):

    def __init__(self, config):
        super(Positional, self).__init__(config)
        self.brightness = 1.0
        # Look at the range of notes assigned to this animations
        # In order to determine the min and max
        self.min = min(self.notes)
        self.max = max(self.notes)

        # The min and max can then be used to deterine the correct
        # position for a set of LEDs, depending on the note pressed.

        self.width = round((1. / (self.max - self.min)) * self.length)
        self.start = (self.msg.note - self.min) * self.width
        self.end = self.start + self.width
        self.midpoint = self.start + (self.width // 2)

    def run(self, deltaMs):
        width = self.find_width(deltaMs)
        if width == 1.0 or self.oscillation == 0.0:
            self.refresh_params()

        if deltaMs < self.attack:
            self.brightness = deltaMs / self.attack
        else:
            self.brightness = 1.0

        self.draw(width)

    def find_width(self, deltaMs):
        if self.oscillation != 0:
            oscillation = self.normalize(self.oscillation, 0, 10)
            return 30 * round(self.width * abs(math.sin(deltaMs * oscillation)))
        return self.width

    def draw(self, width):
        try:
            rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
            self.pixels[self.midpoint] = rgb * 0.9 * self.master
            for px in reversed(xrange(1, int(round(width // 2)))):
                factor = 1- (px / (width // 2))
                self.pixels[self.midpoint+px] = rgb * factor * self.master
                if self.midpoint-px >= 0:
                    self.pixels[self.midpoint-px] = rgb * factor * self.master
        except IndexError:
            pass

    def off(self, deltaMs):
        width = self.find_width(deltaMs)
        if deltaMs < self.decay:
            self.brightness = 1 - (deltaMs / self.decay)
        else:
            self.brightness = 0.0
        self.draw(width)
