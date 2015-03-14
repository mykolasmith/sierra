import numpy as np
import gevent
import time

from gevent.queue import Queue

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.length = length
        
        # Each strip has a master frame that gets aggregated from the active animations' frame
        self.frame = np.array([(0,0,0)] * length)
        
        # Keep track of the active animations depending on their trigger type
        self.holds = {}
        self.oneshots = {}
        
        # Gevent Queue for pending task
        # Includes animation to fire on strip
        # With midi message triggered by controller
        # See "firing" event loop
        self.tasks = Queue()
        
        # Gevent Queue for pending note_off messages
        self.expire = Queue()
        
        # Pending firing / expiry events
        self.pending_events = []

    def aggregator(self):
        # Set the strip frame
        # As the maxima of each indice
        # In each animation frame
        while True:
            if self.holds or self.oneshots:
                self.frame = np.maximum.reduce(
                    [ anim.get_frame() for anim in self.oneshots.itervalues() ] +
                    [ anim.get_frame() for anim in self.holds.itervalues() ]
                )
            gevent.sleep(0)
            
    def worker(self):
        # Run the pending fire / expire events
        while True:
            if self.pending_events:
                gevent.joinall(self.pending_events)
                self.pending_events = []
            gevent.sleep(0)
            
    def firing(self):
        while True:
            while not self.tasks.empty():
                task = self.tasks.get()
                
                # If the message note is being held and we receive a note on
                # Some race condition must have happened.
                # Expire the existing hold before we trigger a new one.
                anim = self.holds.get(task['msg'].note)
                if anim:
                    anim.expire()
                    
                event = gevent.spawn(
                    task['animation'],
                    task['strip'],
                    task['controller'],
                    task['msg']
                )
                self.pending_events.append(event)
            gevent.sleep(0)

    def expiry(self):
        while True:
            while not self.expire.empty():
                expiry = self.expire.get()
                # Only holds get expired by note_off midi messages.
                anim = self.holds.get(expiry.note)
                if anim:
                    # Hold animations should subclass "off" to handle a note_off.
                    event = gevent.spawn(anim.off)
                    self.pending_events.append(event)
            gevent.sleep(0)