from base import Animation
import noise
import math

class Perlin(Animation):

    def __init__(self, config):
        super(Perlin, self).__init__(config)

        self.scale = 0.01
        self.octaves = 1

        self.mmax = 0.0001
        self.mmin = 0.0001

        self.bmax = 0.0001
        self.bmin = 0.0001

        self.decay = 1.0

        self.z = 0

    def run(self, deltaMs):
        self.refresh_params()
        if deltaMs < self.attack:
            self.brightness = self.brightness * (deltaMs / self.attack)
        self.draw()

    def draw(self):
        for x in range(self.length):
            brightness = noise.pnoise2(x * self.scale, self.z * self.scale, 3)

            if brightness > self.bmax: self.bmax = brightness
            if brightness < self.bmin: self.bmin = brightness

            c = noise.pnoise3(x * self.scale, self.scale, self.z * self.scale, self.octaves )
            if c > self.mmax: self.mmax = c
            if c < self.mmin: self.mmin = c

            c = c + math.fabs(self.mmin)
            c = c / (self.mmax + math.fabs(self.mmin))

            brightness = brightness + math.fabs(self.bmin)
            brightness = brightness / (self.bmax + math.fabs(self.bmin)) + 0.2
            if brightness > 1.0: brightness = 1.0

            if self.hue_enabled:
                if self.hue > c:
                    distance = self.hue - c
                    c = c + (self.hue * distance)
                elif self.hue < c:
                    distance = c - self.hue
                    c = c - (c * distance)

            self.pixels[x] = self.hsb_to_rgb(c, self.saturation, brightness * self.brightness)

        self.z += self.normalize(self.speed, 0.01, 10.0)

    def off(self, deltaMs):
        self.refresh_params()
        if deltaMs >= self.decay:
            self.pixels[...] = 0
            self.done = True
        else:
            self.brightness = self.brightness * (1 - (deltaMs / self.decay))
            self.draw()
