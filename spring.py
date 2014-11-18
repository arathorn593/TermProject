from vector import Vector
from physObject import PhysObject
from physEnvironment import PhysEnvironment
import math

class Node(PhysObject):
    def __init__(self, *args):
        super(Node, self).__init__(*args)
        
        self.springs = []
        self.r = 15 #pixels
        self.color = "black"
        self.textColor = "white"

        #draw on top of everything
        self.drawPriority = 3
        #update last
        self.updatePriority = 0

    def onSelected(self):
        self.color = "red"

    def onDeselected(self):
        self.color = "black"

    def draw(self, canvas):
        (x, y) = self.environment.getScreenXY(self.position)

        canvas.create_oval(x-self.r, y-self.r, x+self.r, y+self.r, 
                           fill=self.color)
        canvas.create_text(x, y, text=str(len(self.springs)), 
                           fill=self.textColor)

    def addSpring(self, spring):
        self.springs.append(spring)

    def removeSpring(self, spring):
        for i in xrange(len(self.springs)):
            if(self.springs[i] is spring):
                del self.springs[i]
                break

    def isClicked(self, clickX, clickY):
        (x, y) = self.environment.getScreenXY(self.position)

        xDist = clickX - x
        yDist = clickY - y
        return (xDist**2 + yDist**2) < self.r**2
'''
    def update(self, dt):
        if(not self.isFixed):
            self.force = Vector(0, 0)
            for spring in self.springs:
                if spring.node2 is self:
                    displacement = spring.displacement * -1 * spring.unitVector
                else:
                    displacement = spring.displacement * spring.unitVector
                self.force += displacement / (1+dt*spring.k)

            self.force += self.gravity * self.mass

            self.accel = self.force / self.mass

            self.velocity += self.accel * dt
            self.position += self.velocity * dt
'''

class Spring(PhysObject):
    #copied from notes, creates a custom color string from rgb values
    @staticmethod
    def rgbString(red, green, blue):
        return "#%02x%02x%02x" % (red, green, blue)

    #break ratio is the proportion of the length that is the max displacement
    def __init__(self, node1, node2, k, dampRatio, breakRatio, environment):
        #get the center of the spring
        (x, y) = ((node1.position + node2.position) / 2).getXY()

        #springs have no mass and are not fixed since the nodes pull it around
        super(Spring, self).__init__(x, y, 0, False, environment)

        #draw after nodes(3)
        self.drawPriority = 2
        #update first
        self.updatePriority = 3

        #drawing constants
        self.width = 5
        self.color = Spring.rgbString(0, 255, 0)

        #add this spring to the two nodes
        node1.addSpring(self)
        node2.addSpring(self)

        self.node1 = node1
        self.node2 = node2
        self.breakRatio = breakRatio
        self.broken = False

        #total node mass is the ammount of free moving mass on the spring
        self.totalNodeMass = self.node1.mass if not self.node1.isFixed else 0
        self.totalNodeMass += self.node2.mass if not self.node2.isFixed else 0

        #spring constant
        self.k = k

        #set up damping
        self.dampRatio = dampRatio
        #calculate the damping constant from the requested damp ratio
        #this is a standard formulat used in physics
        self.dampConst = (self.dampRatio * 2 * 
                          math.sqrt(self.totalNodeMass * self.k))

        if(self.environment.isSimulating):
            self.initForSim()

    def initForSim(self):
        #the spring starts out not stretched
        #vector from node2 to node1
        self.nodeVect = self.node1.position - self.node2.position
        self.startLength = self.nodeVect.getMag()
        self.curLength = self.startLength
        self.force = 0

        self.displacement = 0
        self.oldDisplacement = 0
        self.maxDisplacement = self.startLength * self.breakRatio
        #update the displacement, unitVector, etc
        self.updateInfo(0) #dt = 0

    def breakSpring(self):
        #create new nodes that arnt fixed
        #don't make new nodes if the nodes have only this spring
        if(len(self.node1.springs) > 1 or self.node1.isFixed):
            (x1, y1) = self.node1.position.getXY()
            mass1 = self.node1.mass
            self.node1.removeSpring(self)
            self.node1 = Node(x1, y1, mass1, False, self.environment)

        if(len(self.node2.springs) > 1 or self.node2.isFixed):
            (x2, y2) = self.node2.position.getXY()
            mass2 = self.node2.mass
            self.node2.removeSpring(self)
            self.node2 = Node(x2, y2, mass2, False, self.environment)

    def updateColor(self):
        if(self.broken): 
            self.color = "black"
            return

        (red, green, blue) = (0, 255, 0)

        #divide by break ratio so that the max color dif is before change
        displaceRatio = self.displacement/self.maxDisplacement
        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        colorChange = abs(displaceRatio) * 255

        if(displaceRatio < 0):
            blue += colorChange
        else:
            red += colorChange

        green -= colorChange

        self.color = Spring.rgbString(red, green, blue)

    #update spring properties: displacement, curLength, unitVector, force
    def updateInfo(self, dt):
        self.nodeVect = self.node1.position - self.node2.position
        self.curLength = (self.nodeVect).getMag()

        self.oldDisplacement = self.displacement
        self.displacement = self.curLength - self.startLength

        if(abs(self.displacement) > self.maxDisplacement):
            self.broken = True
            self.breakSpring()
        else:
            self.broken = False

        #always points from node2 to node1
        if(self.curLength == 0): self.unitVector = Vector(0, 0)
        else:
            self.unitVector = (self.nodeVect)/self.curLength

        #Hooke's law. muliply unitvector so force is a vector in the right dir
        self.force = -1*self.k*self.displacement*self.unitVector

        #factor in spring damping
        massVelocity = self.node1.velocity + self.node2.velocity * -1
        #velocity of the spring length changing
        if(dt == 0): self.lenVelocity = 0
        else:
            self.lenVelocity = (self.displacement - self.oldDisplacement) / dt 

        self.dampForce = -self.dampConst * self.lenVelocity * self.unitVector
        self.force += self.dampForce

        self.updateColor()

    #overrides update method of super class
    def update(self, dt):
        #update all other updateInfo
        self.updateInfo(dt)

        #add force to each node
        #since unitVector points toward node1, the force on node2 needs to have
        #it's sign flipped.
        self.node1.force += self.force
        self.node2.force -= self.force

    def draw(self, canvas):
        #node1 coordinates
        (x1, y1) = self.environment.getScreenXY(self.node1.position)
        (x2, y2) = self.environment.getScreenXY(self.node2.position)
        canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.width)

def testSpring():
    height = 750
    screenConversion = 250 #pixels/meter

    gravity = 10 #m/s**2
    
    #create an environment with the origin in the lower left
    environment = PhysEnvironment(gravity, screenConversion,
                                       0, height)

    node1Mass = 10 #kg
    node2Mass = 10
    springK = 200

    #node 1 will be fixed
    node1 = Node(2, 0, node1Mass, True, environment)

    node2 = Node(1, 0, node2Mass, False, environment)

    spring = Spring(node1, node2, springK, 
                         environment)

    environment.addObj(spring)
    environment.addObj(node1)
    environment.addObj(node2)

    node2.position = Vector(0, 0)

    spring.updateInfo()

    assert(spring.displacement == 1)
    assert(spring.unitVector == Vector(1, 0))
    assert(spring.curLength == 2)
    assert(spring.nodeVect == Vector(2, 0))
    assert(spring.force == Vector(-200, 0))

    spring.update(0)

    assert(node1.force.x == -200)
    assert(node2.force.x == 200)

#testSpring()
