import numpy as np
import time

from controller import MasterController

from gevent.queue import Queue

class Strip(object):
    
    def __init__(self, length):
        # print 'Created strip %s of length %s' % (self, length)
        self.length = length
        
        # Each strip has a master frame that gets aggregated from the active animations' frame
        self.pixels = np.array([(0,0,0)] * length, dtype=np.uint8)
        
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
        
    def bind(self, *args):
        for item in args:
            if type(item) == MasterController:
                self.controllers = item

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
            
    def worker(self, now):
        for anim in self.active.itervalues():
        
            if not anim.running:
                anim.running = True
                anim.t0 = now
    
            if anim.done:
                self.expire.put(anim)
            else:
                if anim.run != anim.off:
                    anim.pixels[...] = 0
                anim.run(now - anim.t0)
                
    # For oneshots, each animation is unique and should be removed after completion
    # For holds, the note_on/note_off message determines whether the animation is active or not
    def handle_note_on(self, now):
        while not self.note_on.empty():
            task = self.note_on.get()
            
            current = self.active.get(task['msg'].note)
            if current:
                if current.trigger == 'toggle' and current.run != current.off:
                    current.t0 = now
                    current.pixels_at_inflection = current.pixels
                    current.run = current.off
                    break
                self.active.pop(task['msg'].note)
                    
            anim = task['animation'](task['strip'], self.controllers, task['msg'])
            
            if anim.trigger == 'toggle':
                self.active.update({ task['msg'].note : anim })
            elif anim.trigger == 'oneshot':
                self.active.update({ id(anim) : anim })
            elif anim.trigger == 'hold':
                self.active.update({ task['msg'].note : anim })
                
    def handle_note_off(self, now):
        while not self.note_off.empty():
            msg = self.note_off.get()
            anim = self.active.get(msg.note)
            if anim:
                if anim.trigger == 'toggle':
                    break
                
                if anim.trigger == 'hold':
                    anim.t0 = now
                    anim.pixels_at_inflection = anim.pixels
                    anim.run = anim.off
                
    def handle_expire(self):
        while not self.expire.empty():
            expire = self.expire.get()
            if expire.msg.note in self.active:
                self.active.pop(expire.msg.note)
            elif id(expire) in self.active:
                self.active.pop(id(expire))
