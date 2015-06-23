import numpy as np

class Strip(object):
    
    def __init__(self, length):
        self.length = length
        self.pixels = np.zeros((length, 3))
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
