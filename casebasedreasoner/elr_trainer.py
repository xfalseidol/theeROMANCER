from escalationladderreasoner import EscalationLadderReasoner
from simulation_scenario import run
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment


env = SingleThreadEnvironment(None, None, None)
# make CB-ELR
ELR = EscalationLadderReasoner(env, env.time)

# train it
training_runs = 2
for i in range(training_runs):
    print(f"Training Run {i + 1}:")
    run(ELR)
    print()

# serialize it
ELR.serialize("trainedELR.pkl")

# create a new CB-ELR and load the old one's memories into it
new_ELR = EscalationLadderReasoner(env, env.time, load_memory_from="trainedELR.pkl")
print(new_ELR.mops)
