from typing import NamedTuple
from romancer.environment.perceptionengine import PerceptionEngine
from romancer.environment.percept import Percept
from romancer.agent.agent import PerceptionFilter
from numpy import inf
from functools import reduce
from operator import add


class PublicMessage(NamedTuple):
    contents: tuple


class PrivateMessage(NamedTuple):
    contents: tuple
    recipient: int # uid of recipient agent


class HotlineActionROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message, presumed to have taken action
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    action_id: int # unique id representing action
    amygdala_params: dict = {'delta_pbf': 0.0, 'delta_fight': 0.0, 'delta_flight': 0.0, 'delta_freeze': 0.0}
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    target_uid: int = 0 # target object if needed, 0 means 'none'


class HotlinePublicROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message, presumed to have taken action
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    submessage: tuple # e.g., a DeterrentThreat
    amygdala_params: dict = {'delta_pbf': 0.0, 'delta_fight': 0.0, 'delta_flight': 0.0, 'delta_freeze': 0.0}
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    target_uid: int = 0 # target object if needed, 0 means 'none'


class HotlinePrivateROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message, presumed to have taken action
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    submessage: tuple # e.g., a DeterrentThreat
    amygdala_params: dict = {'delta_pbf': 0.0, 'delta_fight': 0.0, 'delta_flight': 0.0, 'delta_freeze': 0.0}
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    target_uid: int = 0 # target object if needed, 0 means 'none'


class HotlineRungChangeMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message, presumed to have taken action
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    old_rung: int # the rung we changed from
    new_rung: int # the rung we changed to


class SendPublicMessage(NamedTuple):
    submessage: tuple

    def coerce_to_message(self, uid, time, sender, recipient, addressee=None):
        if self.submessage[2] == None:
            return HotlinePublicROMANCERMessage(uid, recipient, sender, 'HotlinePublicROMANCERMessage', time, self.submessage) # addressee ignored
        else:
            c = self.submessage.class_of
            new_submessage = c(self.submessage[0], self.submessage[1], self.submessage[2] + time)
            return HotlinePublicROMANCERMessage(uid, recipient, sender, 'HotlinePublicROMANCERMessage', time, new_submessage)


class SendPrivateMessage(NamedTuple):
    submessage: tuple

    def coerce_to_message(self, uid, time, sender, recipient, addressee=None):
        return HotlinePrivateROMANCERMessage(uid, recipient, sender, 'HotlinePublicROMANCERMessage', time, self.submessage, target_uid=addressee)

    def coerce_to_message(self, uid, time, sender, recipient, addressee=None):
        if addressee == None:
            new_addressee = 0
        else:
            new_addressee = addressee
        if self.submessage[2] == None:
            return HotlinePublicROMANCERMessage(uid, recipient, sender, 'HotlinePublicROMANCERMessage', time, self.submessage)
        else:
            c = self.submessage.class_of
            new_submessage = c(self.submessage[0], self.submessage[1], self.submessage[2] + time)
            return HotlinePublicROMANCERMessage(uid, recipient, sender, 'HotlinePublicROMANCERMessage', time, new_submessage)

    
class HotlineMessagePercept(Percept):
    '''This percept is used to transmit messages to agents. Each message consists of a sequence of DeterrentThreats, CompellentThreats, and/or ConcessionOffers. The percept can reflect multiple messages (e.g., simultaneous public and private messages).

    HotlineMessagePercept(messages=(PublicMessage(contents=(DeterrentThreat(provocation=11, threat=13, deadline=None), DeterrentThreat(provocation=17, threat=21, deadline=3110.75), CompellentThreat(demanded_action=22, threat=23, deadline=3050.0))), PrivateMessage(contents=(DeterrentThreat(provocation=15, threat=13, deadline=None), ConcessionOffer(quid=27, quo=28, deadline=3025.5)), recipient=7)))'''
    

class HotlineActionPercept(Percept):
    '''This percept is used to inform one or more agents that a particular action has been taken by a particular agent. In principle, it can reflect disinformation.

    HotlineActionPercept(actor=7, action_taken=28)'''


class HotlinePerceptionEngine(PerceptionEngine):
    '''The HotlinePerceptionEngine works like the CommandPEPerceptionEngine, except that it can force two kinds of Percepts--HotlineMessagePercepts that send messages to either specific recipeints or everyone, or HotlineActionPercepts that broacast to all agents that a specific agent has taken an action. Like the CommandPEPerceptionEngine, these forced percepts can be mixed with observers generating percepts based upon the simulated environment.'''

    
    def __init__(self, environment=None):
        super().__init__(environment)
        self.queued_percepts = dict() # {agent_id: [percept_list]}
        self.queued_percepts_time = inf


    def run(self, **kwargs):
        observer_percepts = super().run() # in default case where there are no observers, returns an empty dict
        # check to see if it is time for currently queued percepts
        if self.environment.time == self.queued_percepts_time: # I don't think this should ever happen under normal circumstances but we should check to be safe
            for key in self.queued_percepts.keys():
                # if it is, add queued percepts to observer_percepts
                if key in observer_percepts:
                    observer_percepts[key] += self.queued_percepts[key]
                else:
                    observer_percepts[key] = self.queued_percepts[key]
                    # now we clear the queued percepts for each key (agent_id)
                    self.queued_percepts[key] = []
        return observer_percepts


    def force_message_percept(self, time, public_messages, private_messages):
        '''Send messages to one or more agents. Public messages broadcast to all agents; private messages are sent to their intended recipient.'''
        private_recipients = {message.recipient for message in private_messages}
        for recipient in private_recipients:
            addressed = [message for message in private_messages if message.recipient == recipient]
            percept = HotlineMessagePercept(messages=tuple(public_messages + addressed))
            if recipient in self.queued_percepts:
                self.queued_percepts[recipient] += [percept]
            else:
                self.queued_percepts[recipient] = [percept]
        other_recipients = {agent.uid for agent in self.environment.agents} | private_recipients # agents that didn't get a private message
        for recipient in other_recipients:
            percept = HotlineMessagePercept(messages=tuple(public_messages)) # public messages only
            if recipient in self.queued_percepts:
                self.queued_percepts[recipient] += [percept]
            else:
                self.queued_percepts[recipient] = [percept]
        self.queued_percepts_time = time
                

    def force_action_percept(self, time, agent_id, action_taken):
        '''Action messages automatically broadcast to all agents.'''
        recipients = {agent.uid for agent in self.environment.agents}
        percept = HotlineActionPercept(actor = agent_id, action_taken = action_taken) # public messages only
        for recipient in recipients:
            if recipient in self.queued_percepts:
                self.queued_percepts[recipient] += [percept]
            else:
                self.queued_percepts[recipient] = [percept]
        self.queued_percepts_time = time
    

class HotlinePerceptionFilter(PerceptionFilter):
    '''The HotlinePerceptionFilter is currently designed to digest only HotlineActionPercepts and HotlineMessagePercepts. It is designed to alter messages based on the recipients ontology, by replacing certain actions with substitutes.'''

    def __init__(self, agent, known, substitutions, wildcard):
        super().__init__(agent)
        self.known = known # set of all numbers recognized by this agent (*not* in substitution table)
        self.substitutions = substitutions # dict mapping integers to other integers
        self.wildcard = wildcard # used to substitute for integers in messages which are unknown and lack a substitution

        
    def digest_percept(self, percept):
        '''This method processes the input percept into a new percept using the substitution table and wildcard. If a number in a message is in the substitution table, it is substituted with than number. If it is neither in known or in the substitution table, it is replaced by the wildcard value.'''

        cur_params = self.agent.amygdala.current_amygdala_parameters()
        
        def digest_submessage(submessage):
            c = submessage.class_obj # fetch submessage's class constructor
            l = list()
            for i in range(2):
                if submessage[i] in self.substitutions:
                    l.append(self.substitutions[submessage[i]])
                elif submessage[i] not in self.known:
                    l.append(self.wildcard)
                else:
                    l.append(submessage[i])
            l.append(submessage[2]) # append deadline or None
            return c(*l) # construct new DeterrentThreat, CompellentThreat, or ConcessionOffer using substitutions

        if isinstance(percept, HotlineActionPercept):
            updated_percept = HotlineActionPercept(actor=percept.actor, action_taken=percept.action_taken, amygdala_params=cur_params)
        elif isinstance(percept, HotlineMessagePercept):
            edited_messages = list()
            for message in percept.messages:
                submessages = (digest_submessage(s) for s in message)
                if isinstance(message, PublicMessage):
                    edited_messages.append(PublicMessage(contents=tuple(submessages)))
                elif isinstance(message, PrivateMessage):
                    edited_messages.append(PrivateMessage(contents=tuple(submessages), recipient=message.recipient))
            updated_percept = HotlineMessagePercept(messages=tuple(edited_messages), amygdala_params=cur_params)

        
        self.agent.reasoner.enqueue_digested_percept(updated_percept, self.agent.time)


                
                
            

        
