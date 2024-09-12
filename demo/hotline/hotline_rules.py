import csv
from functools import reduce
from typing import NamedTuple

from agent.amygdala import UpdateAmygdalaParameters
from demo.hotline.hotline_percept import HotlineActionPercept, HotlineMessagePercept, SendPublicMessage, \
    SendPrivateMessage


class any_of(tuple):

    def evaluate(self, reasoner, amygdala):
        '''Recursively evaluate contents of self until at least one top-level member evaluates to True. If a member is an integer, it is assumed to represent an action that the reasoner perceives to have been taken.'''

        taken_actions = set({percept.action_taken for percept in reasoner.digested_percepts if
                             isinstance(percept, HotlineActionPercept)})

        def action_taken(n):
            return n in taken_actions

        # actions_taken = []
        # for m in self:
        #     if isinstance(m, int):
        #         actions_taken.append(action_taken(m))
        #     else:
        #         actions_taken.append(m.evaluate(reasoner, amygdala))
        # return any(actions_taken)
        # returns true if any action m has been taken or if any other behavior m evaluates to true
        return any((action_taken(m) if isinstance(m, int) else m.evaluate(reasoner, amygdala) for m in self if
                    isinstance(m, int)))


class all_of(tuple):

    def evaluate(self, reasoner, amygdala):
        '''Recursively evaluate contents of self, breaking if a top-level member evaluates False. Returns True if all top-level members return True. If a member is an integer, it is assumed to represent an action that the reasoner perceives to have been taken.'''

        taken_actions = set(
            {percept.action_taken for percept in self.digested_percepts if isinstance(percept, HotlineActionPercept)})

        def action_taken(n):
            return n in taken_actions

        return all((action_taken(m) if isinstance(m, int) else m.evaluate(reasoner, amygdala) for m in self))


class ActionTaken(NamedTuple):
    action: int

    def evaluate(self, reasoner, amygdala):
        return self.action in reasoner.action_taken


class min_adversary_resolve(NamedTuple):
    min_resolve: float

    def evaluate(self, reasoner, amygdala):
        '''Checks if current estimate of adversary resolve presently meets of exceeds self.min_resolve.'''
        return reasoner.perceived_adversary_resolve >= self.min_resolve


class ActionLexicon:
    def __init__(self, csvfile):
        self.actionlexicon = {}
        with open(csvfile, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            self.colnames = reader.fieldnames
            for row in reader:
                actnum = int(row['action_num'])
                self.actionlexicon[actnum] = row

    def get_actionnum(self, side, action, suffix): # g for "get". Expect to call this a lot
        for k, v in self.actionlexicon.items():
            if v['side'] == side and v['action'] == action and v['suffix'] == suffix:
                return k
        return None

    def getlabel(self, actnum):
        thisact = self.actionlexicon[actnum]
        return f"{thisact['side']}{thisact['action']}{thisact['suffix']}({actnum})"

actionlexicon = ActionLexicon("data/action_lexicon.csv")

class DoAction(NamedTuple):
    action: int
    deadline: any

class DeterrentThreat(NamedTuple):  # "Don't Do (provocation) or else I'll (threat) until (deadline??)"
    provocation: int  # action adversary could take that threatener wants to deter
    threat: int  # threatened action if recipient takes provocative action
    deadline: any  # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if
                                isinstance(percept, HotlineMessagePercept)])
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
        script_version = f"Don't take {self.provocation} or else I'll take {self.threat}"
        if self.deadline:
            script_version += f", until {self.deadline}"
        script_version += "."
        return script_version


class CompellentThreat(
    NamedTuple):  # "You must do {demanded_action} or else I'll do {threat}; you have until {deadline}"
    demanded_action: int  # action adversary could take that threatener wants to compel (i.e., a concession)
    threat: int  # threatened action if recipient fails to take demanded action
    deadline: any  # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if
                                isinstance(percept, HotlineMessagePercept)])
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


class ConcessionOffer(NamedTuple):  # "If you do {quid}, I'll do {quo}, until {deadline}"
    quid: int  # offered concession
    quo: int  # expected counter-concession
    deadline: any  # float representing future time or None if no deadline given

    def evaluate(self, reasoner, amygdala):
        '''Determine whether this threat is currently credible to reasoner given its internal state.'''

        messages = reduce(add, [percept.messages for percept in self.digested_percepts if
                                isinstance(percept, HotlineMessagePercept)])
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


# Return a map of run_number to matcher
def load_matcher_csv(csvfile, actionlexicon, actor_mapping={}):
    # Any actors [subject, object] that appear as keys in actor_mapping get replaced with their mapped value
    retval = {}

    rules = []
    with open(csvfile, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 0 == len(row["rung_number"].strip()):
                continue

            rung_number = int(row['rung_number'])
            rules = retval.get(rung_number, [])
            retval[rung_number] = rules

            subject_side = actor_mapping[row['subject_side']] if row['subject_side'] in actor_mapping else row['subject_side']
            object_side = actor_mapping[row['object_side']] if row['object_side'] in actor_mapping else row['object_side']
            actor_subj = actionlexicon.get_actionnum(subject_side, row['subject_action'], row['subject_suffix'])
            actor_obj = actionlexicon.get_actionnum(object_side, row['object_action'], row['object_suffix'])
            if actor_subj is None:
                print(f"Error in input. Could not find action number for {row['subject_side']}={subject_side} {row['subject_action']} {row['subject_suffix']}")

            min_resolve_str = row.get('min_adversary_resolve', '')
            min_resolve = min_adversary_resolve(float(min_resolve_str) if len(min_resolve_str)>0 else -1)
            if row['verb'] == 'ActionTaken':
                rules.append(ActionTaken(actor_subj))
            elif row['verb'] == 'DeterrentThreat':
                threat = DeterrentThreat(actor_subj, actor_obj, None)
                rules.append(all_of([threat, min_resolve]))
            elif row['verb'] == 'CompellentThreat':
                threat = CompellentThreat(actor_subj, actor_obj, None)
                rules.append(all_of([threat, min_resolve]))

    return {rung: any_of(rules) for rung, rules in retval.items()}


# Return a map of rung_number to list of time-action tuples
def load_actions_csv(csvfile, actionlexicon, actiontype="action", actor_mapping={}):
    # Any actors [subject, object] that appear as keys in actor_mapping get replaced with their mapped value
    retval = {}

    rules = []
    with open(csvfile, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 0 == len(row["rung_number"].strip()):
                continue

            rung_number = int(row['rung_number'])
            rules = retval.get(rung_number, [])
            retval[rung_number] = rules

            if row['act_type'] != actiontype:
                continue

            action_time = float(row['action_time'])

            subject_side = actor_mapping[row['subject_side']] if row['subject_side'] in actor_mapping else row['subject_side']
            actor_subj = actionlexicon.get_actionnum(subject_side, row['subject_action'], row['subject_suffix'])
            actor_obj = None
            have_object = len(row['object_side'].strip())>0
            if have_object:
                object_side = actor_mapping[row['object_side']] if row['object_side'] in actor_mapping else row['object_side']
                actor_obj = actionlexicon.get_actionnum(object_side, row['object_action'], row['object_suffix'])

            if actor_subj is None:
                print(f"Error in input. Could not find action number for {row['subject_side']}={subject_side} {row['subject_action']} {row['subject_suffix']}")

            act = None
            if row['verb'] == 'DoAction':
                act = DoAction(actor_subj, None)
            elif row['verb'] == 'DeterrentThreat':
                act = DeterrentThreat(actor_subj, actor_obj, None)
            elif row['verb'] == 'ConcessionOffer':
                act = ConcessionOffer(actor_subj, actor_obj, None)
            elif len(row['verb'].strip()) > 0:
                print(f"Error in input, don't know what to do with verb column {row['verb']}")
                continue

            if row['message'] == "SendPublicMessage":
                act = SendPublicMessage(act)
            elif row['message'] == "SendPrivateMessage":
                act = SendPrivateMessage(act)
            elif len(row['message'].strip())>0:
                print(f"Error in input, don't know what to do with message column {row['message']}")
                continue

            if len(row['delta_amyg_pbf'].strip()) > 0:
                updateaymg = UpdateAmygdalaParameters(float(row['delta_amyg_pbf']),
                                                      float(row['delta_amyg_fight']),
                                                      float(row['delta_amyg_flight']),
                                                      float(row['delta_amyg_freeze']))
            else:
                updateaymg = UpdateAmygdalaParameters(0, 0, 0, 0)

            rules.append((action_time, act, updateaymg))

    return retval
