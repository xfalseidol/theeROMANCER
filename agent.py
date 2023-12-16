from environment.object import RomancerObject
from loglist import Logpoint

class PerceptionFilter():
    '''Each agent should have a perception filter, which translates percepts received from the environment into the agent's internal ontology. Note that the perception filter can be dynamic and can translate percepts differently based upon the agent's current internal state. The perception filter itself can serve as a container for arbitrary state used for this translation process.'''

    def __init__(self, agent):
        self.agent = agent

        
    def digest_percept(self, percept):
        '''This method alters the agent's state based on the percept.'''
        self.agent.most_recent_percept_time = percept.time
    

class AgentLogpoint(Logpoint):
    '''Like regular environmental objects, agents need to have a class of logpoint to document their evolution through time. But in addition to documenting changes in physical state, agents' loglists can document the evolution of their _mental_ states.'''

    def __init__(self, time):
        self.time = time
        self.most_recent_percept_time = None


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


    def deliberate(self, max_time):
        '''This method causes the agent to cogitate and predict how its mental state and intentions will evolve up until max_time in the future, presuming that it receives no additional percepts after the current time. One of the purposes of this method is to establish the evolution of the internal mental state of the agent. These changes can be stored on the loglist and then used to account for how a new percept can interrupt the agent's 'chain of thought.'

        As this base Agent class has no intentions and mental state to update, this method does nothing.'''
        pass

    # add rewind method that doesn't truncate loglist
    # add fastforward or lookahead method?


class ActionROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    time: float # simulation time
    action: str
    most_recent_percept_time: float = -1.0 # negative value means 'None'
