from romancer import *
from supervisor import *
from supervisor import *
from environment import *

print("Begin")
sup = SingleThreadSupervisor()
env = SingleThreadEnvironment(sup, None, None)
cbr_agent = cbr.CaseBasedReasoner(env, env.time)

cbr_agent.add_mop(mop_name='M-ENEMY-DETECTED', absts={'M-EVENT'})
cbr_agent.add_mop(mop_name='I-M-E1-DETECTED', absts={'M-ENEMY-DETECTED'}, mop_type='instance')
cbr_agent.add_mop(mop_name='I-M-E2-DETECTED', absts={'M-ENEMY-DETECTED'}, mop_type='instance')

mop = cbr_agent.mops['I-M-E1-DETECTED']
cbr_agent.get_sibling(None, mop)

cbr_agent.add_mop(mop_name='M-FRIENDLY-DETECTED', absts={'M-EVENT'})
friendly1_detected = cbr_agent.add_mop(mop_name="I-M-F1-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
friendly2_detected = cbr_agent.add_mop(mop_name="I-M-F2-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
# advance time
cbr_agent.forward_simulation(5.0)
# make changes to the agent
cbr_agent.remove_mop('I-M-F2-DETECTED')
friendly3_detected = cbr_agent.add_mop(mop_name="I-M-F3-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
cbr_agent.rewind(4.0)
cbr_agent