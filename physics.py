import math

class Vector(object):
    @staticmethod
    def almostEqual(d1, d2, epsilon=10**-10):
        return (abs(d2 - d1) < epsilon)
    
    @staticmethod
    def zero():
        return Vector(0, 0)

    def __init__(self, x, y):
        #ensure type is always the same
        self.x = float(x)
        self.y = float(y)

    def __eq__(self, other):
        if(isinstance(other, Vector)):
            return (Vector.almostEqual(self.x, other.x) and 
                    Vector.almostEqual(self.y, other.y))
        else:
            return False

    def __add__(self, other):
        if(isinstance(other, Vector)):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            return NotImplemented

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        if(isinstance(other, Vector)):
            return (self.x * other.x) + (self.y * other.y)
        elif(isinstance(other, int) or isinstance(other, float)):
            return Vector(self.x * other, self.y * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        return "Vector(%f, %f)" % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def __sub__(self, other):
        return self + (-1) * other

    def __div__(self, other):
        if(isinstance(other, int)):
            other = float(other)
        if(isinstance(other, float)):
            return Vector(self.x/other, self.y/other)
        else:
            return NotImplemented

    def __iadd__(self, other):
        if(isinstance(other, Vector)):
            self.x += other.x
            self.y += other.y
            return self
        else:
            return NotImplemented

    def __imul__(self, other):
        if(isinstance(other, float) or isinstance(other, int)):
            self.x *= other
            self.y *= other
            return self
        else:
            return NotImplemented

    def getMag(self):
        return math.sqrt(self*self)

    def projOnto(self, u):
        return ((self*u/float(u*u)) * u)

    def getXY(self):
        return (self.x, self.y)

class PhysEnvironment(object):
    #sets up the environment
    #gravity = gravity in m/s**2
    #screenConversion = pixels/meter
    #x0, y0 = origin in screen coordinates
    def __init__(self, gravity, screenConversion, x0, y0):
        self.gravity = gravity
        self.screenConversion = screenConversion

        #vector pointing to the origin of the environment
        self.origin = Vector(x0, y0)

        self.isSimulating = False
        #has the simulation been started once
        self.hasStarted = False 

        self.constraints = []
        self.objects = []

    def start(self):
        if(not self.hasStarted):
            #init all constraints for starting the animation
            for constraint in self.constraints:
                constraint.initForSim()

        self.isSimulating = True
        self.hasStarted = True

    def Pause(self):
        self.isSimulating = False

    #returns the environment coordinates of a screen coordinate
    def getVect(self, x, y):
        position = Vector(x, y)
        position = position - self.origin

        position = position / self.screenConversion

        #invert y coord
        position.y *= -1

        #return a vector since most environment coordinates are vectors
        return position


    #returns the screen coordinates based on the position vector (in meters)
    def getScreenXY(self, position):
        #first, convert meter values to pixel values
        #(don't use inline mulitplication to prevent alias)
        position = position * self.screenConversion

        #flip the sign of the y coordinate so it is in the flipped window 
        #coordinate system and not the cartesian system
        position.y *= -1

        #now, shift to actual values from values based on origin
        position += self.origin

        return position.getXY()

    #add the given object to the environments list
    def add(self, obj):
        if(isinstance(obj, constraint)):
            self.constraints.append(obj)
            return len(self.constraints) - 1
        elif(isinstance(obj, physObject)):
            self.objects.append(obj)
            return len(self.objects) - 1
        else:
            raise Exception("cannot add this thing to the environment")

    def deleteObj(self, obj, objIndex):
        if(isinstance(obj, constraint)):
            #remove from the list by shifting everything else down
            for i in xrange(constraintIndex, len(self.constraints) - 1):
                self.constraints[i] = self.constraints[i+1]
                #update the constraint's index
                self.constraints[i].environIndex = i

            #get rid of the tail element (that is a duplicate)
            del self.constraints[-1]
        elif(isinstance(obj, physObject)):
            

    #update each object in the list, assume each is a physObject
    def update(self, dt):
        #the nodes will ask the springs for force info so only update nodes
        if(self.isSimulating):
            for spring in self.springs:
                spring.update(dt)

            for node in self.nodes:
                #node.accel = node.gravity
                node.update(dt)

            for obj in self.objects:
                obj.update(dt)
        

    #draw all the objects in the simulation
    def draw(self, canvas):
        #draw objects so springs are in front but behind nodes
        for spring in self.springs:
            spring.draw(canvas)

        for node in self.nodes:
            node.draw(canvas)

        for obj in self.objects:
            obj.draw(canvas)

    #returns the object at the given screen coords or none
    def getClickedObj(self, screenX, screenY):
        #look at draw que because that will get the top object
        for node in self.nodes:
            if(node.isClicked(screenX, screenY)):
                return node



class PhysObject(object):
    #creates a physics object
    #position: vector pointing to the objects coordinates in the environment
    #environment: the physics environment that this particle is in relation to
    #isFixed: boolean for if the object is fixed in space
    def __init__(self, position, mass, environment):
        self.environ = environment
        #add the new object to the environment and get the index of the object
        self.index = self.environ.add(self)

        self.position = position
        self.oldPosition = None #will be needed in update func
        self.mass = mass

        self.accel = Vector(0, 0) #no acceleration yet

        #force due to gravity
        self.Fg = Vector(0, -self.environ.gravity) * self.mass
        self.force = Vector(0, 0) #Fg will be added on update

    #add the given force to the object and update the acceleration
    def addForce(self, newForce):
        self.force += newForce
        self.accel = self.force / self.mass

    #update the particle's position based on verlet integration
    def update(self, dt):
        #add force due to gravity
        self.addForce(self.Fg)

        if(self.oldPosition == None):
            #first time updating, calculate new position using regular
            #kinematics equation: x' = x + v*dt + (1/2)*a*dt**2
            #however, initial velocity is zero so v*dt = 0
            newPosition = (self.position + 0.5 * self.accel * dt**2)
        else:
            #calculate new position using verlet
            #x' = 2*x - oldX + a*dt**2
            newPosition = (2 * self.position - self.oldPosition + 
                           self.accel * dt**2)

        self.oldPosition = self.position
        self.position = newPosition
        
        #reset force for next time through the loop
        self.force = Vector.zero()

    #delete the object from the environment
    def delete(self):
        self.environ.deleteObj(self, self.index)

    #draw the object
    def draw(self, canvas):
        #base object just draws a black circle
        r = 5
        (x, y) = self.environ.getScreenXY(self.position)

        canvas.create_oval(x-r, y-r, x+r, y+r, fill="black")

    #check if the object was clicked
    def isClicked(self, x, y):
        #by default the object's can't be clicked
        return False
  
#this class is for constrained particles
class Node(PhysObject):
    def __init__(self, position, mass, environ, isFixed):
        #list of constraints the node is connected to
        self.constraints = []
        #list of indexes of the node in the constraints' node list
        self.constraintIndexes = []

        #if the node is fixed in space
        self.isFixed = isFixed

        super(Node, self).__init__(position, mass, environ)

        #drawing constants
        self.r = 10
        self.color = "black"

    #create a constraint between this node and another node
    def addConstraint(self, constraint, nodeIndex):
        constraintIndex = len(self.constraints)
        self.constraints.append(constraint)
        self.constraintIndexes.append(nodeIndex)
        return constraintIndex

    def removeConstraint(self, constraintIndex, nodeIndex):
        #remove the constraint from the list by shifting everything else down
        for i in xrange(constraintIndex, len(self.constraints) - 1):
            self.constraints[i] = self.constraints[i+1]
            #update the constraint's index
            self.constraints[i].nodeIndexes[nodeIndex] = i

        #get rid of the tail element (that is a duplicate)
        del self.constraints[-1]

    def delete(self):
        #delete all constraints
        i = 0
        while(i < len(self.constraints)):
            #this method will delete the constraint from this node's
            #constraint list so we must watch out for out of bounds accesses
            self.constraints[i].delete()

        super(Node, self).delete() 

    def draw(self, canvas):
        r = self.r
        (x, y) = self.environ.getScreenXY(self.position)

        canvas.create_oval(x-r, y-r, x+r, y+r, fill=self.color)

#does not extend phys object class because it does not act like a physObject
class Constraint(object):
    #node1, node2 are the nodes that the constraint is attached to
    #breakRatio is the fraction of the start len the constraint will move
    #before breaking
    def __init__(self, node1, node2, breakRatio, environ):
        self.environ = environ
        self.environIndex = self.environ.add(self)

        self.nodes = [node1, node2]

        self.nodeIndexes=[self.nodes[i].addConstraint(self, i) 
                          for i in len(self.nodes)]

        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

        self.updateInfo()

        #drawing constants
        self.width = 5

    #initialize for simulation
    def initForSim(self):
        #update rest length (in case nodes were shifted since creation)
        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

    def updateColor(self):
        #base color values
        (red, green, blue) = (0, 255, 0)

        #displaceRatio is 1 or -1 right at breaking
        displaceRatio = self.lenRatio/self.breakRatio

        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        colorChange = abs(displaceRatio) * 255

        if(displaceRatio < 0):
            blue += colorChange
        else:
            red += colorChange

        #reduce the amount of green either way
        green -= colorChange

        self.color = rgbString(red, green, blue)

    def updateInfo(self):
        node1Pos = self.nodes[0].position
        node2Pos = self.nodes[1].position

        #vector going from node 1 to node 2
        self.nodeVect = node2Pos - node1Pos
        self.curLen = self.nodeVect.getMag()

        self.displacement = self.curLen - self.restLen

        self.lenRatio = self.displacement/self.curLen

        self.updateColor()

    def breakConstraint(self):
        #create new nodes on the ends of the constraint so that it 
        #is freed. only create new constraints if there are other constraints
        #on that node or if the node is fixed
        for i in xrange(len(self.nodes)):
            node = self.nodes[i]
            if(len(node.nodes) > 1 or node.isFixed):
                #remove the constraint from the node
                node.removeConstraint(self.nodeIndexes[i], i)

                #make new node (that isn't fixed)
                newNode = Node(node.position, node.mass, self.environ, False)
                #add the constraint to the node
                newNode.addConstraint(self, i)

                self.nodes[i] = newNode

    def resolve(self):
        self.updateInfo()

        if(self.lenRatio > self.breakRatio):
            self.breakConstraint()
        else:
            #shift the nodes to fix the constraints
            if(not self.node1.isFixed):
                self.node1.position += self.nodeVect*0.5*self.lenRatio
            if(not self.node2.isFixed):
                self.node2.position -= self.nodeVect*0.5*self.lenRatio

    def delete(self):
        #remove constraint from nodes
        for i in xrange(len(self.nodes)):
            self.nodes[i].removeConstraint(self.nodeIndexes[i], i)

        #now, remove from environment
        self.environ.delete(self.environIndex)

    def draw(self, canvas):
        #node coordinates
        (x1, y1) = self.environment.getScreenXY(self.node1.position)
        (x2, y2) = self.environment.getScreenXY(self.node2.position)
        canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.width)

