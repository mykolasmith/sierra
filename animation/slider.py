from base import Animation

class Slider(Animation):
    
    def __init__(self, config):
        super(Slider, self).__init__(config)
        
    def run(self, deltaMs):
        self.refresh_params()
        if deltaMs < self.attack:
            self.brightness = deltaMs / self.attack
        self.draw()
            
    def draw(self):
        midpoint = 64 / 127.
        if self.saturation > midpoint:
            saturation = 1 - ((self.saturation - midpoint) / 0.5)
        elif self.saturation < midpoint:
            saturation = self.saturation / 0.5
        elif self.saturation == midpoint:
            saturation = self.saturation
        
        point = int(round(self.position * self.length))
        width = int(round(self.width * self.length))
        rgb = self.hsb_to_rgb(self.hue, saturation, self.brightness)
        if point < self.length:
            self.pixels[point] = rgb
        for px in xrange(1, width // 2):
            factor = 1 - (px / (width // 2.))
            if point+px < self.length:
                self.pixels[point+px] = rgb * factor
            if point-px >= 0:
                self.pixels[point-px] = rgb * factor
            
    def off(self, deltaMs):
        if deltaMs >= self.decay:
            self.pixels[...] = 0
            self.done = True
        else:
            self.refresh_params()
            self.brightness = 1 - (deltaMs / self.decay)
            self.draw()