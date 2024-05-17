from context import *
import networkx as nx
import matplotlib.pyplot as plt

import romancer.supervisor.singlethreadsupervisor

class Judge(casebasedreasoner.cbr.CaseBasedReasoner):
    def judge(self, case): # in book, this takes slots, turns them into a mop, and installs it
        instance = self.slots_to_mop(slots=case.slots, mops={crime}, mop_type='instance', must_work=True)
        instance.get_filler('sentence')
        return instance
    

    def judge_case(self, case_mop): # in book, this takes in slot_forms, turns them into slots
        defendant = case_mop.role_filler("defendant")
        print("~---------------------------~")
        print(f"Sentencing {defendant} in {case_mop.mop_name}...")
        instance = self.judge(case_mop)
        sentence = instance.role_filler('sentence')
        print(f"Sentence in {instance} is {sentence}.")


    def calculate_escalations(pattern, mop):
        print("~---------------------------~")
        print(f"Calculating escalations in {mop}")
        previous_severity = 0
        escalations = []
        for event in mop.role_filler('events'):
            severity = mop.path_filler(['action', 'severity'])
            escalation = severity - previous_severity
            previous_severity = severity
            escalations.append(escalation)
        return escalations

    def calculate_motives(pattern, mop):
        pass


    def adapt_sentence(pattern, mop):
        old_mop = mop.get_filler('old')
        old_size = len(old_mop.get_filler('events'))
        old_sentence = old_mop.get_filler('sentence')
        size = len(mop.get_filler('events'))

        print("~---------------------------~")
        print(f"Adapting sentence in {old_mop}")


    def mop_calc(slots):
        pass

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
motive = judge.add_mop(mop_name='M-MOTIVE', absts={'M-ROOT'}, mop_type='mop')
# (DEFMOP M-JUSTIFIED (M-MOTIVE))
justified = judge.add_mop(mop_name='M-JUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop')
# (DEFMOP M-UNJUSTIFIED (M-MOTIVE))
unjustified = judge.add_mop(mop_name='M-UNJUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop')
# (DEFMOP I-M-SELF-DEFENSE (M-JUSTIFIED) INSTANCE) 
self_defense = judge.add_mop(mop_name='M-SELF-DEFENSE', absts={'M-MOTIVE'}, mop_type='mop')
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
hurt_act = judge.add_mop(mop_name='M-HURT-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': romancer.MOP(environment=env, time=env.time, parent=None, mop_name='M-RANGE', absts={'M-ROOT'}, mop_type='mop')})
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
wound_act = judge.add_mop(mop_name='M-WOUND-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': romancer.MOP(environment=env, time=env.time, parent=None, mop_name='M-RANGE', absts={'M-ROOT'}, mop_type='mop')})
# (DEFMOP I-M-STAB (M-WOUND-ACT) (SEVERITY 5))
stab = judge.add_mop(mop_name='I-M-STAB', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP I-M-SHOOT (M-WOUND-ACT) (SEVERITY 5))
shoot = judge.add_mop(mop_name='I-M-SHOOT', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP I-M-BREAK-SKULL (M-WOUND-ACT) (SEVERITY 5))
break_skull = judge.add_mop(mop_name='I-M-BREAK-SKULL', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5})
# (DEFMOP M-STATE (M-ROOT))
# state = judge.add_mop(mop_name='M-STATE', absts={'M-ROOT'}, mop_type='mop')
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
fight_outcome = judge.add_mop(mop_name='M-FIGHT-OUTCOME', absts={'M-OUTCOME'}, mop_type='mop', slots={'state': phys_state, 'actor': romancer.MOP(environment=env, time=env.time, parent=None, mop_name='M-ACTOR', absts={'M-ROOT'}, mop_type='mop')})
# (DEFMOP M-FIGHT-EVENT (M-EVENT) (ACTION M-FIGHT-ACT))
fight_event = judge.add_mop(mop_name='M-FIGHT-EVENT', absts={'M-EVENT'}, mop_type='mop', slots={'action': fight_act})

# (DEFMOP M-EVENT-GROUP (M-GROUP) (1 M-EVENT))
# (DEFMOP M-OUTCOME-GROUP (M-GROUP) (1 M-OUTCOME)) (DEFMOP M-ESCALATION-GROUP (M-GROUP) (1 M-RANGE)) (DEFMOP M-MOTIVE-GROUP (M-GROUP) (1 M-MOTIVE))
# (DEFMOP CALC-ESCALATIONS (M-FUNCTION))
# (DEFMOP CALC-MOTIVES (M-FUNCTION))
# (DEFMOP ADAPT-SENTENCE (M-FUNCTION))
# (DEFMOP CALC-SENTENCE (M-FUNCTION))

crime = judge.add_mop(mop_name="M-CRIME", 
                      absts={'M-CASE'}, 
                      mop_type='mop', 
                      slots={'crime_type': crime_type, 
                             'defendant': judge.name_mop('M-ACTOR'), 
                             'victim': judge.name_mop('M-ACTOR'), 
                             'events': judge.name_mop('M-GROUP'), 
                             'outcomes': judge.name_mop('M-GROUP'), 
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
# (DEFMOP M-CALC (M-ROOT))
# (DEFMOP M-CALC-MOTIVE (M-CALC)
    # (ROLE MOTIVE) (VALUE NIL))
# (DEFMOP M-CALC-ESCALATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (ABOVE 0))
    # (VALUE I-M-RETALIATION))
# (DEFMOP M-CALC-SELF-DEFENSE-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-UNJUSTIFIED)
    # (VALUE I-M-SELF-DEFENSE))
# (DEFMOP M-CALC-RETALIATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-JUSTIFIED)
    # (VALUE I-M-RETALIATION))


# assuming these are  parentless MOPs
# Case 1
event_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_event_1', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': ted, 'object': al, 'freq': once})
event_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_event_2', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': al, 'object': ted, 'freq': once})
event_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_event_3', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': ted, 'object': al, 'freq': repeatedly})
case_1_events = [event_1, event_2, event_3]
outcome_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_1', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': al})
outcome_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_2', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': ted})
outcome_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_3', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': al})
case_1_outcomes = [outcome_1, outcome_2, outcome_3]
case_1_slots = {'crime_type': homicide, 'defendant': ted, 'victim': al, 'events': case_1_events, 'outcomes': case_1_outcomes, 'sentence': 40}
case_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_case_1', absts={'M-CRIME'}, slots=case_1_slots, mop_type='instance')
judge.judge_case(case_1)

# Case 2
event_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c2_event_1', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': randy, 'object': chuck, 'freq': repeatedly})
event_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c2_event_2', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': chuck, 'object': randy, 'freq': repeatedly})
event_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c2_event_3', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': randy, 'object': chuck, 'freq': once})
event_4 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c2_event_4', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': chuck, 'object': randy, 'freq': once})
event_5 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c2_event_5', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': randy, 'object': chuck, 'freq': repeatedly})
case_2_events = [event_1, event_2, event_3, event_4, event_5]
outcome_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_1', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': chuck})
outcome_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_2', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': randy})
outcome_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_3', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': chuck})
outcome_4 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_4', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': randy})
outcome_5 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c1_outcome_5', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': chuck})
case_2_outcomes = [outcome_1, outcome_2, outcome_3, outcome_4, outcome_5]
case_2_slots = {
    'crime_type': homicide,
    'defendant': randy,
    'victim': chuck,
    'events': case_2_events,
    'outcomes': case_2_outcomes,
    'sentence': 50
}
case_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'case_2', absts={'M-CRIME'}, slots=case_2_slots, mop_type='instance')
judge.judge_case(case_2)

# Case 3    
event_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_event_1', absts={'M-FIGHT-EVENT'}, slots={'action': slap, 'actor': david, 'object': tim, 'freq': several_times})
event_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_event_2', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': tim, 'object': david, 'freq': several_times})
event_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_event_3', absts={'M-FIGHT-EVENT'}, slots={'action': knock_down, 'actor': david, 'object': tim, 'freq': once})
event_4 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_event_4', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': tim, 'object': david, 'freq': several_times})
case_3_events = [event_1, event_2, event_3, event_4]
outcome_1 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_outcome_1', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': tim})
outcome_2 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_outcome_2', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': david})
outcome_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_outcome_3', absts={'M-FIGHT-OUTCOME'}, slots={'state': knocked_down, 'actor': tim})
outcome_4 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'c3_outcome_4', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': david})
case_3_outcomes = [outcome_1, outcome_2, outcome_3, outcome_4]
case_3_slots = {
    'crime_type': homicide,
    'defendant': tim,
    'victim': david,
    'events': case_3_events,
    'outcomes': case_3_outcomes,
}
case_3 = romancer.MOP(environment=env, time=env.time, parent=None, mop_name = 'case_3', absts={'M-CRIME'}, slots=case_3_slots, mop_type='instance')
judge.judge_case(case_3)