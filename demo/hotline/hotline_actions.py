import csv
from typing import NamedTuple
from functools import reduce
from operator import add
from romancer.supervisor.watchlist import WatchlistItem
from hotline_percept import HotlineActionROMANCERMessage

pad = 60
def _make_translation_dictionary():
    actions = 60
    actions_to_names = {}
    current_action = 1
    for action in range(1, actions + 1):
        description = ""
        # who
        if action % 2 == 1:
            description += "Red"
        else:
            description += "Blue"
        # what
        if action % 6 in [1, 2]:
            description += "Punishment"
        elif action % 6 in [3, 4]:
            description += "CompelledConcession"
        elif action % 6 in [5, 0]:
            description += "VoluntaryConcession"
        # which
        description += str(current_action) + "(" + str(action) + ")"
        if action % 6 == 0:
            current_action += 1
        actions_to_names[action] = description
    return actions_to_names


def _save_translation_dictionary():
    with open('actions_dictionary.csv', 'w', newline='') as csv_file:  
        writer = csv.writer(csv_file)
        writer.writerow(["Action", "Name"])
        for key, value in translation_dictionary.items():
            writer.writerow([key, value])


def _get_amygdala_display(params):
    if params:
        pbf = str(round(params.current_pbf, 2))
        fight = str(round(params.current_fight, 2))
        flight = str(round(params.current_flight, 2))
        freeze = str(round(params.current_freeze, 2))
        return "stress: (" + pbf + ", " + fight + ", " + flight + ", " + freeze + ")"


class DeterrentThreat(NamedTuple): # "Don't Do (provocation) or else I'll (threat) until (deadline??)"
    provocation: int # action adversary could take that threatener wants to deter
    threat: int # threatened action if recipient takes provocative action
    deadline: any # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if isinstance(percept, HotlineMessagePercept)])
        submessages = reduce(add, [message.contents for message in messages])
        deterrent_threats = filter(lambda m: isinstance(m, DeterrentThreat), submessages)

        for dt in deterrent_threats:
            if self.provocation == dt.provocation and self.threat == dt.threat:
                if dt.deadline:
                    if reasoner.time <= self.deadline:
                        return True
                elif not dt.deadline:
                    return True   

        return False 
    
    
    def __str__(self):
        script_version = f"Don't take {translation_dictionary[self.provocation]} or else I'll take {translation_dictionary[self.threat]}"
        if self.deadline:
            script_version += f", until {self.deadline}"
        script_version += "."
        return script_version


class CompellentThreat(NamedTuple): # "You must do {demanded_action} or else I'll do {threat}; you have until {deadline}"
    demanded_action: int # action adversary could take that threatener wants to compel (i.e., a concession)
    threat: int # threatened action if recipient fails to take demanded action
    deadline: any # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if isinstance(percept, HotlineMessagePercept)])
        submessages = reduce(add, [message.contents for message in messages])
        compellent_threats = filter(lambda m: isinstance(m, CompellentThreat), submessages)

        for ct in compellent_threats:
            if self.demanded_action == ct.demanded_action and self.threat == ct.threat:
                if ct.deadline:
                    if reasoner.time <= ct.deadline:
                        return True
                elif not ct.deadline:
                    return True    
        
        return False
    

    def __str__(self):
        script_version = f"You must take {translation_dictionary[self.demanded_action]} or else I'll take {translation_dictionary[self.threat]}"
        if self.deadline:
            script_version += f"; you have until {self.deadline}"
        script_version += "."
        return script_version

class ConcessionOffer(NamedTuple): # "If you do {quid}, I'll do {quo}, until {deadline}"
    quid: int # offered concession
    quo: int # expected counter-concession
    deadline: any # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if isinstance(percept, HotlineMessagePercept)])
        submessages = reduce(add, [message.contents for message in messages])
        concession_offers = filter(lambda m: isinstance(m, ConcessionOffer), submessages)

        for co in concession_offers:
            if self.quid == co.quid and self.quo == co.quo:
                if co.deadline:
                    if reasoner.time <= co.deadline:
                        return True
                elif not co.deadline:
                    return True   
                
        return False


    def __str__(self):
        script_version = f"If you do {translation_dictionary[self.quid]}, I'll do {translation_dictionary[self.quo]}"
        if self.deadline:
            script_version += f", until {self.deadline}"
        script_version += "."
        return script_version


class HotlineAction(WatchlistItem):
    def __init__(self, time, actor_id, action_id): # defined by an actor and an action
        super().__init__(time)
        self.actor_id = actor_id
        self.action_id = action_id
        self.params = None


    def process(self, supervisor): # needs to force an ActionPercept?
        agent = supervisor.environment.message_dispatch_table[self.actor_id]
        # take next action on agent's reasoner's action queue
        params = agent.reasoner.take_next_action()
        # self.amygdala_update_parameters = params
        if params:
            agent.amygdala.update_parameters(params)
        self.params = agent.amygdala.current_amygdala_parameters()
        supervisor.environment.perception_engine.force_action_percept(self.time, self.actor_id, self.action_id)
        supervisor.check_for_percepts = True # actions likely to trigger percepts


    def __repr__(self):
        return f"HotlineAction(actor_id={self.actor_id}, action_id={self.action_id})"
    
    
    def __str__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        readable_time = _sim_time_to_days(self.time)
        script_version = f"(Day {readable_time}) {agents_to_names[self.actor_id]}: I'm taking action "
        script_version += translation_dictionary[self.action_id]
        stress =''#_get_amygdala_display(self.params)
        return f"{script_version:<75} {stress}"


class HotlineMessage(WatchlistItem):
    def __init__(self, time, sender, message, public = True):
        super().__init__(time)
        self.sender = sender
        self.message = message
        self.public = public
        self.params = None

    
    def process(self, supervisor):
        agent = supervisor.environment.message_dispatch_table[self.sender]
        # take next action on agent's reasoner's action queue
        params = agent.reasoner.take_next_action()
        self.params = agent.amygdala.current_amygdala_parameters()
        if params:
            agent.amygdala.update_parameters(params)
        self.params = agent.amygdala.current_amygdala_parameters()
        if self.public:
            supervisor.environment.perception_engine.force_message_percept(self.time, private_messages=[], public_messages=[self.message])
        else:
            supervisor.environment.perception_engine.force_message_percept(self.time, private_messages=[self.message], public_messages=[])
        supervisor.check_for_percepts = True # actions likely to trigger percepts


    def __repr__(self):
        return f"HotlineMessage(sender={self.sender}, message={self.message}, public={self.public})"


    def __str__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        readable_time = _sim_time_to_days(self.time)
        script_version = f"(Day {readable_time}) {agents_to_names[self.sender]}: {self.message.submessage}"
        stress =''#_get_amygdala_display(self.params)
        return f"{script_version:<75} {stress}"
    

class HotlineRungChange(WatchlistItem):
    def __init__(self, time, who, old_rung, new_rung):
        super().__init__(time)
        self.who = who
        self.old_rung = old_rung
        self.new_rung = new_rung
        self.params = None


    def process(self, supervisor):
        agent = supervisor.environment.message_dispatch_table[self.who]
        params = agent.reasoner.take_next_action()
        if params:
            agent.amygdala.update_parameters(params)
        self.params = agent.amygdala.current_amygdala_parameters()
        self.params = agent.amygdala.current_amygdala_parameters()


    def __repr__(self):
        return f"HotlineRungChange(previous_rung={self.old_rung}, next_rung={self.new_rung})"
    

    def __str__(self):
        readable_time = _sim_time_to_days(self.time)
        script_version = f"(Day {readable_time}) {agents_to_names[self.who]}: "
        if self.old_rung.id < self.new_rung.id:
            script_version += f"I'm escalating from {self.old_rung} to {self.new_rung}."
        else:
            script_version += f"I'm deescalating from {self.old_rung} to {self.new_rung}."
        stress =''#_get_amygdala_display(self.params)
        return f"{script_version:<75} {stress}"


# dispatchers create and return a watchlist item
def hotline_action_dispatcher(sup, message):
    item = HotlineAction(message.time, message.sender[1], message.action_id)
    return item


def hotline_public_message_dispatcher(sup, message):
    item = HotlineMessage(message.time, message.sender[1], message, public=True)
    return item


def hotline_private_message_dispatcher(sup, message):
    item = HotlineMessage(message.time, message.sender[1], message, public=False)
    return item


def get_scenario_watchlist_items(red_id, blue_id):
    watchlist_items = []
    watchlist_items.append(HotlineAction(1000, red_id, 13))
    return watchlist_items


def hotline_deterministic_action(o, m):
    '''A HotlineAgent has no non-autonomous deterministic actions (they are strictly autonomous agents)'''
    hotline_deliberate_action(o, m)


def hotline_deliberate_action(o, m):
    '''The purpose of this method is to determine whether the agent plans to execute a deliberate action before a maximum time. Deliberate actions are always deterministic, but deterministic actions are not necessarily deliberate. For example, some agents can move just as vehicles can, and some of those movements can be deterministic from a simulation standpoint while not being deliberate. E.g., if an agent represents a falling person, their physical shift to a different disposition as they fell would be deterministic (in that it can be predicted to occur ast a specific future time) but not deliberate in that the agent may not have planned to fall and may not be aware it is falling. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action.'''
    next_action_time = o.reasoner.next_deliberate_action_time
    if not next_action_time or next_action_time > m.time:
        return None
    else:
        action = o.reasoner.next_deliberate_action # action could be an integer or a Threat/Concession
        # message = PersonlikeActionROMANCERMessage(uid=o.new_message_index, sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='PersonlikeActionROMANCERMessage', actions=tuple(action), time=next_action_time, most_recent_percept_time=o.most_recent_percept_time)
        if isinstance(action, int):
            message = HotlineActionROMANCERMessage(uid=o.new_message_index, sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='HotlineActionROMANCERMessage', action_id=action, time=next_action_time)
            o.outbox.append(message)
        else:
            # print("I'm sending a message!!")
            o.outbox.append(action)


def hotline_rung_change_dispatcher(sup, message):
    item = HotlineRungChange(message.time, message.sender[1], message.old_rung, message.new_rung)
    return item


def _sim_time_to_days(time):
    return round(time / (3600 * 24), 2) # divided by seconds in a day


translation_dictionary = _make_translation_dictionary()
agents_to_names = {6: 'RED', 10: 'BLUE'}
