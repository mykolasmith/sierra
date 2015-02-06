import numpy as np
import gevent
import time

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.length = length
        self.holds = {}
        self.oneshots = {}

    def aggregator(self):
        while True:
            t0 = time.time()
            
            try:
                self.frame = np.maximum.reduce(
                    [ anim.get_frame() for k, anim in self.oneshots.iteritems() ] +
                    [ anim.get_frame() for k, anim in self.holds.iteritems() ]
                )
            except:
                self.frame = np.array([(0,0,0)] * self.length)
            
            gevent.sleep(time.time() - t0)