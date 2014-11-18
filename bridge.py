from physEnvironment import PhysEnvironment
from physObject import PhysObject
from vector import Vector

class Joint(object):
    def __init__(self, position, mass, environment):
        self.pos = position
        self.velocity = Vector(0, 0)
        self.acceleration = 0
        self.mass = mass
        self.environment = environment

    def getDerivatives

class Beam(physObject):

class Bridge(PhysObject):
    def __init__(self, joints, beams):

