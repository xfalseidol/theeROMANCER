import csv
from romancer.supervisor.watchlist import WatchlistItem
from hotline_percept import HotlineActionROMANCERMessage

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
        description += str(current_action)
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


class HotlineAction(WatchlistItem):
    def __init__(self, time, actor_id, action_id): # defined by an actor and an action
        super().__init__(time)
        self.actor_id = actor_id
        self.action_id = action_id


    def process(self, supervisor): # needs to force an ActionPercept?
        supervisor.environment.perception_engine.force_action_percept(self.time, self.actor_id, self.action_id)
        supervisor.check_for_percepts = True # actions likely to trigger percepts


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        readable_time = _sim_time_to_days(self.time)
        script_version = f"(Day {readable_time}) RED agent takes action: "
        script_version += translation_dictionary[self.action_id]
        return script_version


class HotlineMessage(WatchlistItem):
    def __init__(self, time, sender, message, public = True):
        super().__init__(time)
        self.sender = sender
        self.message = message
        self.public = public

    def process(self, supervisor):
        if self.public:
            supervisor.environment.perception_engine.force_message_percept(self.time, private_messages=[], public_messages=[self.message])
        else:
            supervisor.environment.perception_engine.force_message_percept(self.time, private_messages=[self.message], public_messages=[])
        supervisor.check_for_percepts = True # actions likely to trigger percepts


def hotline_action_dispatcher(sup, message):
    item = HotlineAction(sup.time, message.sender, message.action_id)
    return item


def hotline_public_message_dispatcher(sup, message):
    item = HotlineMessage(message.time, message.sender, message, public=True)
    return item


def hotline_private_message_dispatcher(sup, message):
    item = HotlineMessage(message.time, message.sender, message, public=False)
    return item


def get_scenario_watchlist_items(red_id, blue_id):
    watchlist_items = []
    watchlist_items.append(HotlineAction(1000, red_id, 13))
    return watchlist_items


def hotline_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the agent will take. This can be an arbitrary action. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action, but it can also represent non-cognitive processes associated with the "person."'''
    hotline_deliberate_action(o, m)
    # pass


def hotline_deliberate_action(o, m):
    '''The purpose of this method is to determine whether the agent plans to execute a deliberate action before a maximum time. Deliberate actions are always deterministic, but deterministic actions are not necessarily deliberate. For example, some agents can move just as vehicles can, and some of those movements can be deterministic from a simulation standpoint while not being deliberate. E.g., if an agent represents a falling person, their physical shift to a different disposition as they fell would be deterministic (in that it can be predicted to occur ast a specific future time) but not deliberate in that the agent may not have planned to fall and may not be aware it is falling. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action.'''
    next_action_time = o.reasoner.next_deliberate_action_time
    if not next_action_time or next_action_time > m.time:
        return None
    else:
        action = o.reasoner.next_deliberate_action
        message = action[0]
        if isinstance(message, HotlineActionROMANCERMessage):
            o.outbox.append(message)
        # message = HotlineActionROMANCERMessage(uid=o.new_message_index, sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='PersonlikeActionROMANCERMessage', action_id=tuple(action), time=next_action_time, most_recent_percept_time=o.most_recent_percept_time)
        # o.outbox.append(message)


def _sim_time_to_days(time):
    return round(time / (3600 * 24), 2) # divided by seconds in a day


translation_dictionary = _make_translation_dictionary()

