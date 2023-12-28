from typing import NamedTuple
from environment.object import RomancerObject
from loglist import Logpoint

class RedRadarLogpoint(Logpoint):
    
    def __init__(self, time, on):
        self.time = time
        self.on = on # bool

        
    def __repr__(self):
        return 'RedRadarLogpoint(time={}, on={})'.format(self.time, self.on)


class ProbabilisticROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    probability: float # probability of event in anticipated occurrences per second
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    

def stochastic_actions_before_time(o, m):
    if self.on:
        messages = list()
        peers = {d.peers() for d in self.dispositions} # Use disposition tree to identify objects radar might detect (e.g., plane)
        for peer in peers:
            if peer.__class__.__name__ == 'BZero':
                initial_time = peer.time
                delta_t = 5.0 # 5 second detection interval
                times = range(o.time, m.time, delta_t)
                if not peer.ecm:
                    for t in times:
                        peer.forward_simulation(t)
                        distance = abs(peer.location - o.location)
                        detection_prob = max(0.5 - 0.002 * distance, 0.0)
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(m.sender[0], m.sender[1]), messagetype='AttemptDisplayBlip', time=t, probability=detection_prob)
                        messages.append(message)
                else:
                    for t in times:
                        peer.forward_simulation(t)
                        distance = abs(peer.location - o.location)
                        # and the probability that it will detect them during time interval
                        detection_prob = max(0.75 - 0.015 * distance, 0.0)
                        # Generate message(s) to send to supervisor about these possible events, their probabilities, and the times at which they would occur if they do
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptDisplayBlip', time=t, probability=detection_prob)
                        messages.append(message)
            peer.rewind(initial_time) # rewind bomber to previous state
    
        # Also produce message(s) representing false positives
        times = range(o.time, m.time, delta_t)
        false_blip_rate = 0.01 # stochastic blips per second
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(m.sender[0], m.sender[1]), messagetype='AttemptDisplayBlip', time=t, probability=false_blip_rate * delta_t)
            messages.append(message)
        self.send_messages(messages)
    else:
        pass # nothing happens if the radar is turned off    

    
class RedRadar(RomancerObject):

    def __init__(self, environment, time, location, on=False, granularity=1000):
        super().__init__(environment, time) # set up standard object slots
        self.children = list() # screen and red agent can be added here
        self.location = location
        self.on = on # is radar on?
        self.granularity = granularity # used for disposition tree
        # self.dispositions = [self.environment.disposition_tree.set_disposition(self, self.granularity)] # perhaps this should be part of Environment.register_object(RedRadar)?
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: None, # radar generates no autonomous deterministic actions
                               'StochasticActionsBeforeTime': stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'ActivateRadar': lambda o, m: o.activate_radar(),
                               'DeactivateRadar': lambda o, m: o.deactivate_radar()} # dict of functions for processing messages
        self.repr_list = self.repr_list + ['location', 'on', 'granularity']
        initial_logpoint = RedRadarLogpoint(time=self.time, on=self.on)
        self.loglist.append(initial_logpoint)


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the radar's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table.getattr(message.messagetype)
        except AttributeError:
            print('No dispatch set for ', message)


    def update_disposition(self):
        '''While the radar can't move, its disposition may change if its granularity is adjusted.'''
        cur = self.dispositions[0]
        self.dispositions[0] = self.environment.disposition_tree.adjust_disposition(self, self.granularity)
        if self.dispositions[0] is not cur:
            new_logpoint = RedRadarLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)


    def forward_simulation(self, time):
        super().forward_simulation(time)
        for child in self.children:
            child.forward_simulation(time)
            
            
    def rewind(self, time):
        if self.time == time:
            pass
        elif low <= time:
            self.loglist.truncate_to_time(time)
            latest = self.loglist[-1]
            self.on = latest.on
            self.forward_simulation(time)
            for child in self.children:
                child.rewind(time)
            

    def activate_radar(self):
        if not self.on:
            pass
        else:
            self.on = True
            new_logpoint = RedRadarLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)


    def deactivate_radar(self):
        if self.on:
            pass
        else:
            self.on = False
            new_logpoint = RedRadarLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)

            
class RadarScreenLogpoint(Logpoint):
    def __init__(self, time, blip_to_display):
        self.time = time
        self.blip_to_display = blip_to_display # bool

    
    def __repr__(self):
        return 'RedRadarLogpoint(time={}, blip_to_display={})'.format(self.time, self.blip_to_display)


def screen_stochastic_actions_before_time(o, m):
    if self.parent.on: # ensure radar is on before generating blips
        # Produce message(s) representing false positives irrespective of whether blip_to_display is True; these are false positives originating inside the screen as opposed to the radar
        delta_t = 10.0 # 5 second detection interval
        times = range(o.time, m.time, delta_t)
        false_blip_rate = 0.005 # stochastic blips per second            
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(m.sender[0], m.sender[1]), messagetype='AttemptDisplayBlip', time=t, probability=false_blip_rate * delta_t)
            messages.append(message)
        self.send_messages(messages)
    else:
        pass # nothing happens if the radar is turned off
    

class RadarScreen(RomancerObject):
    '''The radar screen can display blips that can turn into percepts for the red agent.'''
    def __init__(self, environment, time, location):
        super().__init__(environment, time) # set up standard object slots
        self.parent = None
        self.blip_to_display = None # used to generate percept
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: None, # screen generates no autonomous deterministic actions
                               'StochasticActionsBeforeTime': screen_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'DisplayBlip': lambda o,m: o.display_blip()}
        self.repr_list = self.repr_list + ['parent'] # should this include blip_to_display?


    @property
    def location(self):
        '''The radar screen is part of the radar, so its location is the same as that of the radar.'''
        return self.parent.location


    @property
    def granularity(self):
        '''The screen is part of the radar, so its granularity is the same as that of the radar.'''
        return self.parent.granularity
    
        
    def display_blip(self):
        self.blip_to_display = True # need to reset this after generating possible percept event
        new_logpoint = RadarScreenLogpoint(time = self.time, blip_to_display = self.blip_to_display)
        self.loglist.append(new_logpoint)
