from Queue import Queue

class AnimationConfig(object):
    
    def __init__(self, length, controllers, msg, notes, params):
        self.length = length
        self.controllers = controllers
        self.msg = msg
        self.notes = notes
        self.params = params

class Handler(object):
    
    def __init__(self, strips, controllers):
        self.strips = strips
        self.controllers = controllers
        
        # Note on MIDI messages waiting to be attached to an animaton
        self.on = Queue()
        
        # Note off MIDI messages waiting to schedule expiry
        self.off = Queue()
        
        # Messages for which we will remove the corresponding animation
        # from the active animations dictionary.
        self.expiry = Queue()
        
        # A map of strip lengths to animation identifiers.
        # So that we are only doing work on a single animation,
        # regardless of if that animation appears on many strips.
        self.active = {}
        
        # Expose the handler to the controllers
        for controller in controllers.itervalues():
            controller.handler = self
        
    def worker(self, now):
        for group in self.active.itervalues():
            for anim in group.itervalues():
                
                if not anim.running:
                    anim.running = True
                    anim.t0 = now
    
                if anim.done:
                    self.expiry.put(anim)
                else:
                    anim.runner(now - anim.t0)
        
    def note_on(self, now):
        while not self.on.empty():
            task = self.on.get()
            identifier = task['msg'].note
            current = self.active.get(identifier)
            
            if current:
                # If the MIDI message note refers to an animation that is already active,
                # then we know that it is either a 'hold' or 'toggle'
                # (oneshots have a unique ID)
                for anim in current.itervalues():
                    # If a toggle exists for this note, and send another note_on
                    # then it's time to turn this animation off
                    if anim.trigger == 'toggle':
                        if anim.runner != anim.off:
                            anim.t0 = now
                            anim.pixels_at_inflection = anim.pixels
                            anim.runner = anim.off
                            break
                        else:
                            self.end_animation(identifier, anim, task['strips'])
                 
            # This is where we schedule the animation depending on the unique
            # strip lengths for which we wish to trigger this animation
            # task['animation'] = Animation class (e.g. MotionTween)
            # which gets called with the strip length, master controller, MIDI message,
            # and range of notes associated with the animation.
            lengths = set( strip.length for strip in task['strips'])
            for length in lengths:
                config = AnimationConfig(length, self.controllers, task['msg'], task['notes'], task['params'])
                anim = task['animation'](config)

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
            if strip.length == anim.length:
                if identifier in strip.active:
                    strip.active.pop(identifier)
        self.active.pop(identifier)

    def note_off(self, now):
        while not self.off.empty():
            msg = self.off.get()
            current = self.active.get(msg.note) 
            
            if current:
                for anim in current.itervalues():
                    
                    if anim.trigger == 'toggle':
                        break
                
                    if anim.trigger == 'hold':
                        anim.t0 = now
                        anim.pixels_at_inflection = anim.pixels
                        anim.runner = anim.off
                    
                
    def expire(self):
        while not self.expiry.empty():
            expire = self.expiry.get()
            if expire.trigger in ('hold', 'toggle'):
                identifier = expire.msg.note
            else:
                identifier = id(expire)
    
            self.end_animation(identifier, expire, self.strips)