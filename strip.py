import numpy as np
import gevent
import time

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.frame = np.array([(0,0,0)] * length)
        self.length = length
        self.holds = {}
        self.oneshots = {}

    def aggregator(self):
        while True:
            t0 = time.time()
            
            if self.holds or self.oneshots:
                self.frame = np.maximum.reduce(
                    [ anim.get_frame() for anim in self.oneshots.itervalues() ] +
                    [ anim.get_frame() for anim in self.holds.itervalues() ]
                )
            
            gevent.sleep(time.time() - t0)