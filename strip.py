import numpy as np

class Strip(object):
    
    def __init__(self, length):
        self.length = length
        
        # Each strip has a master frame that gets aggregated from the active animations' frame
        self.pixels = np.zeros((length, 3), dtype=np.uint8)
        
        # Keep track of the active animations
        self.active = {}

    def aggregate(self):
        # Set the strip frame
        # As the maxima of each indice
        # In each animation frame
        if self.active:
            self.pixels = np.maximum.reduce([
                anim.pixels
                for anim
                in self.active.itervalues()
            ])
