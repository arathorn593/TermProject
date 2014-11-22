import math

def rgbString(red, green, blue):
        return "#%02x%02x%02x" % (red, green, blue)

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

    #get the value of cosine of the angle b/w the vects
    def getCosTheta(self, other):
        return (self * other)/(self.getMag() * other.getMag())

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

        self.resolveIterations = 10

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

    def getScreenScalar(self, c):
        return c * self.screenConversion

    def getEnvironScalar(self, c):
        return c / float(self.screenConversion)

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
        if(isinstance(obj, Constraint)):
            self.constraints.append(obj)
            return len(self.constraints) - 1
        elif(isinstance(obj, PhysObject)):
            self.objects.append(obj)
            return len(self.objects) - 1
        else:
            raise Exception("cannot add this thing to the environment")

    def deleteObj(self, obj, objIndex):
        if(isinstance(obj, Constraint)):
            objList = self.constraints
        elif(isinstance(obj, PhysObject)):
            objList = self.objects
        else:
            raise Exception("cannot delete this thing from the environment")

        #remove from the list by shifting everything else down
        for i in xrange(objIndex, len(objList) - 1):
            objList[i] = objList[i+1]
            #update the constraint's index
            objList[i].environIndex = i

        #get rid of the tail element (that is a duplicate)
        del objList[-1]

    #update each object in the list, assume each is a physObject
    def update(self, dt):
        if(self.isSimulating):
            for iteration in xrange(self.resolveIterations):
                fixedCollisions = True
                #stop adjusting if all collisions fixed
                #print fixedCollisions
                if(not fixedCollisions): break

                #resolve collisions
                for i in xrange(len(self.objects)):
                    if(isinstance(self.objects[i], Weight)):
                        #resolve colisions with the rest of the list, the 
                        #earlier part was already resolved
                        fixedCollisions = self.objects[i].fixCollisions(              self.objects[i+1:] + 
                                          self.constraints)

                #resolve constraints
                for constraint in self.constraints:
                    constraint.resolve()

            #once constraints and collisions handled, update objects
            for obj in self.objects:
                obj.update(dt)
        

    #draw all the objects in the simulation
    def draw(self, canvas):
        #draw objects so springs are in front but behind nodes
        for constraint in self.constraints:
            constraint.draw(canvas)

        for obj in self.objects:
            obj.draw(canvas)

    #returns the object at the given screen coords or none
    def getClickedObj(self, screenX, screenY):
        #look at objects first, then constraints
        for obj in self.objects:
            if(obj.isClicked(screenX, screenY)):
                return obj

        for constraint in self.constraints:
            if(constraint.isClicked(screenX, screenY)):
                return constraint



class PhysObject(object):
    #creates a physics object
    #position: vector pointing to the objects coordinates in the environment
    #environment: the physics environment that this particle is in relation to
    #isFixed: boolean for if the object is fixed in space
    def __init__(self, position, mass, environment):
        self.environ = environment
        #add the new object to the environment and get the index of the object
        self.environIndex = self.environ.add(self)

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
        self.environ.deleteObj(self, self.environIndex)

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

    #Fix any collisions and return true if any collisions fixed
    def fixCollisions(self, objList):
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

    def update(self, dt):
        if(not self.isFixed):
            super(Node, self).update(dt)

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

    def isClicked(self, clickX, clickY):
        (x, y) = self.environ.getScreenXY(self.position)

        xDist = clickX - x
        yDist = clickY - y
        return (xDist**2 + yDist**2) <= self.r**2

#weights that will drop onto the bridge
class Weight(PhysObject):
    def __init__(self, *args):
        self.r = 15
        self.color = "orange"
        
        super(Weight, self).__init__(*args)

    def fixCollisions(self, objList):
        for obj in objList:
            if(isinstance(obj, Weight)):
                #vector from this object to the other object's center
                centerVect = obj.position - self.position
                dist = centerVect.getMag()

                minDist = (self.environ.getEnvironScalar(obj.r) + 
                           self.environ.getEnvironScalar(self.r))
                if(dist < minDist):
                    #move the two weights so they are not overlapping
                    displacement = dist - (minDist)
                    scaleFactor = displacement / dist

                    self.position += centerVect*0.5*scaleFactor
                    obj.position -= centerVect*0.5*scaleFactor
                    return True

            elif(isinstance(obj, Constraint)):
                minDist = self.environ.getEnvironScalar(self.r)
    
                #vector from the 0th node to the wieght
                nodeWeightVect = self.position - obj.nodes[0].position
                otherNodeWeightVect = self.position - obj.nodes[1].position
                #get updated dist b/w nodes
                constraintVect = (obj.nodes[1].position - 
                                  obj.nodes[0].position)
                reverseConstVect = (obj.nodes[0].position -
                                    obj.nodes[1].position)

                #the value of cosine of the angle b/w the vects
                cosTheta0 = nodeWeightVect.getCosTheta(constraintVect)
                cosTheta1 = otherNodeWeightVect.getCosTheta(reverseConstVect)

                #if the weight is over the constaint
                if(cosTheta0 > 0 and cosTheta1 > 0):
                    projection = nodeWeightVect.projOnto(constraintVect)
                    #vector perpendicular to constraint to center of ball
                    perpVect = projection - nodeWeightVect
                    dist = perpVect.getMag()


                    if(dist < minDist):
                        displacement = dist - minDist
                        scaleFactor = displacement / dist

                        self.position += perpVect*0.5*scaleFactor
                        #obj.nodes[0].addForce(self.mass * Vector(0, -1))
                        #obj.nodes[1].addForce(self.mass * Vector(0, -1))
                        if(not obj.nodes[0].isFixed):
                            obj.nodes[0].position -= perpVect*0.5*scaleFactor
                        if(not obj.nodes[1].isFixed):
                            obj.nodes[1].position -= perpVect*0.5*scaleFactor
                        return True
        #no collisions occured
        return False

    def update(self, dt):
        #first, update as usual
        super(Weight, self).update(dt)

        #now make sure weight is in canvas
        (x, y) = self.position.getXY()
        environR = self.environ.getEnvironScalar(self.r)
        if(y < environR): 
            y = environR
            self.position = Vector(x, y)

    def draw(self, canvas):
        r = self.r
        (cx, cy) = self.environ.getScreenXY(self.position)

        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.color) 

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
                          for i in xrange(len(self.nodes))]

        self.breakRatio = breakRatio
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
            if(len(node.constraints) > 1 or node.isFixed):
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
            if(not self.nodes[0].isFixed):
                self.nodes[0].position += self.nodeVect*0.5*self.lenRatio
            if(not self.nodes[1].isFixed):
                self.nodes[1].position -= self.nodeVect*0.5*self.lenRatio

    def delete(self):
        #remove constraint from nodes
        for i in xrange(len(self.nodes)):
            self.nodes[i].removeConstraint(self.nodeIndexes[i], i)

        #now, remove from environment
        self.environ.delete(self.environIndex)

    def draw(self, canvas):
        #node coordinates
        (x1, y1) = self.environ.getScreenXY(self.nodes[0].position)
        (x2, y2) = self.environ.getScreenXY(self.nodes[1].position)
        canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.width)

    def isClicked(self, screenX, screenY):
        return False

