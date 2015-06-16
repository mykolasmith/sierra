    strips = (
        # STAGE 1, Receiver 1
        Strip(300), Strip(1), Strip(1), Strip(1),
        # Stage 1, Receiver 2
        Strip(300), Strip(300), Strip(300), Strip(1),
        # Stage 1, Receiver 3
        Strip(300), Strip(300), Strip(1), Strip(1),
        ###
        # Stage 2, Receiver 1
        Strip(300), Strip(300), Strip(1), Strip(1),
        # Stage 2, Receiver 2
        Strip(300), Strip(300), Strip(300), Strip(1),
        # Stage 2, Receiver 3
        Strip(300), Strip(1), Strip(1), Strip(1),
    )
    
    GOAL1 = [
        strips[0],
        strips[4],
        strips[5]
    ]
    
    GOAL2 = [
        strips[6],
        strips[8],
        strips[9],
    ]
    
    GOAL3 = [
        strips[12],
        strips[13],
        strips[16]
    ]
    
    GOAL4 = [
        strips[17],
        strips[18],
        strips[20]
    ]
 
    ALL_GOALS = GOAL1 + GOAL2 + GOAL3 + GOAL4
    
     # DRUM PADS
    
    mpk49.add_trigger(
        [45],
        channel=1,
        animation=MotionTween,
        strips=GOAL2)
        
    mpk49.add_trigger(
        [42],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL2)
    
    mpk49.add_trigger(
        [39],
        channel=1,
        animation=MotionTween,
        strips=GOAL1)

    mpk49.add_trigger(
        [36],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL1)
        
    mpk49.add_trigger(
        [47],
        channel=1,
        animation=MotionTween,
        strips=GOAL3)
        
    mpk49.add_trigger(
        [44],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL3)
        
    mpk49.add_trigger(
        [41],
        channel=1,
        animation=MotionTween,
        strips=GOAL4)
        
    mpk49.add_trigger(
        [38],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL4)
        
    mpk49.add_trigger(
        [46],
        channel=1,
        animation=MotionTween,
        strips=ALL_GOALS)
        
    mpk49.add_trigger(
        [43],
        channel=1,
        animation=BackwardMotionTween,
        strips=ALL_GOALS)
        
    # KEYS
    
    mpk49.add_trigger(
        [53],
        channel=1,
        animation=Perlin,
        strips=ALL_GOALS,
    )
    
    mpk49.add_trigger(
        xrange(60,76),
        channel=1,
        animation=Positional,
        strips=ALL_GOALS,
    )
    
    # MISC
    
    mpk49.add_trigger(
        [84],
        channel=1,
        animation=ClearOSC,
        strips=[strips[0]])
    
    # touchOSC
    
    osc.add_trigger(
        '/multipush1/1/16',
        channel=1,
        animation=Positional,
        strips=ALL_GOALS
    )
    
    osc.add_trigger(
        '/multipush2/16/1',
        channel=1,
        animation=Positional,
        strips=GOAL1 + GOAL2)
    
    osc.add_trigger(
        '/multipush3/16/1',
        channel=1,
        animation=Positional,
        strips=GOAL3 + GOAL4)

    osc.add_trigger(
        '/push1',
        channel=1,
        animation=ClearOSC,
        strips=[strips[0]])
        
    osc.add_trigger(
        '/multipush3/1/16',
        channel=1,
        animation=Positional,
        strips=GOAL3 + GOAL4)
        
    osc.add_trigger(
        '/push1',
        channel=2,
        animation=MotionTween,
        strips=GOAL1)
        
    osc.add_trigger(
        '/push2',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL1)
        
    osc.add_trigger(
        '/push3',
        channel=2,
        animation=MotionTween,
        strips=GOAL2)
        
    osc.add_trigger(
        '/push4',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL2)
    
    osc.add_trigger(
        '/push5',
        channel=2,
        animation=MotionTween,
        strips=GOAL3)
        
    osc.add_trigger(
        '/push6',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL3)
        
    osc.add_trigger(
        '/push7',
        channel=2,
        animation=MotionTween,
        strips=GOAL4)
        
    osc.add_trigger(
        '/push8',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL4)
        
    osc.add_trigger(
        "/push10",
        channel=2,
        animation=Perlin,
        strips=ALL_GOALS
    )
    
    osc.add_trigger(
        '/push9',
        channel=2,
        animation=ClearOSC,
        strips=[strips[0]])
        
    osc.add_trigger(
        '/push11',
        channel=2,
        animation=MotionTween,
        strips=ALL_GOALS)
        
    osc.add_trigger(
        '/push12',
        channel=2,
        animation=BackwardMotionTween,
        strips=ALL_GOALS)