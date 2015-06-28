from base import Animation

class MotionTween(Animation):
    
    def __init__(self, length, controllers, msg, notes, params):
        super(MotionTween, self).__init__(length, controllers, msg, notes, params, 'oneshot')
        
        self.refresh_params()
        
        # Based on OSC values from 0-1, normalize them to a duration from 1/2 to 5 seconds.
        self.duration = self.normalize(self.duration, 0.5, 5.)
        
        # The trail is the length of the motion tween,
        # again normalized from a length of 1-60 LEDs long.
        self.trail = xrange(0, int(self.normalize(self.trail_length, 1, 60)))
        
    def run(self, deltaMs):
        self.num_frames = self.length + len(self.trail)
        
        if self.refresh_enabled:
            self.refresh_params()
            self.duration = self.normalize(self.duration + 0.1, 0.1, 10.)
        
        frame = round(self.num_frames * (deltaMs / self.duration))
        if frame >= self.num_frames:
            self.done = True
            return
        
        rgb = self.hsb_to_rgb(self.hue,self.saturation,self.brightness)
        for offset in reversed(self.trail):
            factor = 1 - (float(offset) / len(self.trail))
            try:
                if frame - offset > 0:
                    self.pixels[frame-offset] = rgb * factor
                    self.pixels[frame - len(self.trail)] = [0,0,0]
            except IndexError:
                pass