import csv
from typing import NamedTuple
from functools import reduce
from operator import add

from romancer.supervisor.watchlist import WatchlistItem
from hotline_percept import HotlineActionROMANCERMessage

def _get_amygdala_display(params):
    if params:
        pbf = str(round(params.current_pbf, 2))
        fight = str(round(params.current_fight, 2))
        flight = str(round(params.current_flight, 2))
        freeze = str(round(params.current_freeze, 2))
        return "stress: (" + pbf + ", " + fight + ", " + flight + ", " + freeze + ")"


class HotlineAction(WatchlistItem):
    def __init__(self, time, actor_id, action_id, action_label=None): # defined by an actor and an action
        super().__init__(time)
        self.actor_id = actor_id
        self.action_id = action_id
        self.params = None
        self.action_label = action_label if action_label is not None else f"{actor_id}.{action_id}"


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
        script_version = f"(Day {readable_time}) {agents_to_names[self.actor_id]}: "
        stress = '' #_get_amygdala_display(self.params)
        if self.action_id == -1:
            script_version += f"Redeliberating... (because expected amygdala domincance change)"
        else:
            script_version +=  "I'm taking action "
            script_version += self.action_label
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
    def __init__(self, time, who, old_rung, new_rung, why):
        super().__init__(time)
        self.who = who
        self.old_rung = old_rung
        self.new_rung = new_rung
        self.why = why
        self.params = None


    def process(self, supervisor):
        agent = supervisor.environment.message_dispatch_table[self.who]
        params = agent.reasoner.take_next_action()
        if params:
            agent.amygdala.update_parameters(params)
        self.params = agent.amygdala.current_amygdala_parameters()


    def __repr__(self):
        return f"HotlineRungChange(previous_rung={self.old_rung}, next_rung={self.new_rung})"
    

    def __str__(self):
        readable_time = _sim_time_to_days(self.time)
        script_version = f"(Day {readable_time}) {agents_to_names[self.who]}: "
        if self.old_rung.id < self.new_rung.id:
            script_version += f"I'm escalating from {self.old_rung.name} to {self.new_rung.name}. (because {self.why})"
        elif self.old_rung.id > self.new_rung.id:
            script_version += f"I'm deescalating from {self.old_rung.name} to {self.new_rung.name}. (because {self.why})"
        else:
            script_version += f"I've decided not to change rungs, at {self.new_rung.name}. (because {self.why})"
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
    item = HotlineRungChange(message.time, message.sender[1], message.old_rung, message.new_rung, message.why)
    return item


def _sim_time_to_days(time):
    return round(time / (3600 * 24), 3) # divided by seconds in a day


agents_to_names = {6: 'RED', 10: 'BLUE'}
