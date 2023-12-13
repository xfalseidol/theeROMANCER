from typing import NamedTuple
from environment.object import RomancerObject
from loglist import Logpoint

class RedRadarLogpoint(Logpoint):
    def __init__(self, time, on):
        self.time = time
        self.on = on # bool

    
    def __repr__(self):
        return 'RedRadarLogpoint(time={}, on={})'.format(self.time, self.on)

    
def stochastic_actions_before_time(o, m):
    if self.on:
        # Use disposition tree to identify objects radar might detect (e.g., plane)
        # and the probability that it will detect them during time interval
        # Generate message(s) to send to supervisor about these possible events, their probabilities, and the times at which they would occur if they do
        # Also produce message(s) representing false positives
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
        self.repr_list = super().repr_list + ['location', 'on', 'granularity']


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the radar's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        f = self.dispatch_table.get(message.messagetype)
        if f:
            return f
        else:
            raise Exception('No dispatch set for ', message)


    def update_disposition(self):
        '''While the radar can't move, its disposition may change if its granularity is adjusted.'''
        cur = self.dispositions[0]
        self.dispositions[0] = self.environment.disposition_tree.adjust_disposition(self, self.granularity)
        if self.dispositions[0] is not cur:
            new_logpoint = RedRadarLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)

            
    def rewind(self, time):
        if self.time == time:
            pass
        elif low <= time:
            self.loglist.truncate_to_time(time)
            latest = self.loglist[-1]
            self.on = latest.on
            self.forward_simulation(time)
            

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
    if self.parent.on and self.blip_to_display: # ensure radar is on before generating blips
        # Generate message(s) to send to supervisor about possible percept-generating blip event
        # Also produce message(s) representing false positives irrespective of whether blip_to_display is True
    else:
        pass # nothing happens if the radar is turned off
    

def RadarScreen(RomancerObject):
    '''The radar screen can display blips that can turn into percepts for the red agent.'''
    def __init__(self, environment, time, location):
        super().__init__(environment, time) # set up standard object slots
        self.parent = None
        self.blip_to_display = None # used to generate percept
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: None, # screen generates no autonomous deterministic actions
                               'StochasticActionsBeforeTime': screen_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time)
                               'DisplayBlip': lambda o,m: o.display_blip()}
        self.repr_list = super().repr_list + ['parent']


        
    def display_blip(self):
        self.blip_to_display = True # need to reset this after generating possible percept event
        new_logpoint = RadarScreenLogpoint(time = self.time, blip_to_display = self.blip_to_display)
        self.loglist.append(new_logpoint)
