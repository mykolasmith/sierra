import numpy as np
import time

from gevent.queue import Queue

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.length = length
        
        # Each strip has a master frame that gets aggregated from the active animations' frame
        self.frame = np.array([(0,0,0)] * length)
        
        # Keep track of the active animations
        self.active = {}
        
        # Gevent Queue for pending task
        # Includes animation to fire on strip
        # With midi message triggered by controller
        # See "firing" event loop
        self.note_on = Queue()
        self.note_off = Queue()
        
        # Gevent Queue for pending note_off messages
        self.expire = Queue()

    def aggregate(self):
        # Set the strip frame
        # As the maxima of each indice
        # In each animation frame
        if self.active:
            self.frame = np.maximum.reduce(
                [ anim.get_frame() for anim in self.active.itervalues() ]
            )
            
    def worker(self, now):
        for anim in self.active.itervalues():
            if not anim.running:
                anim.running = True
                anim.t0 = now
            if not anim.done:
                anim.frame = anim.run(now - anim.t0, np.zeros_like(anim.frame))
            else:
                self.expire.put(anim)

    def handle_note_on(self):
        while not self.note_on.empty():
            task = self.note_on.get()
            anim = task['animation'](task['strip'], task['controller'], task['msg'])
            
            if anim.trigger == 'oneshot':
            # For oneshots, each animation is unique and show be removed after the whole thing has completed
                anim.strip.active.update({ id(anim) : anim })
                
            if anim.trigger == 'hold':
            # For holds, the note_on/note_off message determines whether the animation is active or not
                anim.strip.active.update({ anim.msg.note : anim })
                
    def handle_note_off(self):
        while not self.note_off.empty():
            msg = self.note_off.get()
            anim = self.active.get(msg.note)
            if msg.note in self.active:
                anim.frame = np.zeros_like(anim.frame)
                anim.done = True
                
    def handle_expire(self):
        while not self.expire.empty():
            expire = self.expire.get()
            if expire.msg.note in self.active:
                self.active.pop(expire.msg.note)
            if id(expire) in self.active:
                self.active.pop(id(expire))
