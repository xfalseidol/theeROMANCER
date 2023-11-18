from typing import NamedTuple
from environment.object import RomancerObject

# Introducing the B-0: a plane that really, really sucks

class BZero(RomancerObject):

    def __init__(self, environment, time, location, speed, ecm=False):
        super().__init__(environment, time) # set up standard object slots
        
        self.location = location # one-dimensional, this plane can't steer!
        self.speed = speed # speed along trajectory in km/hr
        self.ecm = ecm # electronic countermeasures that can confound adversary radar

        self.dispositions = [self.environment.disposition_tree.set_disposition(self)]

        self.dispatch_table = {} # dict of functions for processing messages
