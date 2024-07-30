import context
from romancer.agent.escalationladderreasoner import EscalationLadder, EscalationLadderRung, EscalationLadderReasoner
from romancer.agent.amygdala import Amygdala, UpdateAmygdalaParameters
from romancer.agent.personlikeagent import push_personlike_action, DraftROMANCERMessage

def rational_scenario(env):
    red_fight_weight = 1.0
    red_flight_weight = 1.0
    red_freeze_weight = 1.0
    red_initial_fight = 0.0
    red_initial_flight = 0.0
    red_initial_freeze = 0.0
    red_initial_pbf = 0.0001
    red_pbf_halflife = 100.0
    red_max_pbf = 1.0
    red_response_threshhold = 1.1

    # Step 3.1.2: 
    red_amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)

    # Intended Schedule: just like normal_stress_scenario, but no fight escalation/flight de-escalation/freezing should occur
    rung1 = EscalationLadderRung(match_attributes = {'event_type': 'deployed', 'weapon': '2'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [test_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Calm")

    rung2 = EscalationLadderRung(match_attributes = {'event_type': 'fired', 'weapon': '3'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [low_stress_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Irritated")
    # While Herman Kahn's escalation ladder had 44 rungs, for our purposes here far fewer are needed, as we only need a subsection of a full ladder appropriate for the situation decribed in the Command PE model run used to generate the watchlist

    rung3 = EscalationLadderRung(match_attributes = {'event_type': 'hit', 'weapon': '4'},
                                blue_actions = [],
                                red_actions = [high_stress_freeze_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Annoyed")

    rung4 = EscalationLadderRung(match_attributes = {'weapon': '5'},
                                blue_actions = [],
                                red_actions = [high_stress_fight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Agitated")

    rung5 = EscalationLadderRung(match_attributes = {'weapon': '6'},
                                blue_actions = [],
                                red_actions = [high_stress_flight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Angry")

    red_escalation_ladder = EscalationLadder([rung1, rung2, rung3, rung4, rung5])
    red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    red_planned_actions = None # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
    red_actions_taken = None # change to give Red NCA history of actions taken
    red_digested_percepts = None # change to give Red NCA history of digested percepts
    red_reasoner = EscalationLadderReasoner(environment = env, time = env.time, escalation_ladder = red_escalation_ladder, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)
    return red_amygdala, red_reasoner

def normal_stress_scenario(env):
    red_fight_weight = 1.0
    red_flight_weight = 1.0
    red_freeze_weight = 1.0
    red_initial_fight = 0.0
    red_initial_flight = 0.0
    red_initial_freeze = 0.0
    red_initial_pbf = 0.0001
    red_pbf_halflife = 100.0
    red_max_pbf = 1.0
    red_response_threshhold = 0.7

    # Step 3.1.2: 
    red_amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)

    # agents start on rung1:
    ## first watchlist item escalates to rung2, stressing out agent just a bit
    ## second watchlist item escalates to rung3, stressing out agent to point of freezing
    ## third watchlist item should escalate to rung4, but doesn't since agent is frozen
    ## agent destresses enough to unfreeze and escalates to rung4, which stresses agent out to point of fighting
    ## agent automatically escalates to rung5 despite no match, due to fight stress response
    ## rung5 stresses agent out to point of flight and agent attempts to deescalate

    # Intended Schedule:
    ## 600:     New WatchlistItem causes agent to escalate from Rung1 to Rung2
    ## 600.5:   Agent takes low_stress_action
    ## 1800:    New WatchlistItem causes agent to escalate from Rung2 to Rung3
    ## 1800.3:  Agent takes high_stress_freeze_action, freezes
    ## 1810:    New WatchlistItem should cause agent to escalate from Rung3 to Rung4, doesn't happen due to freeze
    ## 1819.57: Agent should un-freeze and escalate
    ## 1819.67: Agent takes high_stress_fight_action, escalates from Rung4 to Rung5
    ## 1825.67: Agent takes high_stress_flight_action, deescalates from Rung5 to Rung4
    ## 1829.67: Agent takes deescalate_action, reducing its stress level

    rung1 = EscalationLadderRung(match_attributes = {'event_type': 'deployed', 'weapon': '2'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [test_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Calm")

    rung2 = EscalationLadderRung(match_attributes = {'event_type': 'fired', 'weapon': '3'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [low_stress_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Irritated")
    # While Herman Kahn's escalation ladder had 44 rungs, for our purposes here far fewer are needed, as we only need a subsection of a full ladder appropriate for the situation decribed in the Command PE model run used to generate the watchlist

    rung3 = EscalationLadderRung(match_attributes = {'event_type': 'hit', 'weapon': '4'},
                                blue_actions = [],
                                red_actions = [high_stress_freeze_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Annoyed")

    rung4 = EscalationLadderRung(match_attributes = {'weapon': '5'},
                                blue_actions = [],
                                red_actions = [high_stress_fight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Agitated")

    rung5 = EscalationLadderRung(match_attributes = {'weapon': '6'},
                                blue_actions = [],
                                red_actions = [high_stress_flight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Angry")

    red_escalation_ladder = EscalationLadder([rung1, rung2, rung3, rung4, rung5])
    red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    red_planned_actions = None # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
    red_actions_taken = None # change to give Red NCA history of actions taken
    red_digested_percepts = None # change to give Red NCA history of digested percepts
    red_reasoner = EscalationLadderReasoner(environment = env, time = env.time, escalation_ladder = red_escalation_ladder, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)
    return red_amygdala, red_reasoner

def sensitive_amygdala_scenario(env):
    red_fight_weight = 1.0
    red_flight_weight = 1.0
    red_freeze_weight = 1.0
    red_initial_fight = 0.0
    red_initial_flight = 0.0
    red_initial_freeze = 0.0
    red_initial_pbf = 0.0001
    red_pbf_halflife = 100.0
    red_max_pbf = 1.0
    red_response_threshhold = 0.2

    # Step 3.1.2: 
    red_amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)
    deescalate_params = UpdateAmygdalaParameters(-0.1, 0, 0, 0)
    deescalate_action = (4, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), deescalate_params)

    # Intended Schedule: like normal_stress_scenario, but the sensitive agent: freezes longer, escalates from fight more, and de-escalates all the way
    ## 600:     New WatchlistItem causes agent to escalate from Rung1 to Rung2
    ## 600.5:   Agent takes low_stress_action
    ## 1800:    New WatchlistItem causes agent to escalate from Rung2 to Rung3
    ## 1800.3:  Agent takes high_stress_freeze_action, freezes
    ## 1810:    New WatchlistItem should cause agent to escalate from Rung3 to Rung4, doesn't happen due to freeze
    ## 1819.57: Agent should un-freeze and escalate
    ## 1819.67: Agent takes high_stress_fight_action, escalates from Rung4 to Rung5
    ## 1825.67: Agent takes high_stress_flight_action, deescalates from Rung5 to Rung4
    ## 1829.67: Agent takes deescalate_action, reducing its stress level

    rung1 = EscalationLadderRung(match_attributes = {'event_type': 'deployed', 'weapon': '2'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [test_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Calm")

    rung2 = EscalationLadderRung(match_attributes = {'event_type': 'fired', 'weapon': '3'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [low_stress_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Irritated")
    # While Herman Kahn's escalation ladder had 44 rungs, for our purposes here far fewer are needed, as we only need a subsection of a full ladder appropriate for the situation decribed in the Command PE model run used to generate the watchlist

    rung3 = EscalationLadderRung(match_attributes = {'event_type': 'hit', 'weapon': '4'},
                                blue_actions = [],
                                red_actions = [high_stress_freeze_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Annoyed")

    rung4 = EscalationLadderRung(match_attributes = {'weapon': '5'},
                                blue_actions = [],
                                red_actions = [high_stress_fight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Agitated")

    rung5 = EscalationLadderRung(match_attributes = {'weapon': '6'},
                                blue_actions = [],
                                red_actions = [high_stress_flight_action],
                                blue_deescalation_actions = [],
                                red_deescalation_actions = [deescalate_action],
                                name = "Angry")

    red_escalation_ladder = EscalationLadder([rung1, rung2, rung3, rung4, rung5])
    red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    red_planned_actions = None # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
    red_actions_taken = None # change to give Red NCA history of actions taken
    red_digested_percepts = None # change to give Red NCA history of digested percepts
    red_reasoner = EscalationLadderReasoner(environment = env, time = env.time, escalation_ladder = red_escalation_ladder, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)
    return red_amygdala, red_reasoner


test_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0, 0, 0, 0))
low_stress_params = UpdateAmygdalaParameters(0.1, 0.2, 0.3, 0.4)
low_stress_action = (0.5, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), low_stress_params)
high_stress_freeze_params = UpdateAmygdalaParameters(0.8, 0.6, 0.7, 0.8)
high_stress_freeze_action = (0.3, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_freeze_params)
high_stress_fight_params = UpdateAmygdalaParameters(0.8, 2.0, 0.1, 0.1)
high_stress_fight_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_fight_params)
high_stress_flight_params = UpdateAmygdalaParameters(0.8, 0.2, 3.0, 0.3)
high_stress_flight_action = (20, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_flight_params)
deescalate_params = UpdateAmygdalaParameters(-0.2, 0, 0, 0)
deescalate_action = (4, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), deescalate_params)

scenarios = [rational_scenario, normal_stress_scenario, sensitive_amygdala_scenario]
scenario_names = ["Rational", "Normal", "Sensitive"]