from gevent.queue import Queue

class Handler(object):
    
    def __init__(self, strips, controllers):
        self.strips = strips
        self.controllers = controllers
        self.note_on = Queue()
        self.note_off = Queue()
        self.expire = Queue()
        
        self.active = {}
        
    def print_active(self):
        print self.active
        
    def worker(self, now):
        for group in self.active.itervalues():
            for anim in group.itervalues():
                
                if not anim.running:
                    anim.running = True
                    anim.t0 = now
    
                if anim.done:
                    self.expire.put(anim)
                else:
                    if anim.run != anim.off:
                        anim.pixels[...] = 0
                    anim.run(now - anim.t0)
        
    def handle_note_on(self, now):
        while not self.note_on.empty():
            task = self.note_on.get()
            current = self.active.get(task['msg'].note)
            
            if current:
                for anim in current.itervalues():
                    if anim.trigger == 'toggle':
                        if anim.run != anim.off:
                            anim.t0 = now
                            anim.pixels_at_inflection = anim.pixels
                            anim.run = anim.off
                            break
                        else:
                            self.active.pop(anim.msg.note)
                            [
                                strip.active.pop(anim.msg.note)
                                for strip in task['strips']
                                if strip.length == anim.length
                            ]
                    
            lengths = set( strip.length for strip in task['strips'])
            
            for length in lengths:
                anim = task['animation'](length, self.controllers, task['msg'])
                if anim.trigger == 'toggle':
                    if anim.msg.note in self.active:
                        break
                    else:
                        self.active.update({ anim.msg.note : {length : anim} })
                        [
                            strip.active.update({ anim.msg.note : anim})
                            for strip in task['strips']
                            if strip.length == anim.length
                        ]
                elif anim.trigger == 'oneshot':
                    self.active.update({ id(anim) : {length: anim } })
                    [
                        strip.active.update({ id(anim) : anim})
                        for strip in task['strips']
                        if strip.length == anim.length
                    ]
                elif anim.trigger == 'hold':
                    self.active.update({ anim.msg.note : {length : anim} })
                    [
                        strip.active.update({ anim.msg.note : anim})
                        for strip in task['strips']
                        if strip.length == anim.length
                    ]
            
    def handle_note_off(self, now):
        while not self.note_off.empty():
            msg = self.note_off.get()
            current = self.active.get(msg.note)
            if current:
                for anim in current.itervalues():
                    
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
                group = self.active.pop(expire.msg.note)
                for anim in group.itervalues():
                    for strip in self.strips:
                        if anim.length == strip.length:
                            strip.active.pop(expire.msg.note)
            elif id(expire) in self.active:
                group = self.active.pop(id(expire))
                for anim in group.itervalues():
                    for strip in self.strips:
                        if anim.length == strip.length:
                            strip.active.pop(id(expire))