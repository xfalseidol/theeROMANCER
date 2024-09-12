from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from romancer.agent.amygdala import UpdateAmygdalaParameters
from romancer.agent.reasoner import Reasoner
from romancer.agent.personlikeagent import PersonlikeActionROMANCERMessage
from romancer.commandpe.watchlist import CommandPEWatchlistItem
from collections import UserList
from heapq import heapify, heappush, heappop
from scipy import optimize
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import math
from collections import namedtuple


class EscalationLadder(UserList):
    '''The EscalationLadderReasoner stores its ontology in an instance of the EscalationLadder class. This is an ordered collection of Rung objects representing the ascending levels of escalation. The information about what internal perceptions (perception filter outpus) will cause the reasoner to match against these rungs and perceive that a particular rung of the escalation ladder has been reached is stored in the Rung objects, as are the actions that the reasoner considers appropriate at this rung of the escalation ladder given its intentions/internal state.

    Note that this EscalationLadder is not logged and is therefore meant to be treated as a static, unchanging object in the context of the simulation.

    A key purpose for the EscalationLadder class that is not yet implemented here is a visualization method.'''

    # default __init__ method is probably already sufficient here, although it might be appropriate to make it assert that the EscalationLadder contains only Rung objects

    def next_rung(self, current_rung):
        '''This method returns the next rung on the escalation ladder after current_rung, or None if current_rung is the top rung.'''
        cur_i = self.data.index(current_rung)
        try:
            next_rung = self.data[cur_i + 1]
        except IndexError:
            next_rung = None
        finally:
            return next_rung

    def previous_rung(self, current_rung):
        '''The opposite of next_rung.'''
        cur_i = self.data.index(current_rung)
        if cur_i == 0:
            return None
        try:
            previous_rung = self.data[cur_i - 1]
        except IndexError:
            previous_rung = None
        finally:
            return previous_rung

    # for deliberating into the future
    def next_matched_rung(self, current_rung, reasoner, amygdala):
        matched = False
        next_rung = self.next_rung(current_rung)
        while next_rung:
            matched = next_rung.rung_matched(reasoner, amygdala)
            if matched:
                return next_rung
            next_rung = self.next_rung(next_rung)

    # for deliberaing present time
    def highest_matched_rung(self, current_rung, reasoner, amygdala):
        matched = False
        next_rung = self.data[0]
        highest_matched_rung = None
        while next_rung:
            matched = next_rung.rung_matched(reasoner, amygdala)
            if matched:
                #print(f"Matched. current_rung={current_rung}, next_rung={next_rung}")
                highest_matched_rung = next_rung
            next_rung = self.next_rung(next_rung)
        return highest_matched_rung


    def rung_number(self, rung):
        return self.data.index(rung)
    

class EscalationLadderRung():
    '''Much of the logic of the EscalationLadderReasoner is stored in EscalationLadderRung instances. This permits these rungs to exhibit custom behavior if necessary.'''
    rung_id = 1

    def __init__(self, match_attributes=None, actions=[], deescalation_actions=[], pbf_threshold = 1.0, amygdala_update=UpdateAmygdalaParameters(0, 0, 0, 0), name=""):
        self.match_attributes = match_attributes # a sequence of patterns that are used to check whether agent believes that this rung has been reached
        self.pbf_threshold = pbf_threshold # what stress level would trigger this rung regardless of match_attributes
        self.actions = actions # collection of actions that reasoner will take at this rung, associated with amount of time that must pass before/between those actions
        self.deescalation_actions = deescalation_actions # collection of actions that reasoner will take at this rung if it is attempting to de-escalate the situation, associated with amount of time that must pass before/between those actions
        self.amygdala_update = amygdala_update
        self.id = EscalationLadderRung.rung_id
        self.name = name
        EscalationLadderRung.rung_id += 1

    def rung_matched(self, reasoner, amygdala):
        dominant_response = amygdala.dominant_response()
        if dominant_response == amygdala.FREEZE_STR: # never escalate
            return False
        if dominant_response == amygdala.FIGHT_STR: # always escalate
            return True
        if dominant_response == amygdala.FLIGHT_STR: # try to de-escalate
            return False
        
        # ANY attribute in match_attributes matches a digested percept
        for attribute, value in self.match_attributes.items():
            for percept in reasoner.digested_percepts:
                try:
                    for event in percept.events_list:
                        percept_value = event[attribute]
                        if value == percept_value:
                            return True # an attribute matched
                except AttributeError:
                    pass # not a problem
        return False
    

    def coerce_attribues_to_matcher(self, attributes):
        '''This method uses the information stored in match_attributes to return a Python callable with an EscalationLadderReasoner, Amygdala call signature. Returns True if these attributes are met based on current state of reasoner and amygdala, False otherwise.'''
        def matcher(reasoner, amygdala_params): # possibly create lexical closure storing information for use by matcher
            return False

        return matcher


    def update_planned_actions(self, reasoner):
        '''This method mutates the passed reasoner's planned_actions attribute. Defaults to simply resetting planned action queue. This method assumes that all matchers associated with this rung have been evaluated.'''
        reasoner.planned_actions.clear()


    def untaken_actions(self, actions, reasoner):
        '''This method returns a set of actions that are not in the reasoner's actions_taken list. It may be handy to override this method to get more subtle, custom behavior from certain rungs.'''
        # return set(reasoner.actions_taken).difference(actions) # FIX
        return actions


    def enqueue_deescalation_actions(self, reasoner):
        '''This method enqueues the red deescalation actions associated with this rung in the reasoner's action queue.'''
        reasoner.enqueue_deescalation_actions(self.deescalation_actions, reasoner)

    def check_for_deescalation(self, reasoner, amygdala):
        '''This method uses information stored in this rung and the reasoner, in conjunction with the current amygdala state, to determine whether it appears that the adversary is attempting to deescalate (from the reasoner's standpoint, or if the agent is is desperate based on its amygdala state that it wants to try to deescalate no matter what. (This captures the case in which stressors cause the agent to become more desparate even though conditions necessary to match a higher rung of the escalation ladder have not occured.)'''
        # This needs to compare reasoner.digested_percepts and the opponent's deescalation_actions and return True if there is a suffient match
        # It seems reasonable that deescalation will usually be associated with *special* percepts (explicit messages) that will be easy to test for, but for a general solution it will be necessary to consider the whole percept history somehow
        # Also return True if dominant amygdala response is currently 'flight'
        parameters = amygdala.current_amygdala_parameters()
        if parameters.current_dominant_response == amygdala.FLIGHT_STR:
            return True, False
        elif parameters.current_dominant_response == amygdala.FREEZE_STR or parameters.current_dominant_response == amygdala.FIGHT_STR:
            return False, False
        else:                  
            return False, False
    
    def __repr__(self):
        return "Rung " + str(self.id)
    
class MatchAllRung(EscalationLadderRung):
    def rung_matched(self, reasoner, amygdala):
        dominant_response = amygdala.dominant_response()
        if dominant_response == amygdala.FREEZE_STR: # never escalate
            return False
        if dominant_response == amygdala.FIGHT_STR: # always escalate
            return True
        if dominant_response == amygdala.FLIGHT_STR: # try to de-escalate
            return False

        # if any digested percept's singular event matches all attributes, the rung is matched
        for percept in reasoner.digested_percepts:
            # we want to match EVERY attribute in match_attributes against SOME event in the percept's event list
            for event in percept.events_list:
                match = True # try to proce there ISN't a match
                for attribute, value in self.match_attributes.items():
                    try: # attempt to access the match attribute out of the current event
                        if event[attribute] != value:
                            match = False # at least one attribute does not match
                    except:
                        match = False # the event does not have the right attributes
                if match: # all rung attributes have a matching value in the event
                    return True
        return False # no event in any percept matches this rung

class EscalationLadderReasoner(Reasoner):
    '''
    '''

    def __init__(self,  environment, time, escalation_ladder, identity, current_rung = None, planned_actions = None, actions_taken = None, digested_percepts = None, cbr = None):
        super().__init__(environment, time)
        self.escalation_ladder = escalation_ladder # an EscalationLadder instance
        self.identity = identity # 'blue' or 'red'
        if current_rung and current_rung in self.escalation_ladder: # rung of escalation ladder agent believes represents current state of conflict
            self.current_rung = current_rung
        elif current_rung == None:
            self.current_rung = self.escalation_ladder[0]
        else:
            raise ValueError('Current rung not in EscalationLadder')
        if planned_actions: # should planned_actions be a logged UserList?
            self.planned_actions = planned_actions # planned_actions should be a list of (planned_action_time, action) tuples representing actions that the agent plans to take in the future. These can be provided out of chronological order as EscalationLadderReasoner will heapify them into a priority queue
            # WILL BINARY HEAP PRIORITY QUEUE WORK CORRECTLY WITH LoggedList?
        else:
            self.planned_actions = list()
        heapify(self.planned_actions) # ensure planned actions are heapified
        if actions_taken: 
            self.actions_taken = LoggedList(data = sorted(actions_taken, key = lambda p: p[0]), parent = self, varname = 'actions_taken') # actions taken sorted in ascending chronological time
        else:
            self.actions_taken = LoggedList(data = list(), parent = self, varname = 'actions_taken')
        if digested_percepts:
            self.digested_percepts = LoggedList(data = digested_percepts, parent = self, varname = 'digested_percepts')
        else:
            self.digested_percepts = LoggedList(data = list(), parent = self, varname = 'digested_percepts')
        self.max_deliberation_time = self.time # maximum time to which reasoner has deliberated; should this be unlogged?
        self.most_recent_percept_time = self.time
        self.plot_time = []
        self.plot_rungs = []
        self.cbr = cbr
        self.capture_plot()

    def reset_reasoner(self, rung_num=0):
        self.rewind(0)
        self.digested_percepts.clear()
        self.actions_taken.clear()
        self.planned_actions.clear()
        self.current_rung = self.escalation_ladder[rung_num]

    def enqueue_digested_percept(self, digested_percept, percept_time):
        '''This method is used to update the EscalationLadderReasoner's internal state on the basis of the output of the egent's perception filter. What this does is enque the digested percept in the history of percepts digested by the reasoner, and update the reasoner's max_deliberation_time so that the next time that its deliberate method is called, its planned future actions will be recalculated if necessary.'''
        if percept_time < self.most_recent_percept_time:
            self.rewind(percept_time) # this
            self.max_deliberation_time = percept_time
            # what, if anything, should be done with planned_actions at this juncture?
            # presumably deliberate() should check if a new percept has been received since those actions were planned and then
            # edit planned actions accordingly
            # maybe add attr to EscalationLadderReasoner to act as flag for this, containing planned action most recent percept time?
            no_digested_percepts = len(self.digested_percepts)
            # pop self.digested_percepts until percepts are earlier than the  new digested percepts
            for i in range(no_digested_percepts):
                if self.digested_percepts.time > percept_time:
                    self.digested_percepts.pop()
                else:
                    break
            self.digested_percepts.append(digested_percept)
        elif percept_time == self.time: # this should be the case when the percept is the "next interesting event" processed by the supervisor
            self.max_deliberation_time = percept_time
            self.digested_percepts.append(digested_percept)

        if percept_time > self.most_recent_percept_time:
            self.most_recent_percept_time = percept_time


    def deliberate(self, max_time, amygdala):
        '''This method causes the agent to cogitate and predict how its mental state and intentions will evolve up until max_time in the future, presuming that it receives no additional percepts after the current time. One of the purposes of this method is to establish the evolution of the internal mental state of the agent. These changes can be stored on the loglist and then used to account for how a new percept can interrupt the agent's 'chain of thought.'
        '''
        amygdala.capture_plot()
        pres_time = self.time
        no_change = True

        # determine if a higher rung is matched now and escalate accordingly
        next_rung = self.escalation_ladder.highest_matched_rung(self.current_rung, self, amygdala)
        if next_rung:
            self._remember_scenario(percepts = self.digested_percepts,
                                    amygdala_parameters = amygdala.current_amygdala_parameters(),
                                    current_rung_match_attributes = self.current_rung.match_attributes,
                                    outcome = 'escalate')
            self._escalate(next_rung, amygdala)
            no_change = False

        # Check for de-escalation and attempt to de-escalate if possible and desired
        deescalate, adversary_deescalated = self.current_rung.check_for_deescalation(self, amygdala)
        if deescalate or adversary_deescalated:
            self._remember_scenario(percepts = self.digested_percepts,
                                    amygdala_parameters = amygdala.current_amygdala_parameters(),
                                    current_rung_match_attributes = self.current_rung.match_attributes,
                                    outcome = 'deescalate')
            self._deescalate(amygdala)
            self.digested_percepts.clear()
            no_change = False

        if no_change:
            self._remember_scenario(percepts = self.digested_percepts,
                                    amygdala_parameters = amygdala.current_amygdala_parameters(),
                                    current_rung_match_attributes = self.current_rung.match_attributes,
                                    outcome = 'no_change')
        
        # determine if a higher rung will be matched in the future\
        if max_time > pres_time:
            self.forward_simulation(max_time, amygdala)
            next_rung = self.escalation_ladder.next_matched_rung(self.current_rung, self, amygdala)
            if next_rung: # there is a match in the future
                match_time = self._find_approximate_match_time(pres_time, max_time, next_rung, amygdala)
                # create a new WatchlistItem at future match time
                self._push_empty_action(match_time)
            self.max_deliberation_time = max_time
        # self.rewind(pres_time)
    
    def _remember_scenario(self, percepts, amygdala_parameters, current_rung_match_attributes, outcome):
        if self.cbr:
            # must ensure we pass percepts as a list of dictionaries and current_rung_match_attributes is a dictionary
            ## percepts has attribute events_list, which is a list of percept dictionaries
            percepts_as_list_of_dict = []
            for percept in percepts:
                percepts_as_list_of_dict.append(percept.events_list)
            if self.cbr is not None:
                self.cbr.add_ELRScenario(percepts=percepts_as_list_of_dict, amygdala_parameters=amygdala_parameters, current_rung_match_attributes=current_rung_match_attributes, outcome=outcome)

    def _push_empty_action(self, time):
        heappush(self.planned_actions, (time, tuple(), UpdateAmygdalaParameters(0, 0, 0, 0)))
        
    @property
    def next_deliberate_action(self):
        if len(self.planned_actions):
            return self.planned_actions[0][1] # this is an iterable of messages for the supervisor
        else:
            return None


    @property
    def next_deliberate_action_time(self):
        if len(self.planned_actions):
            return self.planned_actions[0][0]
        else:
            return None

        
    def take_next_action(self):
        '''This method is meant to be called when a WatchListItem reflecting the agent's planned action is processed by the Supervisor. It should be an internal implementation detail which is called via a method on the PersonLikeAgent, which uses the values it returns to update the Amygdala state.'''
        action_time, messages, params = heappop(self.planned_actions) # This should return an iterable of messages 
        self.forward_simulation(action_time) # make sure that Reasoner is at correct time, although in practice this should do nothing as forward_simulation should have been called on the Agent first
        # send messages to supervisor reflecting actions, if necessary
        actions = []
        for message in messages:
            actions.append(message.actions)
        if len(messages) > 0:
            self.environment.supervisor.inbox.clear() # should already be empty
            self.environment.supervisor.deliver_messages(messages)
            self.environment.supervisor.process_inbox() # all messages should be at the same time, otherwise would be separate actions
            self.environment.supervisor.inbox.clear() # remove action messages
        self.actions_taken.append((action_time, actions))
        return params # the caller should use these to update the agent's amygdala parameters; much of the time taking action should reduce pbf, inclination to fight or flight


    def _escalate(self, next_rung, amygdala):
        next_rung.update_planned_actions(self)
        self.current_rung = next_rung
        self._enqueue_actions()
        self.capture_plot()


    def _enqueue_actions(self):
        for action in self.current_rung.actions:
            delta_t, draft_messages, update_params = action # unpack 3-tuple
            action_time = self.time + delta_t
            action_messages = [draft_message.coerce_to_message(**{'uid': self.new_message_index(), 'time': action_time, 'sender': (self.environment.uid, self.uid), 'recipient': (1, 1)}) for draft_message in draft_messages]
            # action_messages = self.untaken_actions(action_messages, reasoner)
            heappush(self.planned_actions, (action_time, tuple(action_messages), update_params))

        if len(self.current_rung.actions) == 0:
            self._push_empty_action(self.time+15 * 60)

    def _enqueue_deescalation_actions(self):
        for action in self.current_rung.deescalation_actions:
            delta_t, draft_messages, update_params = action # unpack 3-tuple
            action_time = self.time + delta_t
            action_messages = [draft_message.coerce_to_message(**{'uid': self.new_message_index(), 'time': action_time, 'sender': (self.environment.uid, self.uid), 'recipient': (1, 1)}) for draft_message in draft_messages]
            # action_messages = self.untaken_actions(action_messages, reasoner)
            heappush(self.planned_actions, (action_time, tuple(action_messages), update_params))

        if len(self.current_rung.deescalation_actions) == 0:
            self._push_empty_action(self.time)

    def _find_approximate_match_time(self, pres_time, max_time, matched_rung, amygdala):
        def matched_at_time(t): # adjust objects to correct time, determine if there's a match
            if t < self.time:
                self.rewind(t)
                amygdala.rewind(t)
            elif t > self.time:
                self.forward_simulation(t, amygdala)
            if matched_rung.rung_matched(self, amygdala):
                return 1
            else:
                return -1
        match_time = optimize.bisect(matched_at_time, pres_time, max_time)
        return match_time


    def _deescalate(self, amygdala):
        # update planned actions
        previous_rung = self.escalation_ladder.previous_rung(self.current_rung)
        if previous_rung:
            self.current_rung.update_planned_actions(self)
            self._enqueue_deescalation_actions()
            self.current_rung = self.escalation_ladder.previous_rung(self.current_rung)
            self.capture_plot()

    def capture_plot(self):
        self.plot_time.append(self.time)
        self.plot_rungs.append(self.escalation_ladder.rung_number(self.current_rung))
        

    def export_plot(self, filename=None, title=None):
        if filename is None:
            filename = "escalationladder.png"

        fig, ax = plt.subplots(figsize=(10, 6))
        # plt.figure(figsize=(10, 6))
        rung_labels = [rung.name for rung in self.escalation_ladder]

        show_ladder_y_axis = False
        if show_ladder_y_axis:

            ax.yaxis.set_visible(False)
            ladder_halfwidth = 180
            ax.set_xlim(-ladder_halfwidth - 5, self.plot_time[len(self.plot_time) - 1])
            ax.set_ylim(-1, len(self.escalation_ladder))

            ladder_linewidth = 3
            ax.axvline(x=-ladder_halfwidth, color='grey', linewidth=ladder_linewidth)
            ax.axvline(x=0, color='grey', linewidth=ladder_linewidth)
            for y in range(len(rung_labels)):
                # ax.axhline(y=y, xmin=-ladder_halfwidth, xmax=0, linewidth=ladder_linewidth, color="grey")
                rung = mlines.Line2D([-ladder_halfwidth, 0], [y, y], color='grey', linewidth=ladder_linewidth)
                ax.add_line(rung)
                ax.text(-ladder_halfwidth/2, y+0.1, rung_labels[y], ha='center', va='center')

        plot_time = self.plot_time.copy()
        plot_time.append(self.environment.time)
        plot_rungs = self.plot_rungs.copy()
        plot_rungs.append(plot_rungs[-1])
        plt.step(plot_time, plot_rungs, label="Rung", marker="o")
        plt.xlabel("Time (s)")
        plt.ylabel("Ladder")
        plt.title("Escalation Ladder" if title is None else title)
        plt.legend()

        plt.yticks(range(len(rung_labels)), labels=rung_labels)
        # plt.savefig(filename)
        plt.show()
        plt.close()

    def visualise_final(self):
        super().visualise_final()
        self.export_plot()


