from base import Animation

class Slider(Animation):
    
    def __init__(self, config):
        super(Slider, self).__init__(config, 'toggle')
        
    def run(self, deltaMs):
        self.refresh_params()
        point = int(round(self.position * self.length))
        width = int(round(self.width * self.length))
        rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
        if point < self.length:
            self.pixels[point] = rgb
        for px in xrange(1, width // 2):
            if point+px < self.length:
                self.pixels[point+px] = rgb
            if point-px >= 0:
                self.pixels[point-px] = rgb
            
    def off(self, deltaMs):
        self.done = True
        