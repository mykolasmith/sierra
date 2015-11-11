from base import Animation
import math

class MotionTween(Animation):

    def __init__(self, config):
        super(MotionTween, self).__init__(config)

        self.refresh_params()
        self.trail = xrange(0, int(self.normalize(self.trail_length, 1, 60)))
        self.num_frames = self.length + len(self.trail)

        if self.duration > 0:
            self.speed = self.duration
        else:
            self.speed = 0.1

    def run(self, deltaMs):
        self.pixels[...] = 0

        if self.refresh_enabled:
            self.refresh_params()

        frame = int(round(math.sin(deltaMs / self.speed) * self.num_frames))
        if frame == self.num_frames:
            self.done = True
            return

        rgb = self.hsb_to_rgb(self.hue,self.saturation,self.brightness)
        for offset in reversed(self.trail):
            factor = 1 - (float(offset) / len(self.trail))
            px = frame-offset
            if 0 <= px < self.length:
                self.pixels[px] = rgb * factor
