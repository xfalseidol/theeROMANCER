import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
os.chdir('demo/hotline')
import context
import casebasedreasoner
import romancer.environment
import romancer.supervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor