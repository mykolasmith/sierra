import numpy as np
import gevent

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.length = length
        self.frame = np.array([(0,0,0)] * length)
        self.active_events = { 'oneshot' : {}, 'hold' : {} }

    def aggregator(self, universe):
        self.universe = universe
        while True:
            oneshots = [ anim.frame for anim in
                self.active_events['oneshot'].itervalues() ]
            holds = [ anim.frame for anim in
                self.active_events['hold'].itervalues() ]
            
            if oneshots or holds:
                self.frame = np.maximum.reduce(oneshots + holds)
            
            gevent.sleep(1/240.)