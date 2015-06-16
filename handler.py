from gevent.queue import Queue
from message import OSCMetaMessage

class Handler(object):
    
    def __init__(self, strips, controllers):
        self.strips = strips
        self.controllers = controllers
        
        self.on = Queue()
        self.off = Queue()
        self.expiry = Queue()
        
        self.active = {}
        
    def worker(self, now):
        for group in self.active.itervalues():
            for anim in group.itervalues():
                
                if not anim.running:
                    anim.running = True
                    anim.t0 = now
    
                if anim.done:
                    self.expiry.put(anim)
                else:
                    if anim.run != anim.off:
                        anim.pixels[...] = 0
                    anim.run(now - anim.t0)
        
    def note_on(self, now):
        while not self.on.empty():
            task = self.on.get()
            
            if isinstance(task['msg'], OSCMetaMessage):
                identifier = task['msg'].pattern
            else:
                identifier = task['msg'].note
                
            current = self.active.get(identifier)
            if current:
                for anim in current.itervalues():
                    if anim.trigger == 'toggle':
                        if anim.run != anim.off:
                            anim.t0 = now
                            anim.pixels_at_inflection = anim.pixels
                            anim.run = anim.off
                            break
                        else:
                            self.end_animation(identifier, anim, task['strips'])
                 
            lengths = set( strip.length for strip in task['strips'])
            for length in lengths:
                anim = task['animation'](length, self.controllers, task['msg'], task['notes'])
                
                if isinstance(task['msg'], OSCMetaMessage):
                    identifier = anim.msg.pattern
                else:
                    identifier = anim.msg.note
                    
                if anim.trigger == 'toggle':
                    if identifier in self.active:
                        break
                    else:
                        self.begin_animation(identifier, anim, length, task['strips'])
                
                elif anim.trigger == 'hold':
                    self.begin_animation(identifier, anim, length, task['strips'])

                elif anim.trigger == 'oneshot':
                    identifier = id(anim)
                    self.begin_animation(identifier, anim, length, task['strips'])
                
    def begin_animation(self, identifier, anim, length, strips):
        for strip in strips:
            if strip.length == anim.length:
                strip.active.update({ identifier: anim })
        self.active.update({ identifier : {length : anim} })
        
    def end_animation(self, identifier, anim, strips):
        for strip in strips:
            if identifier in strip.active:
                if strip.length == anim.length:
                    strip.active.pop(identifier)
        self.active.pop(identifier)

    def note_off(self, now):
        while not self.off.empty():
            msg = self.off.get()
            
            if isinstance(msg, OSCMetaMessage):
                identifier = msg.pattern
            else:
                identifier = msg.note
                
            current = self.active.get(identifier) 
            if current:
                for anim in current.itervalues():
                    
                    if anim.trigger == 'toggle':
                        break
                
                    if anim.trigger == 'hold':
                        anim.t0 = now
                        anim.pixels_at_inflection = anim.pixels
                        anim.run = anim.off
                    
                
    def expire(self):
        while not self.expiry.empty():
            expire = self.expiry.get()
            
            if isinstance(expire.msg, OSCMetaMessage):
                identifier = expire.msg.pattern
            else:
                identifier = expire.msg.note
                
            if identifier in self.active:
                self.end_animation(identifier, expire, self.strips)
            elif id(expire) in self.active:
                self.end_animation(id(expire), expire, self.strips)