from context import *
from casebasedreasoner.util import make_graphviz_graph
import networkx as nx
import matplotlib.pyplot as plt

import romancer.supervisor.singlethreadsupervisor

class Judge(casebasedreasoner.cbr.CaseBasedReasoner):
    def judge(self, case_slots): # in book, this takes slots, turns them into a mop, and installs it
        instance = self.slots_to_mop(slots=case_slots, absts={'M-CRIME'}, mop_type='instance', must_work=True)
        defendant = instance.role_filler('defendant')
        print(f"Sentencing {defendant} in {instance}...")
        instance.get_filler('sentence')
        return instance
    

    def judge_case(self, case_slots): # in book, this takes in slot_forms, turns them into slots
        print("---------------------------")
        instance = self.judge(case_slots)
        sentence = instance.role_filler('sentence')
        print(f"Sentence in {instance} is {sentence}.")


    def calculate_escalations(self, mop):
        print("---------------------------")
        print(f"Calculating escalations in {mop}")
        previous_severity = 0
        counter = 1
        escalations = {}
        for event in mop.get_filler('events').group_to_list():
            severity = event.path_filler(('action', 'severity'))
            escalation = severity - previous_severity
            previous_severity = severity
            escalations[counter] = escalation
            counter += 1
        escalations_mop = self.slots_to_mop(slots=escalations, absts={'M-ESCALATION-GROUP'}, mop_type='instance')
        return escalations_mop
    

    def calculate_motives(self, mop):
        print("---------------------------")
        print(f"Calculating motives in {mop}")
        prev_motive = 0
        motives = {}
        counter = 1
        for escalation in mop.get_filler('escalations').group_to_list():
            prev_motive = self.mop_calc({'role': motive, 'escalation': escalation, 'prev_motive': prev_motive})
            motives[counter] = prev_motive
        motives_mop = self.slots_to_mop(slots=motives, absts={'M-MOTIVE-GROUP'}, mop_type='instance')
        return motives_mop


    def adapt_sentence(self, mop):
        old_mop = mop.get_filler('old')
        old_size = old_mop.get_filler('events').group_size()
        old_sentence = old_mop.get_filler('sentence')
        size = mop.get_filler('events').group_size()

        print("---------------------------")
        print(f"Adapting sentence in {old_mop}")

        for old_pos, pos in zip(range(1, old_size + 1), range(1, size + 1)):
            # old_slots = judge.crime_compare_slots(old_mop, old_pos, ['OLD-ACTION', 'OLD-MOTIVE', 'OLD-SEVERITY'])
            # new_slots = judge.crime_compare_slots(mop, pos, ['THIS-ACTION', 'THIS-MOTIVE', 'THIS-SEVERITY'])
            slots = {'role': 'sentence', 'index': size - pos, 'old_sentence': old_sentence}
            slots.update(judge.crime_compare_slots(old_mop, old_pos, ['OLD-ACTION', 'OLD-MOTIVE', 'OLD-SEVERITY']))
            slots.update(judge.crime_compare_slots(mop, pos, ['THIS-ACTION', 'THIS-MOTIVE', 'THIS-SEVERITY']))
            result = judge.mop_calc(slots)
            if result is not None:
                return result
        print("---------------------------")
        print("No major difference found")
        print("Using old sentence")
        return old_sentence
    

    def mop_calc(self, slots):
        instance = self.slots_to_mop(slots=slots, absts={'M-CALC'}, mop_type='instance')
        if instance:
            return instance.get_filler('value')
        return None

    def crime_compare_slots(self, mop, n, roles):
        paths = [('events', n, 'action'), ('motives', n), ('outcomes', n, 'state', 'severity')]
        assert len(roles) == len(paths), "Length of roles and paths must be equal"
        slots = {}
        for role, path in zip(roles, paths):
            slots[role] = mop.path_filler(path)
        return slots


    def adjust_sentence(self, mop):
        print("~---------------------------~")
        print(f"{mop} applied, {mop.get_filler('index')} events from the end")
        self.adjust_function(
            mop.get_filler('old_sentence'),
            mop.get_filler('weight'),
            mop.get_filler('index'),
            mop.get_filler('direction')
        )
    
    def compare_constraint(self, constraint, filler, slots):
        compare_fn = getattr(constraint, 'compare_fn')
        to = self.indirect_filler('to', constraint, slots)
        return compare_fn(filler, to)

    def indirect_filler(self, role, mop, slots):
        filler = mop.get_filler(role)
        return filler.get_filler(slots)

    def adjust_function(self, sentence, weight, index, direction):
        closeness = 0.25 if index <= 1 else 0
        return sentence + (sentence * (weight + closeness) * direction)

    
    def range_constraint(self, constraint, filler, slots):
        '''Assume filler is number that can be compared against the constraint.'''
        below = constraint.role_filler('below')
        above = constraint.role_filler('above')
        if below:
            return filler < below
        if above:
            return filler > above
        return False

sup = romancer.supervisor.singlethreadsupervisor.SingleThreadSupervisor()
env = romancer.environment.singlethreadenvironment.SingleThreadEnvironment(sup, None, None)
judge = Judge(env, env.time)

# create different mops
al = judge.add_mop(mop_name='I-M-AL', absts={'M-ACTOR'}, mop_type='instance')
chuck = judge.add_mop(mop_name='I-M-CHUCK', absts={'M-ACTOR'}, mop_type='instance')
david = judge.add_mop(mop_name='I-M-DAVID', absts={'M-ACTOR'}, mop_type='instance')
randy = judge.add_mop(mop_name='I-M-RANDY', absts={'M-ACTOR'}, mop_type='instance')
ted = judge.add_mop(mop_name='I-M-TED', absts={'M-ACTOR'}, mop_type='instance')
tim = judge.add_mop(mop_name='I-M-TIM', absts={'M-ACTOR'}, mop_type='instance')

# some of these are mops with roles/fillers (aka slots)
# (DEFMOP M-FREQUENCY (M-ROOT) (SEVERITY NIL)) NIL is None
frequency = judge.add_mop(mop_name='M-FREQUENCY', absts={'M-ROOT'}, mop_type='mop', slots={'severity': None})
# (DEFMOP I-M-ONCE (M-FREQUENCY) (SEVERITY 0))
once = judge.add_mop(mop_name='I-M-ONCE', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 0})
# (DEFMOP I-M-SEVERAL-TIMES (M-FREQUENCY) (SEVERITY 1)) (DEFMOP I-M-REPEATEDLY (M-FREQUENCY) (SEVERITY 2))
several_times = judge.add_mop(mop_name='I-M-SEVERAL-TIMES', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 1})
repeatedly = judge.add_mop(mop_name='I-M-REPEATEDLY', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 2})

# (DEFMOP M-MOTIVE (M-ROOT))
judge.add_mop(mop_name='M-MOTIVE', absts={'M-ROOT'}, mop_type='mop')
# (DEFMOP M-JUSTIFIED (M-MOTIVE))
justified = judge.add_mop(mop_name='M-JUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop')
# (DEFMOP M-UNJUSTIFIED (M-MOTIVE))
unjustified = judge.add_mop(mop_name='M-UNJUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop')
# (DEFMOP I-M-SELF-DEFENSE (M-JUSTIFIED) INSTANCE) 
self_defense = judge.add_mop(mop_name='I-M-SELF-DEFENSE', absts={'M-JUSTIFIED'}, mop_type='instance')
# (DEFMOP I-M-RETALIATION (M-UNJUSTIFIED) INSTANCE) 
retaliation = judge.add_mop(mop_name='I-M-RETALIATION', absts={'M-UNJUSTIFIED'}, mop_type='instance')
# (DEFMOP I-M-UNPROVOKED (M-UNJUSTIFIED) INSTANCE)
unprovoked = judge.add_mop(mop_name='I-M-UNPROVOKED', absts={'M-UNJUSTIFIED'}, mop_type='instance')
# (DEFMOP M-CRIME-TYPE (M-ROOT))
crime_type = judge.add_mop(mop_name='M-CRIME-TYPE', absts={'M-ROOT'}, mop_type='mop')
# (DEFMOP I-M-HOMICIDE (M-CRIME-TYPE) INSTANCE)
homicide = judge.add_mop(mop_name='I-M-HOMICIDE', absts={'M-CRIME-TYPE'}, mop_type='instance')

# (DEFMOP M-FIGHT-ACT (M-ACT) (SEVERITY NIL))
fight_act = judge.add_mop(mop_name='M-FIGHT-ACT', absts={'M-ACT'}, mop_type='mop', slots={'severity': None})
# (DEFMOP M-HURT-ACT (M-FIGHT-ACT) (SEVERITY M-RANGE (BELOW 5)))
m_range = judge.add_mop(mop_name='M-RANGE', absts={'M-PATTERN'}, mop_type='mop', slots={'abst_fn':judge.range_constraint})
hurt_act = judge.add_mop(mop_name='M-HURT-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': judge.add_mop(absts={'M-RANGE'}, slots={'below': 5})}) 
# (DEFMOP I-M-SLAP (M-HURT-ACT) (SEVERITY 1))
slap = judge.add_mop(mop_name='I-M-SLAP', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 1})
# (DEFMOP I-M-HIT (M-HURT-ACT) (SEVERITY 1))
hit = judge.add_mop(mop_name='I-M-HIT', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 1})
# (DEFMOP I-M-STRIKE (M-HURT-ACT) (SEVERITY 2))
strike = judge.add_mop(mop_name='I-M-STRIKE', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 2})
# (DEFMOP I-M-KNOCK-DOWN (M-HURT-ACT) (SEVERITY 3)) 
knock_down = judge.add_mop(mop_name='I-M-KNOCK-DOWN', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 3})
# (DEFMOP I-M-SLASH (M-HURT-ACT) (SEVERITY 4))
slash = judge.add_mop(mop_name='I-M-SLASH', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 4})
# (DEFMOP M-WOUND-ACT (M-FIGHT-ACT) (SEVERITY M-RANGE (ABOVE 4)))
wound_act = judge.add_mop(mop_name='M-WOUND-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': judge.add_mop(absts={'M-RANGE'}, slots={'above': 4})})
# (DEFMOP I-M-STAB (M-WOUND-ACT) (SEVERITY 5))
stab = judge.add_mop(mop_name='I-M-STAB', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP I-M-SHOOT (M-WOUND-ACT) (SEVERITY 5))
shoot = judge.add_mop(mop_name='I-M-SHOOT', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP I-M-BREAK-SKULL (M-WOUND-ACT) (SEVERITY 5))
break_skull = judge.add_mop(mop_name='I-M-BREAK-SKULL', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP M-PHYS-STATE (M-STATE) (SEVERITY NIL))
phys_state = judge.add_mop(mop_name='M-PHYS-STATE', absts={'M-STATE'}, mop_type='mop', slots={'severity': None})
# (DEFMOP I-M-BRUISED (M-PHYS-STATE) (SEVERITY 1)) 
bruised = judge.add_mop(mop_name='I-M-BRUISED', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 1})
# (DEFMOP I-M-KNOCKED-DOWN (M-PHYS-STATE) (SEVERITY 2)) 
knocked_down = judge.add_mop(mop_name='I-M-KNOCKED-DOWN', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 2})
# (DEFMOP I-M-CUT (M-PHYS-STATE) (SEVERITY 3))
cut = judge.add_mop(mop_name='I-M-CUT', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 3})
# (DEFMOP I-M-DEAD (M-PHYS-STATE) (SEVERITY 5))
dead = judge.add_mop(mop_name='I-M-DEAD', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP M-OUTCOME (M-ROOT))
outcome = judge.add_mop(mop_name='M-OUTCOME', absts={'M-ROOT'}, mop_type='mop')
# (DEFMOP M-FIGHT-OUTCOME (M-OUTCOME) (STATE M-PHYS-STATE) (ACTOR M-ACTOR))
fight_outcome = judge.add_mop(mop_name='M-FIGHT-OUTCOME', absts={'M-OUTCOME'}, mop_type='mop', slots={'state': phys_state, 'actor': judge.name_mop('M-ACTOR')})
# (DEFMOP M-FIGHT-EVENT (M-EVENT) (ACTION M-FIGHT-ACT)
fight_event = judge.add_mop(mop_name='M-FIGHT-EVENT', absts={'M-EVENT'}, mop_type='mop', slots={'action': fight_act})

# (DEFMOP M-EVENT-GROUP (M-GROUP) (1 M-EVENT))
judge.add_mop(mop_name='M-EVENT-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-EVENT')})
# (DEFMOP M-OUTCOME-GROUP (M-GROUP) (1 M-OUTCOME))
judge.add_mop(mop_name='M-OUTCOME-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-OUTCOME')})
# (DEFMOP M-ESCALATION-GROUP (M-GROUP) (1 M-RANGE))
judge.add_mop(mop_name='M-ESCALATION-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-RANGE')})
# (DEFMOP M-MOTIVE-GROUP (M-GROUP) (1 M-MOTIVE))
judge.add_mop(mop_name='M-MOTIVE-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-MOTIVE')})
# (DEFMOP CALC-ESCALATIONS (M-FUNCTION))
calc_escalations = judge.add_mop(mop_name='CALC-ESCALATIONS', absts={'M-FUNCTION'}, mop_type='mop')
# (DEFMOP CALC-MOTIVES (M-FUNCTION))
calc_motives = judge.add_mop(mop_name='CALC-MOTIVES', absts={'M-FUNCTION'}, mop_type='mop')
# (DEFMOP ADAPT-SENTENCE (M-FUNCTION))
adapt_sentence = judge.add_mop(mop_name='ADAPT-SENTENCE', absts={'M-FUNCTION'}, mop_type='mop')
# (DEFMOP CALC-SENTENCE (M-FUNCTION))
calc_sentence = judge.add_mop(mop_name='CALC-SENTENCE', absts={'M-FUNCTION'}, mop_type='mop')

crime = judge.add_mop(mop_name="M-CRIME", 
                      absts={'M-CASE'}, 
                      mop_type='mop', 
                      slots={'crime_type': crime_type, 
                            'defendant': judge.name_mop('M-ACTOR'), 
                            'victim': judge.name_mop('M-ACTOR'), 
                            'events': judge.name_mop('M-EVENT-GROUP'), 
                            'outcomes': judge.name_mop('M-OUTCOME-GROUP'), 
                            'escalations': judge.calculate_escalations,
                            'motives': judge.calculate_motives,
                            'sentence': judge.adapt_sentence})
# (DEFMOP M-CRIME (M-CASE)
    # (CRIME-TYPE M-CRIME-TYPE)
    # (DEFENDANT M-ACTOR)
    # (VICTIM M-ACTOR)
    # (EVENTS M-EVENT-GROUP)
    # (OUTCOMES M-OUTCOME-GROUP)
    # (ESCALATIONS M-PATTERN (CALC-FN CALC-ESCALATIONS)) 
    # (MOTIVES M-PATTERN (CALC-FN CALC-MOTIVES)) 
    # (SENTENCE M-PATTERN (CALC-FN ADAPT-SENTENCE)))

# (DEFMOP MOTIVE (M-ROLE) INSTANCE)
motive = judge.add_mop(mop_name='MOTIVE', absts={'M-ROLE'}, mop_type='instance')
# (DEFMOP M-CALC (M-ROOT))
judge.add_mop(mop_name='M-CALC', mop_type='mop')
# (DEFMOP M-CALC-MOTIVE (M-CALC)
    # (ROLE MOTIVE) (VALUE NIL))
judge.add_mop(mop_name='M-CALC-MOTIVE', absts={'M-CALC'}, slots={'role': motive, 'value': None}, mop_type='mop')
# (DEFMOP M-CALC-ESCALATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (ABOVE 0))
    # (VALUE I-M-RETALIATION))
judge.add_mop(mop_name='M-CALC-ESCALATION-MOTIVE', absts={'M-CALC-MOTIVE'}, slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'above': 0}) , 'value': retaliation}, mop_type='mop')
# (DEFMOP M-CALC-SELF-DEFENSE-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-UNJUSTIFIED)
    # (VALUE I-M-SELF-DEFENSE))
judge.add_mop(mop_name='M-CALC-SELF-DEFENSE-MOTIVE', absts={'M-CALC-MOTIVE'}, slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'below': 1}), 'prev_motive': unjustified, 'value': self_defense}, mop_type='mop')
# (DEFMOP M-CALC-RETALIATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-JUSTIFIED)
    # (VALUE I-M-RETALIATION))
judge.add_mop(mop_name='M-CALC-RETALIATION-MOTIVE', absts={'M-CALC-MOTIVE'}, slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'above': 0}), 'prev_motive': justified, 'value': retaliation}, mop_type='mop')

judge.add_mop(mop_name='M-COMPARE', absts={'M-PATTERN'}, mop_type='mop', slots={'abst_fn': judge.compare_constraint, 'to': judge.name_mop('M-ROLE'), 'compare_fn': judge.name_mop('M-FUNCTION')})
judge.add_mop(mop_name='M-EQUAL', absts={'M-COMPARE'}, mop_type='mop', slots={'compare_fn': romancer.MOP.equals})
judge.add_mop(mop_name='M-LESS-THAN', absts={'M-COMPARE'}, mop_type='mop', slots={'compare_fn': romancer.MOP.less_than})
sentence = judge.add_mop(mop_name='SENTENCE', absts={'M-ROLE'}, mop_type='instance')
judge.add_mop(mop_name='OLD-SEVERITY', absts={'M-ROLE'}, mop_type='instance')
# (DEFMOP M-ADAPT-SENTENCE (M-CALC)
    # (ROLE SENTENCE)
    # (VALUE M-PATTERN (CALC-FN ADJUST-SENTENCE)))
judge.add_mop(mop_name='M-ADAPT-SENTENCE', absts={'M-CALC'}, mop_type='mop', slots={'role': sentence, 'value': judge.adjust_sentence})


event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': ted, 'object': al, 'freq': once})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': al, 'object': ted, 'freq': once})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': ted, 'object': al, 'freq': repeatedly})
case_1_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3})
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': al})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': ted})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': al})
case_1_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3})
case_1_slots = {'crime_type': homicide, 'defendant': ted, 'victim': al, 'events': case_1_events, 'outcomes': case_1_outcomes, 'sentence': 40}
# case_1 = judge.add_mop(mop_type='instance', absts={'M-CRIME'}, slots=case_1_slots)
judge.judge_case(case_1_slots)

# Define the events
event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': randy, 'object': chuck, 'freq': repeatedly})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': chuck, 'object': randy, 'freq': repeatedly})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': randy, 'object': chuck, 'freq': once})
event_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': chuck, 'object': randy, 'freq': once})
event_5 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': randy, 'object': chuck, 'freq': repeatedly})
# Combine the events into a list
case_2_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3, 4: event_4, 5: event_5})
# Define the outcomes
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': chuck})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': randy})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': chuck})
outcome_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': randy})
outcome_5 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': chuck})
# Combine the outcomes into a list
case_2_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3, 4: outcome_4, 5: outcome_5})
# Define the slots for the case
case_2_slots = {
    'crime_type': homicide,
    'defendant': randy,
    'victim': chuck,
    'events': case_2_events,
    'outcomes': case_2_outcomes,
}
# Create the case MOP instance
# case_2 = judge.add_mop(mop_type='instance', absts={'M-CRIME'}, slots=case_2_slots)
# Judge the case
judge.judge_case(case_2_slots)

# Define the events
event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slap, 'actor': david, 'object': tim, 'freq': several_times})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': tim, 'object': david, 'freq': several_times})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': knock_down, 'actor': david, 'object': tim, 'freq': once})
event_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': tim, 'object': david, 'freq': several_times})
# Combine the events into a list
case_3_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3, 4: event_4})
# Define the outcomes
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': tim})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': david})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': knocked_down, 'actor': tim})
outcome_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': david})
# Combine the outcomes into a list
case_3_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3, 4: outcome_4})
# Define the slots for the case
case_3_slots = {
    'crime_type': homicide,
    'defendant': tim,
    'victim': david,
    'events': case_3_events,
    'outcomes': case_3_outcomes,
}
# Create the case MOP instance
# case_3 = judge.add_mop(mop_type='instance', absts={'M-CRIME'}, slots=case_3_slots)
# Judge the case
judge.judge_case(case_3_slots) 


dot = make_graphviz_graph(judge)
with open("judge.dot", "w") as out_dot:
    out_dot.write(dot)
fmt = "png"
os.system(f"dot -Kdot -T{fmt} -ojudge.{fmt} judge.dot && xdg-open judge.{fmt}")
 #the aggressor is the one that is killed so sentence is less bad and 30 years