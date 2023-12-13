from environment.object import RomancerObject

class PerceptionFilter():
    '''Each agent should have a perception filter, which translates percepts received from the environment into the agent's internal ontology. Note that the perception filter can be dynamic and can translate percepts differently based upon the agent's current internal state. The perception filter itself can serve as a container for arbitrary state used for this translation process.'''

    def __init__(self, agent):
        self.agent = agent

        
    def digest_percept(self, percept):
        '''This method alters the agent's state based on the percept.'''
        pass
    

class AgentLogpoint(logpoint):
    '''Like regular environmental objects, agents need to have a class of logpoint to document their evolution through time. But in addition to documenting changes in physical state, agents' loglists can document the evolution of their _mental_ states.'''

    def __init__(self, time):
        self.time = time


def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the agent will take. This can be an arbitrary action.'''
    pass


class Agent(RomancerObject):
    '''Agents are like other environmental objects in ROMANCER, except that they possess agency and can receive percepts from the environment. Agents do not necessarily represent individual humans. Agents can also be collective (e.g., a group of humans or a bureacracy). Agents can also be used to represent certain kinds of autonomous systems, such as the guidance set in a guided munition or robots.

    One of the key design goals of ROMANCER is to abstract agent design and implementation from the rest of the simulation. Therefore, ROMANCER tries to be agnostic about how agents work internally.'''
    
    def __init__(self, environment, time, perception_filter):
        super().__init__(environment, time)
        self.perception_filter = perception_filter
        self.dispatch_table = {'DeterministicActionsBeforeTime': next_deterministic_action, 
                               'StochasticActionsBeforeTime': lambda o, m: None,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time)}
        self.repr_list = super().repr_list + ['perception_filter']


    def perceive(self, percept):
        '''This method updates the agent's internal state based on percept.'''
        self.perception_filter.digest_percept(percept)
