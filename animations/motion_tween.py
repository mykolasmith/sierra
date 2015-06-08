from base import Animation

class MotionTween(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(MotionTween, self).__init__(length, controllers, msg, notes, 'oneshot')
        self.trail = xrange(0,20)
        self.pitch = 0
        
        if self.pitch != 0:
            self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        self.num_frames = self.length + len(self.trail)
        self.duration = 2.0
        
        self.refresh_enabled = self.controllers.get(self.msg.channel, "mpk49", 13, 0)
        self.djm_enabled = self.controllers.get(self.msg.channel, "mpk49", 13, 0)
        
        self.refresh_params()
        
    def refresh_params(self):
        self.hue = self.controllers.get(self.msg.channel, "mpk49", 12, 64)
        self.saturation = 127
        self.brightness = 127
        
    def run(self, deltaMs):
        frame = round(self.num_frames * (deltaMs / self.duration))
        if frame >= self.num_frames:
            self.done = True
            return
            
        if self.refresh_enabled:
            self.refresh_params()
        
        if self.djm_enabled:
            self.saturatiion = self.controllers.get(self.msg.channel, 'nexus', 'color', 64)
        
        rgb = self.hsb_to_rgb(self.hue,self.saturation,self.brightness)
        for offset in reversed(self.trail):
            factor = 1 - (float(offset) / len(self.trail))
            try:
                if frame - offset > 0:
                    self.pixels[frame-offset] = rgb * factor
                    self.pixels[frame - len(self.trail)] = [0,0,0]
            except IndexError:
                pass
