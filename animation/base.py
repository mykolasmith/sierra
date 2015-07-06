import numpy as np
import colorsys
import math

class Animation(object):
    
    def __init__(self, config):
        self.length = config.length
        self.controllers = config.controllers
        self.msg = config.msg
        self.notes = config.notes
        self.params = config.params
        self.trigger = config.trigger
        
        # Running / done let the handler and worker know when to
        # stop animating and remove from the active animation queue.
        self.running = False
        self.done = False
        self.runner = self.run
        
        # Each animation operates on it's own frame
        # of pixel values: [[R,G,B],[R,G,B],...]
        self.pixels = np.zeros((config.length,3))
        
        self.refresh_params()
        
    def run(self, deltaMs):
        # Each animation is passed the amount of time elapsed since it began,
        # whenever the worker comes back to it in the event loop.
        # This implementation is how most physics / graphics engines do procedural animations.
        pass
        
    def off(self, deltaMs):
        # "Off" is the opposite of "run" in that off *becomes* the run function
        # when certain conditions occur for certain animation types.
        # This mimics common musical performance patterns: 
        # e.g. oneshot, hold, toggle.
        # This is useful for when you want to do something *other* than
        # immediately turn off the lights when a key is let go off or untoggled.
        pass
        
    def normalize(self, val, new_min, new_max):
        # Return a normalized decimal value for a new min and max (e.g. 0-1).
        if val == 0.0:
            return new_min
        elif val == 1.0:
            return new_max
        else:
            return float(val) * (new_max - new_min)
            
    def refresh_params(self):
        # Accepts a dictionary of devices and parameters
        # and stores their current value from the controller state
        # as an instance variable on the animation.
        params = self.controllers.params(self.msg.channel, self.params)
        for param, val in params.iteritems():
            setattr(self, param, val)
        
    def hsb_to_rgb(self, h, s, b):
        # The colorsys module returns a 0-1 value for R,G,B
        # based on different hue, saturation, or brightness values.
        # We multiply by 255 in order to get 0-255 normalized values.
        return np.array(colorsys.hsv_to_rgb(h, s, b)) * 255