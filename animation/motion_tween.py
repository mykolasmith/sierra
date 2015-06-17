from base import Animation

class MotionTween(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(MotionTween, self).__init__(length, controllers, msg, notes, 'oneshot')
        self.params = {
            'refresh_enabled': [
                0,
                ("ipad", "toggle1"),
                ("mpk49", 21),
            ],
            'hue': [
                0.5,
                ("ipad", "fader1"),
                ("mpk49", 2),
            ],
            'saturation' : [
                1.0,
                ("ipad", "fader2"),
                ("mpk49", 1)
            ],
            'brightness': [
                1.0, 
                ("ipad", "fader3"),
                ("mpk49", 12),
            ],
            'duration': [
                0,
                ("ipad", "rotary2"),
                ("mpk49", 3)
            ],
            'trail_length' : [
                0.5,
                ("ipad", "rotary1"),
                ("mpk49", 13)
            ]
        }
        
        self.refresh_params()
        self.duration = self.normalize(self.duration, 0.0, 1.0, 0.5, 5.)
        self.trail = xrange(0, int(self.normalize(self.trail_length, 0., 1., 1, 60)))
        
    def run(self, deltaMs):
        self.num_frames = self.length + len(self.trail)
        
        if self.refresh_enabled:
            self.refresh_params()
            self.duration = self.normalize(self.duration + 0.1, 0.1, 1.0, 0.1, 10.)
        
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
                
class BackwardMotionTween(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(BackwardMotionTween, self).__init__(length, controllers, msg, notes, 'oneshot')
        
        self.params = {
            'refresh_enabled': [
                0,
                ("ipad", "toggle1"),
                ("mpk49", 21),
            ],
            'hue': [
                0.5,
                ("ipad", "fader1"),
                ("mpk49", 2),
            ],
            'saturation' : [
                1.0,
                ("ipad", "fader2"),
                ("mpk49", 1)
            ],
            'brightness': [
                1.0, 
                ("ipad", "fader3"),
                ("mpk49", 12),
            ],
            'duration': [
                0,
                ("ipad", "rotary2"),
                ("mpk49", 3)
            ],
            'trail_length' : [
                0.5,
                ("ipad", "rotary1"),
                ("mpk49", 13)
            ]
        }
        
        self.refresh_params()
        self.duration = self.normalize(self.duration, 0.0, 1.0, 0.5, 5.)
        self.trail = xrange(0, int(self.normalize(self.trail_length, 0., 1., 1, 60)))
        
    def run(self, deltaMs):
        self.num_frames = self.length + len(self.trail)
        
        if self.refresh_enabled:
            self.refresh_params()
            self.duration = self.normalize(self.duration + 0.1, 0.1, 1.0, 0.1, 10.)
        
        frame = round(self.num_frames * (deltaMs / self.duration))
        if frame >= self.num_frames:
            self.done = True
            return
        
        rgb = self.hsb_to_rgb(self.hue,self.saturation,self.brightness)
        for offset in reversed(self.trail):
            factor = 1 - (float(offset) / len(self.trail))
            try:
                if offset - frame < 0:
                    self.pixels[offset-frame] = rgb * factor
                    self.pixels[-frame + len(self.trail)] = [0,0,0]
            except IndexError:
                pass