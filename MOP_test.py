from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from casebasedreasoner.mop import MOP
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from romancer.environment.location import GeographicLocation
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
import casebasedreasoner.cbr

sup = SingleThreadSupervisor()
env = SingleThreadEnvironment(supervisor=sup, disposition_tree=None, perception_engine=None) # env is only needed to initialize TestImprovedRomancerObject

# create case-based reasoner
cbr_agent = casebasedreasoner.cbr.CaseBasedReasoner(env, env.time) # this tests initialization

# test add_mop

# test get_sibling

# advance time, test move the mop we added up/down

# test get_sibling

# test rewind




# build a simple model of planes in combat
# assume: the CBR agent wants to worry the case that a 
# plane piloted by a foreign pilot with weapons is heading toward him

# m_root = MOP(env, env.time, parent=reasoner, mop_name="M-ROOT", mop_type='abstract')

# m_pilot = MOP(env, env.time, parent=reasoner, mop_name="M-PILOT", mop_type='abstract')
# m_pilot.link_abst(m_root)
# m_weapons = MOP(env, env.time, parent=reasoner, mop_name="M-WEAPONS", mop_type='abstract')
# m_weapons.link_abst(m_root)
# m_direction = MOP(env, env.time, parent=reasoner, mop_name="M-DIRECTION", mop_type='abstract')
# m_direction.link_abst(m_root)
# m_plane = MOP(env, env.time, parent=reasoner, mop_name="M-PLANE", mop_type='abstract', slots={"Pilot": m_pilot, "Weapons": m_weapons, "Heading": m_direction})
# m_plane.link_abst(m_root)
# # m_root.spec = {m_pilot, m_weapons, m_plane, m_direction}
# print(m_root.spec)

# i_m_missiles = MOP(env, env.time, parent=reasoner, mop_name="I-M-MISSILES", abst={m_weapons}, slots={"Number of Missiles": 5})
# i_m_red_pilot = MOP(env, env.time, parent=reasoner, mop_name="I-M-REDPILOT", abst={m_pilot})
# i_m_heading = MOP(env, env.time, parent=reasoner, mop_name="I-M-HEADING", abst={m_direction})
# i_m_plane = MOP(env, env.time, parent=reasoner, mop_name="I-M-BZERO", abst={m_plane}, slots={"Pilot": i_m_red_pilot, "Weapons": i_m_missiles})

# we should probably have an MOP "package" with helper functions that makes the creation of "boiler plate" objects simpler
# like, I define all of my "1st order" (directly below root) and call some helper that automatically connects them to the
# root and the root to them

# instance MOPs should perhaps be subclasses of abstract MOPs