from physEnvironment import PhysEnvironment
from physObject import PhysObject
from vector import *

class Joint(object):
    def __init__(self, position, mass, environment):
        self.pos = position
        self.velocity = Vector(0, 0)
        self.acceleration = 0
        self.mass = mass
        self.environment = environment
        #list of joints
        self.connections = []
        self.k = 2000
        self.index = self.environment.addObj(self)

    def getNewState(self, dt, derivatives):
        (dx, dv) = (derivatives.dx, derivatives.dv)
        newPos = self.pos + dx * dt
        newVel = self.velocity + dv * dt

        return physState(newPos, newVel)

    def getDerivatives(self, dt, states):
        dx = states[self.index].velocity

        force = 0
        for joint in self.connections:
            

class Beam(physObject):

class Bridge(PhysObject):
    def __init__(self, joints, beams):

