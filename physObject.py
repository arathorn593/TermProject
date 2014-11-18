from vector import Vector
from vector import PhysState
from vector import PhysDerivatives

class PhysObject(object):
    #velocity is a vector
    def __init__(self, x, y, mass, isFixed, environment, velocity=(0,0)):
        if(isinstance(velocity, tuple) or isinstance(velocity, list)):
            #convert velocity list to vector if need be
            velocity = Vector(*velocity)

        self.position = Vector(x, y)

        self.environment = environment

        self.gravity = Vector(0, -self.environment.gravity)

        self.mass = mass
        self.velocity = velocity
        self.force = self.gravity * self.mass
        if(self.mass != 0):
            self.accel = self.force/self.mass
        else:
            self.accel = Vector(0, 0)

        self.isFixed = isFixed

        #default to lowest drawing and updating priority
        self.drawPriority = 0
        self.updatePriority = 0

        #addobject to the environment
        self.index = self.environment.addObj(self) #index in the environ list

    def evaluate(self, initial, dt, derivatives):
        newPos = initial.pos + derivatives.dx * dt
        newVelocity = initial.velocity + derivatives.dv * dt

        newState = PhysState(newPos, newVelocity)

        newDx = newState.velocity
        newDv = self.getAccel(newState, dt)

        return PhysDerivatives(newDx, newDv)

    def getAccel(self, state, dt):
        return self.force / self.mass if self.mass != 0 else 0

    def update(self, dt):
        if(self.isFixed or self.mass == 0):
            self.force = Vector(0, 0)
        else:
            '''
            state = PhysState(self.position, self.velocity)
            a = self.evaluate(state, 0, 
                              PhysDerivatives(Vector(0, 0), Vector(0, 0)))
            b = self.evaluate(state, dt * 0.5, a)
            c = self.evaluate(state, dt * 0.5, b)
            d = self.evaluate(state, dt, c)

            dxdt = (a.dx + 2*b.dx + 2*c.dx + d.dx) / 6.0
            dvdt = (a.dv + 2*b.dv + 2*c.dv + d.dv) / 6.0

            self.position += dxdt * dt
            self.velocity += dvdt * dt

            self.force = Vector(0, 0)
            '''
            self.position += self.velocity * dt + 0.5 * self.accel * dt**2

            #add gravity to force
            self.force += self.gravity * self.mass

            oldAccel = self.accel

            #update accel
            self.accel = self.force / self.mass

            #update velocity
            self.velocity += 0.5*(self.accel + oldAccel) * dt 

            #reset force for the next loop through
            self.force = Vector(0, 0)

    def draw(self, canvas):
        r = 10
        (x, y) = self.environment.getScreenXY(self.position)

        canvas.create_oval(x-r, y-r, x+r, y+r, fill="black")

    def isClicked(self, x, y):
        #by default the object's can't be clicked
        return False

    def onSelected(self):
        #by default do nothing when selected
        pass

    def onDeselected(self):
        #do nothing when deselected
        pass

    #where any special instructions for starting the simulation should go
    def initForSim(self):
        pass

    def __str__(self):
        (x, y) = self.position.getXY()

        return "%s(%f, %f)" % (type(self).__name__, x, y)
        