import math

def rgbString(red, green, blue):
        return "#%02x%02x%02x" % (red, green, blue)

#2D vector class
class Vector(object):
    #for checking equality of floats
    @staticmethod
    def almostEqual(d1, d2, epsilon=10**-10):
        return (abs(d2 - d1) < epsilon)
    
    #returns the zero Vector
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

    #get the length of the vector
    def getMag(self):
        return math.sqrt(self*self)

    #return the projection of the vector onto u
    def projOnto(self, u):
        return ((self*u/float(u*u)) * u)

    #get the XY coordinates of the vector
    def getXY(self):
        return (self.x, self.y)

    #get the value of the cosine of the angle b/w the vects
    def getCosTheta(self, other):
        return (self * other)/(self.getMag() * other.getMag())

#this class keeps track of all aspects of the physics environment
#objects, converting units, updating objects, collisions, etc. 
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

        self.constraintIndexes = []
        self.weightIndexes = []
        self.otherIndexes = []
        self.objects = []

        self.resolveIterations = 5
        self.debug = False

    #start the simulation (or restart it)
    def start(self):
        if(not self.hasStarted):
            #init all constraints for starting the animation
            for index in self.constraintIndexes:
                self.objects[index].initForSim()

        self.isSimulating = True
        self.hasStarted = True

    #pause the simulation
    def pause(self):
        self.isSimulating = False

    #returns the environment coordinates (in vector form)of a screen coordinate
    def getVect(self, x, y):
        position = Vector(x, y)
        position = position - self.origin

        position = position / self.screenConversion

        #invert y coord
        position.y *= -1

        #return a vector since most environment coordinates are vectors
        return position

    #converts a single environment scalar (c) from meters to pixels
    def getScreenScalar(self, c):
        return c * self.screenConversion

    #converts a single screen scalar(c) from pixels, to meters
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
        #add to the list of objects
        self.objects.append(obj)
        #get the objects index in the list
        index = len(self.objects) - 1

        #add the index to specialized lists if needed
        if(isinstance(obj, Constraint)):
            self.constraintIndexes.append(index)
        elif(isinstance(obj, Weight)):
            self.weightIndexes.append(index)
        else:
            self.otherIndexes.append(index)

        #return the index so the object can keep track of its position
        return index

    #delete the object from the environment
    def deleteObj(self, obj, objIndex):
        #remove from the list by shifting everything else down
        for i in xrange(objIndex, len(self.objects) - 1):
            self.objects[i] = self.objects[i+1]
            #update the constraint's index
            self.objects[i].environIndex = i

        #get rid of the tail element (that is a duplicate)
        del self.objects[-1]

        #recalculate indexes
        self.constraintIndexes = []
        self.weightIndexes = []
        self.otherIndexes = []
        for i in xrange(len(self.objects)):
            if(isinstance(self.objects[i], Constraint)):
                self.constraintIndexes.append(i)
            elif(isinstance(self.objects[i], Weight)):
                self.weightIndexes.append(i)
            else:
                self.otherIndexes.append(i)

    #get a list of all edges of all (collidable) objects 
    #edges in the form (xval, index, "R"/"L")
    def generateEdgeList(self):
        edgeList = []

        for obj in self.objects:
            edgeList += obj.getEdges()

        edgeList.sort()
        return edgeList

    #returns a list of the nodes left  of the screens edge that are connected
    #to a collidable constraint
    def getLeftCollidableNodes(self, leftScreenEdge):
        leftNodes = []
        for obj in self.objects:
            if(isinstance(obj, Node)):
                x = obj.position.getXY()[0]
                if(x < leftScreenEdge):
                    #only assign if there is a collidable constraint on the obj
                    for constraint in obj.constraints:
                        if(constraint.isCollidable):
                            leftNodes.append(obj)
                            break
        return leftNodes

    #is there a path from the given constraint to the right side
    def isCovered(self, node, rightSide, seen=None, depth=0):
        if(seen == None):
            seen = set()

        if(node.position.getXY()[0] >= rightSide):
            #the node is past the right side.
            return True
        elif(node in seen):
            #already been to this node. 
            return False
        else:
            seen.add(node)
            #check all collidable constraints
            for constraint in node.constraints:
                #get the other node in the constraint
                if(constraint.nodes[0] is node):
                    newNode = constraint.nodes[1]
                else:
                    newNode = constraint.nodes[0]
                
                if(constraint.isCollidable and 
                   self.isCovered(newNode, rightSide, seen, depth+1)):
                    return True

            return False                    

    #checks if the bridge covers the gap (checks if there is a path of
    #collidable(bed or land beams) that spans the entire screen
    def doesBridgeCover(self, screenWidth):
        #find the left and right edges of the screen in meter units
        leftEdge = self.getEnvironScalar(self.origin.getXY()[0])

        rightEdge = leftEdge + self.getEnvironScalar(screenWidth)

        #list of all collidable constraints with (leftX, rightX)
        leftNodes = self.getLeftCollidableNodes(leftEdge)

        for node in leftNodes:
            if(self.isCovered(node, rightEdge)):
                return True
        return False

    #I came up with an initial rough version of this algorith, but
    # my roomate helped me get it to this point
    #resolves all collisions in the environment but only checks when two 
    #objects are above one another in order to improve efficiency
    def resolveCollisions(self):
        #list of tuples in the form: (xVal, index, "R"/"L" (right or left))
        #note: xval is in environ coordinates
        edgeList = self.generateEdgeList()

        #the list of objects that could be colliding
        #when adding an obj to this list the algorithm resolves all collisions
        #with the objects in the list and the new object. That means that it 
        #can assume none of the objects in the list are colliding
        objList = []

        #go through all edges and only check collisions when 2+ objects
        for edge in edgeList:
            (x, i, side) = edge

            if(side == "L"):
                #left side, add it to the list
                newObj = self.objects[i]

                #only need to check collisions if the list isn't empty
                if(len(objList) > 0):
                    #if the new obj is a weight, just pass it the list of obj
                    if(isinstance(newObj, Weight)):
                        newObj.fixCollisions(objList)
                    #if it is not a weight, compare all weights in the objList
                    #with it
                    else:
                        for i in xrange(len(objList)):
                            if(isinstance(objList[i], Weight)):
                                objList[i].fixCollisions([newObj])
                #add the object to the list after collisions resolved
                objList.append(newObj)
            #if it is the right side, just remove it
            elif(side == "R"):
                for index in xrange(len(objList)):
                    if(objList[index].environIndex == i):
                        objList.pop(index)
                        break

    #resolve all collisisons and constraints in the system
    def resolveCollisionsConstraints(self):
        #resolve multiple times each loop to approx best resolution
        for iteration in xrange(self.resolveIterations):
                #fixedCollisions = True

                self.resolveCollisions()

                #resolve constraints
                for index in self.constraintIndexes:
                    self.objects[index].resolve()

    #update each object in the list, assume each is a physObject
    #returns true if a constraint broke, false otherwise
    def update(self, dt, width, height):
        if(self.isSimulating):
            self.resolveCollisionsConstraints()

            objToDelete = []
            #once constraints and collisions handled, update objects
            for index in self.otherIndexes + self.weightIndexes:
                self.objects[index].update(dt, width, height)
                if(not self.objects[index].inScreen):
                    #check if the object exited the bottom
                    (x, y) = self.getScreenXY(self.objects[index].position)

                    #delete the object either way
                    if(not isinstance(self.objects[index], Node)):
                        objToDelete.append(self.objects[index])

            for obj in objToDelete:
                obj.delete()

            #check for broken constraints
            for index in self.constraintIndexes:
                isBroken = self.objects[index].checkForBreak()
                if(isBroken and isinstance(self.objects[index], BridgeBed)):
                    return True

            #no objects broken
            return False
    
    #draw all the objects in the simulation
    def draw(self, canvas, debug=False):
        #draw objects so constraints are in front but behind nodes
        for index in self.weightIndexes:
            self.objects[index].draw(canvas, debug)

        for index in self.constraintIndexes:
            self.objects[index].draw(canvas, debug)

        for index in self.otherIndexes:
            self.objects[index].draw(canvas, debug)

    #returns the object at the given screen coords or none
    def getClickedObj(self, screenX, screenY):
        #look at objects first, then constraints
        for index in self.otherIndexes:
            if(self.objects[index].isClicked(screenX, screenY)):
                return self.objects[index]

        for index in self.constraintIndexes:
            if(self.objects[index].isClicked(screenX, screenY)):
                return self.objects[index]

#the base class for all objects that respond to basic physics
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

        #by default the basic object is always in the screen
        self.inScreen = True

    #add the given force to the object and update the acceleration
    def addForce(self, newForce):
        self.force += newForce
        self.accel = self.force / self.mass

    #update the particle's position based on verlet integration
    #found verlet at: 
    #http://www.gotoandplay.it/_articles/2005/08/advCharPhysics.php
    def update(self, dt, width, height):
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
    def draw(self, canvas, debug=False):
        #base object just draws a black circle
        r = 5
        (x, y) = self.environ.getScreenXY(self.position)

        canvas.create_oval(x-r, y-r, x+r, y+r, fill="black")
        if(debug):
            canvas.create_text(x, y, text=self.environIndex)

    #check if the object was clicked
    def isClicked(self, x, y):
        #by default the object's can't be clicked
        return False

    #Fix any collisions and return true if any collisions fixed
    def fixCollisions(self, objList):
        return False

    #return edges in the form (xval, index, "R"/"L")
    #by default, don't return anything since it is not collidable
    def getEdges(self):
        return []

    def __eq__(self, other):
        if(isinstance(other, PhysObject)):
            return ((self.position == other.position) and 
                    (type(self) == type(other)))
        else:
            return NotImplemented
  
#this class is for constrained particles
class Node(PhysObject):
    def __init__(self, position, mass, environ, isFixed, visible=True, 
                 color="black"):
        #list of constraints the node is connected to
        self.constraints = []
        #list of indexes of the node in the constraints' node list
        self.constraintIndexes = []

        #if the node is fixed in space
        self.isFixed = isFixed

        super(Node, self).__init__(position, mass, environ)

        #drawing constants
        self.r = 10
        self.color = color
        self.visible = visible

    def __hash__(self):
        return hash(str(self.position.getXY()) + self.color)

    #update particle only if it is not fixed        
    def update(self, dt, width, height):
        if(not self.isFixed):
            super(Node, self).update(dt, width, height)

    #create a constraint between this node and another node
    def addConstraint(self, constraint, nodeIndex):
        constraintIndex = len(self.constraints)
        self.constraints.append(constraint)
        self.constraintIndexes.append(nodeIndex)
        return constraintIndex

    #remove a constraint from the node's constraint list
    #(and update all other constraints of their changed indexes)
    def removeConstraint(self, constraintIndex, nodeIndex):
        #remove the constraint from the list by shifting everything else down
        for i in xrange(constraintIndex, len(self.constraints) - 1):
            self.constraints[i] = self.constraints[i+1]
            #update the constraint's index
            self.constraints[i].nodeIndexes[nodeIndex] = i

        #get rid of the tail element (that is a duplicate)
        del self.constraints[-1]

    #delete the node (and all of the connected constraints)
    def delete(self):
        #delete all constraints
        i = 0
        while(i < len(self.constraints)):
            #this method will delete the constraint from this node's
            #constraint list so we must watch out for out of bounds accesses
            self.constraints[i].delete()

        super(Node, self).delete() 

    #draw the node (if visisble)
    def draw(self, canvas, debug=False):
        r = self.r
        (x, y) = self.environ.getScreenXY(self.position)

        if(self.visible):
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=self.color)
        #optional debug info
        if(debug):
            canvas.create_text(x, y, text=len(self.constraints), fill="white")

    #returns true if the node was clicked, false otherwise
    def isClicked(self, clickX, clickY):
        #only visible nodes can be clicked
        if(self.visible):
            (x, y) = self.environ.getScreenXY(self.position)

            xDist = clickX - x
            yDist = clickY - y
            return (xDist**2 + yDist**2) <= self.r**2
        else:
            return False

#weights that will drop onto the bridge
class Weight(PhysObject):
    def __init__(self, *args):
        self.r = 15
        self.color = "orange"
        #the proportion of the collision distance that the weight moves
        #the lower this is, the heavier the weights seem
        self.collisionRatio = 0.25

        super(Weight, self).__init__(*args)

    #fix collisions between two weights
    def fixWeightWeightCollision(self, otherWeight):
        #vector from this object to the other object's center
        centerVect = otherWeight.position - self.position
        #distance b/w centers
        dist = centerVect.getMag()

        #minimum distance that the centers can be without colliding
        minDist = (self.environ.getEnvironScalar(otherWeight.r) + 
                   self.environ.getEnvironScalar(self.r))
        #if they are two close, fix the collision
        if(dist < minDist):
            #move the two weights so they are not overlapping
            displacement = dist - (minDist)
            scaleFactor = displacement / dist

            self.position += centerVect*(1/2.0)*scaleFactor
            otherWeight.position -= centerVect*(1/2.0)*scaleFactor

    #checks if the weight is above the constraint
    #aka, can the weight collide with the node
    def isWeightAboveConstraint(self, constraint):
        #vector from the 0th node to the wieght
        nodeWeightVect = self.position - constraint.nodes[0].position
        otherNodeWeightVect = self.position - constraint.nodes[1].position
        #get updated dist b/w nodes
        constraintVect = (constraint.nodes[1].position - 
                          constraint.nodes[0].position)
        reverseConstVect = (constraint.nodes[0].position -
                            constraint.nodes[1].position)

        #the value of cosine of the angle b/w the vects
        cosTheta0 = nodeWeightVect.getCosTheta(constraintVect)
        cosTheta1 = otherNodeWeightVect.getCosTheta(reverseConstVect)

        return cosTheta0 > 0 and cosTheta1 > 0

    #returns the vector perpendicular to the constraint, pointing toward
    #the weight
    def getWeightConstraintPerpVect(self, constraint):
        #vector from 0th node to weight
        nodeWeightVect = self.position - constraint.nodes[0].position
        #vector from 0th node to 1th node
        constraintVect = (constraint.nodes[1].position - 
                          constraint.nodes[0].position)
        #project the vector to the weight down onto the constraint
        projection = nodeWeightVect.projOnto(constraintVect)

        #vector perpendicular to constraint to center of ball
        perpVect = projection - nodeWeightVect

        return perpVect

    #Fix collision between a weight and a constraint
    def fixWeightConstraintCollision(self, constraint):
        #minimum distance that the weight and constraint can be before 
        #colliding
        minDist = (self.environ.getEnvironScalar(self.r) +
                   self.environ.getEnvironScalar(constraint.width/2))

        #if the weight is over the constaint
        if(self.isWeightAboveConstraint(constraint)):
            perpVect = self.getWeightConstraintPerpVect(constraint)
            dist = perpVect.getMag()

            if(dist < minDist):
                displacement = dist - minDist
                scaleFactor = displacement / dist

                #weight ratio
                wr = self.collisionRatio
                #constraint ratio
                cr = 1-self.collisionRatio

                #adjust the position of the weight
                self.position += perpVect*wr*scaleFactor
                #adjust the position of the constraint
                if(not constraint.nodes[0].isFixed):
                    constraint.nodes[0].position -= perpVect*cr*scaleFactor
                if(not constraint.nodes[1].isFixed):
                    constraint.nodes[1].position -= perpVect*cr*scaleFactor

    #collision resolution algorithm adapted from:
    #http://www.gotoandplay.it/_articles/2005/08/advCharPhysics.php
    def fixCollisions(self, objList):
        for obj in objList:
            if(isinstance(obj, Weight)):
                self.fixWeightWeightCollision(obj)
            elif(isinstance(obj, Constraint) and obj.isCollidable):
                self.fixWeightConstraintCollision(obj)

    #update the object. return true if it is still in the screen, else false
    def update(self, dt, width, height):
        #first, update as usual
        super(Weight, self).update(dt, width, height)

        #now make sure weight is in canvas
        (x, y) = self.environ.getScreenXY(self.position)
        r = self.r

        if(y - r > height or y + r < 0 or x - r > width or x + r < 0):
            self.inScreen = False

    #draw the weight
    def draw(self, canvas, debug=False):
        r = self.r
        (cx, cy) = self.environ.getScreenXY(self.position)

        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.color) 
        if(debug):
            canvas.create_text(cx, cy, text=self.environIndex)

    #get the right and left edges of the weight (xval, index, "R"/"L")
    def getEdges(self):
        (x, y) = self.position.getXY()
        r = self.environ.getEnvironScalar(self.r)
        leftEdge = (x-r, self.environIndex, "L")
        rightEdge = (x+r, self.environIndex, "R")
        return [leftEdge, rightEdge]

#does not extend phys object class because it does not act like a physObject
class Constraint(object):
    #node1, node2 are the nodes that the constraint is attached to
    #breakRatio is the fraction of the start len the constraint will move
    #before breaking
    def __init__(self, node1, node2, breakRatio, environ, collidable, 
                 baseColor="black"):
        self.isCollidable = collidable
        self.environ = environ
        self.environIndex = self.environ.add(self)

        self.nodes = [node1, node2]

        #the index of the constraint in both nodes constraint list
        self.nodeIndexes=[self.nodes[i].addConstraint(self, i) 
                          for i in xrange(len(self.nodes))]

        #what fraction of the length the constraint can change before breaking
        self.breakRatio = breakRatio
        #the initial length of the constraint
        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

        #drawing constants
        self.width = 5
        self.baseColor = baseColor
        self.color = self.baseColor

        #update basic info
        self.updateInfo()

    #initialize for simulation
    def initForSim(self):
        #update rest length (in case nodes were shifted since creation)
        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

    #this method is overwritten by subclasses
    #included so the overhead of super not needed each update
    def updateColor(self):
        pass

    #update all variables important for breaking/resolving constraint
    def updateInfo(self):
        node1Pos = self.nodes[0].position
        node2Pos = self.nodes[1].position

        #vector going from node 1 to node 2
        self.nodeVect = node2Pos - node1Pos
        self.curLen = self.nodeVect.getMag()
        if(self.curLen == 0): self.curLen = 0.01

        self.displacement = self.curLen - self.restLen

        self.lenRatio = self.displacement/self.curLen

    #break the constraint by making new nodes which are not fixed
    def breakConstraint(self):
        #create new nodes on the ends of the constraint so that it 
        #is freed. only create new constraints if there are other constraints
        #on that node or if the node is fixed
        if(self.environ.debug): 
            print "constraint %d is broken" % self.environIndex
            self.color = "black"
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

    #based on code from this tutorial:
    #http://www.gotoandplay.it/_articles/2005/08/advCharPhysics.php
    def resolve(self):
        self.updateInfo()

        #shift the nodes to fix the constraints
        if(not self.nodes[0].isFixed):
            self.nodes[0].position += self.nodeVect*0.5*self.lenRatio
        if(not self.nodes[1].isFixed):
            self.nodes[1].position -= self.nodeVect*0.5*self.lenRatio

    #check if the constraint should be broken
    def checkForBreak(self):
        self.updateInfo()
        if(abs(self.lenRatio) > self.breakRatio):
            self.breakConstraint()
            return True
        else:
            return False

    #delete the constraint (and update both nodes)
    def delete(self):
        #remove constraint from nodes
        for i in xrange(len(self.nodes)):
            self.nodes[i].removeConstraint(self.nodeIndexes[i], i)

        #now, remove from environment
        self.environ.deleteObj(self, self.environIndex)

    #get the length without updating the color and other info
    def getLength(self):
        return (self.nodes[0].position - self.nodes[1].position).getMag()

    def draw(self, canvas, debug=False):
        if(self.environ.isSimulating):
            self.updateColor()
        #node coordinates
        (x1, y1) = self.environ.getScreenXY(self.nodes[0].position)
        (x2, y2) = self.environ.getScreenXY(self.nodes[1].position)

        canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.width)

        if(debug):
            canvas.create_text((x1+x2)/2, (y1+y2)/2, text=self.environIndex)

    #get edges in the form (xval, index, "R"/"L")
    def getEdges(self):
        i = self.environIndex

        (xLeft, xRight) = self.getSortedXVals()

        return [(xLeft, i, "L"), (xRight, i, "R")]

    #get the xvalues of the edges of the constraint, sorted
    def getSortedXVals(self):
        xVals = [self.nodes[0].position.getXY()[0], 
                 self.nodes[1].position.getXY()[0]]
        xVals.sort()
        return tuple(xVals)  

    def isClicked(self, xClick, yClick):
        return False

#a non-collidable constraint for bridges
class BridgeBeam(Constraint):
    def __init__(self, *args):
        self.colorVals = (180, 180, 180)
        super(BridgeBeam, self).__init__(*args, collidable=False, 
                                         baseColor=rgbString(*self.colorVals))

    #update the color of the constraint based on tension/compression
    def updateColor(self):
        increaseScale = 75
        decreaseScale = 180
        #base color values
        (red, green, blue) = self.colorVals

        #displaceRatio is 1 or -1 right at breaking
        displaceRatio = self.lenRatio/self.breakRatio

        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        increaseChange = abs(displaceRatio) * increaseScale
        decreaseChange = abs(displaceRatio) * decreaseScale

        if(displaceRatio < 0):
            blue += increaseChange
            red -= decreaseChange
            green -= decreaseChange
        else:
            red += increaseChange
            blue -= decreaseChange
            green -= decreaseChange

        self.color = rgbString(red, green, blue)
        
#a collicable constraint for bridges     
class BridgeBed(Constraint):
    def __init__(self, *args):
        #base color values (R, G, B)
        self.colorVals = (100, 100, 100)
        super(BridgeBed, self).__init__(*args, collidable=True, 
                                        baseColor=rgbString(*self.colorVals))

    #update the color based on 
    def updateColor(self):
        increaseScale = 155
        decreaseScale = 100
        #base color values
        (red, green, blue) = self.colorVals

        #displaceRatio is 1 or -1 right at breaking
        displaceRatio = self.lenRatio/self.breakRatio

        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        increaseChange = abs(displaceRatio) * increaseScale
        decreaseChange = abs(displaceRatio) * decreaseScale

        if(displaceRatio < 0):
            blue += increaseChange
            red -= decreaseChange
            green -= decreaseChange
        else:
            red += increaseChange
            blue -= decreaseChange
            green -= decreaseChange

        self.color = rgbString(red, green, blue)

# a colidable constraint used for the terrain of the level
class LandBeam(Constraint):
    def __init__(self, *args):
        super(LandBeam, self).__init__(*args, collidable=True,
                                       baseColor="green")
