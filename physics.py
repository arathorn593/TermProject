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

        self.constraintIndexes = []
        self.weightIndexes = []
        self.otherIndexes = []
        self.objects = []

        self.resolveIterations = 5
        self.debug = False

    def start(self):
        if(not self.hasStarted):
            #init all constraints for starting the animation
            for index in self.constraintIndexes:
                self.objects[index].initForSim()

        self.isSimulating = True
        self.hasStarted = True

    def pause(self):
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
        self.objects.append(obj)
        index = len(self.objects) - 1
        if(isinstance(obj, Constraint)):
            self.constraintIndexes.append(index)
        elif(isinstance(obj, Weight)):
            self.weightIndexes.append(index)
        else:
            self.otherIndexes.append(index)

        return index

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

    def resolveCollisions1(self):
        #resolve collisions
        for i in xrange(len(self.objects)):
            if(isinstance(self.objects[i], Weight)):
                self.objects[i].fixCollisions(self.objects[i+1:] + 
                                              self.constraints)

    def generateEdgeList(self):
        edgeList = []

        for obj in self.objects:
            #if(isinstance(obj, Weight)):
            #    print obj.getEdges()
            edgeList += obj.getEdges()

        edgeList.sort()
        #print the edge list for debuging
        if(self.debug):
            print "edgeList = [",
            for edge in edgeList:
                print edge[1],
            print "]"
        return edgeList

    #I came up with an initial rough version of this algorith, but
    # my roomate helped me get it to this point
    def resolveCollisions(self):
        #list of tuples in the form: (xVal, index, "R"/"L" (right or left))
        #note: xval is in environ coordinates
        edgeList = self.generateEdgeList()

        #the list of objects that could be colliding
        objList = []
        for edge in edgeList:
            if(self.debug):
                print "edge = (%d, %s)" % (edge[1], edge[2])
                print "objList before = [",
                for obj in objList:
                    print "%d," % obj.environIndex,
                print "]"

            (x, i, side) = edge
            if(side == "L"):
                newObj = self.objects[i]
                if(len(objList) > 0):
                    if(isinstance(newObj, Weight)):
                        if(self.debug): print "new obj is a weight"
                        newObj.fixCollisions(objList)
                    else:
                        if(self.debug): print "new obj is not a weight"
                        for i in xrange(len(objList)):
                            if(isinstance(objList[i], Weight)):
                                objList[i].fixCollisions([newObj])
                objList.append(newObj)

            elif(side == "R"):
                for index in xrange(len(objList)):
                    if(objList[index].environIndex == i):
                        objList.pop(index)
                        break

            if(self.debug):
                print "objList after = [",
                for obj in objList:
                    print "%d," % obj.environIndex,
                print "]"

    #update each object in the list, assume each is a physObject
    #returns the number of objects that left the bottom of the screen
    def update(self, dt, width, height):
        if(self.isSimulating):
            for iteration in xrange(self.resolveIterations):
                #fixedCollisions = True

                self.resolveCollisions()

                #resolve constraints
                for index in self.constraintIndexes:
                    self.objects[index].resolve()

                #stop adjusting if all collisions fixed
                #print fixedCollisions
                #if(not self.resolveCollisions()): break

            objExitingBottom = 0
            objToDelete = []
            #once constraints and collisions handled, update objects
            for index in self.otherIndexes + self.weightIndexes:
                self.objects[index].update(dt, width, height)
                if(not self.objects[index].inScreen):
                    #check if the object exited the bottom
                    (x, y) = self.getScreenXY(self.objects[index].position)

                    if(y > height):
                        objExitingBottom += 1
                    #delete the object either way
                    if(not isinstance(self.objects[index], Node)):
                        objToDelete.append(self.objects[index])

            for obj in objToDelete:
                obj.delete()

            return objExitingBottom
        

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

    def update(self, dt, width, height):
        if(not self.isFixed):
            super(Node, self).update(dt, width, height)

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

    def draw(self, canvas, debug=False):
        r = self.r
        (x, y) = self.environ.getScreenXY(self.position)
        if(self.visible):
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=self.color)
        if(debug):
            canvas.create_text(x, y, text=len(self.constraints), fill="white")

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
        self.collisionRatio = 0.4
        self.frictionCoef = 0.01
        super(Weight, self).__init__(*args)

    #collision resolution algorithm adapted from:
    #http://www.gotoandplay.it/_articles/2005/08/advCharPhysics.php
    def fixCollisions(self, objList):
        returnVal = False
        debug = self.environ.debug
        if(debug):
            print "objList in collision func: [",
            for obj in objList:
                print obj.environIndex,
            print "]"
        for obj in objList:
            if(debug): print "testing index %d" % obj.environIndex
            if(isinstance(obj, Weight)):
                if(debug): print "object is a weight"
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
                    returnVal = True

            elif(isinstance(obj, Constraint) and obj.isCollidable):
                if(debug): print "object is a collidable constraint"
                minDist = (self.environ.getEnvironScalar(self.r) +
                           self.environ.getEnvironScalar(obj.width/2))
    
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

                        #weight ratio
                        wr = self.collisionRatio
                        #constraint ratio
                        cr = 1-self.collisionRatio
                        self.position += perpVect*wr*scaleFactor
                        #obj.nodes[0].addForce(self.mass * Vector(0, -1))
                        #obj.nodes[1].addForce(self.mass * Vector(0, -1))
                        if(not obj.nodes[0].isFixed):
                            obj.nodes[0].position -= perpVect*cr*scaleFactor
                        if(not obj.nodes[1].isFixed):
                            obj.nodes[1].position -= perpVect*cr*scaleFactor
                        returnVal = True
            #if there was a collision, add friction
            '''
            if(returnVal):
                penetration = minDist - dist
                frictionScale = 1-self.frictionCoef
                v = self.position - self.oldPosition
                #change in velocity
                dv = v.getMag() - penetration*frictionScale
                dv = dv if dv < v.getMag() else v.getMag()

                #move oldPos along velocity vector by dv
                ratio = v.getMag()/dv
                v *= ratio
                self.oldPosition += v
                '''

        #no collisions occured
        return returnVal

    def update(self, dt, width, height):
        #first, update as usual
        super(Weight, self).update(dt, width, height)

        #now make sure weight is in canvas
        (x, y) = self.environ.getScreenXY(self.position)
        r = self.r

        if(y - r > height or y + r < 0 or x - r > width or x + r < 0):
            self.inScreen = False

    def draw(self, canvas, debug=False):
        r = self.r
        (cx, cy) = self.environ.getScreenXY(self.position)

        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.color) 
        if(debug):
            canvas.create_text(cx, cy, text=self.environIndex)

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

        self.nodeIndexes=[self.nodes[i].addConstraint(self, i) 
                          for i in xrange(len(self.nodes))]

        self.breakRatio = breakRatio
        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

        #drawing constants
        self.width = 5
        self.baseColor = baseColor
        self.color = self.baseColor
        self.updateInfo()

    #initialize for simulation
    def initForSim(self):
        #update rest length (in case nodes were shifted since creation)
        self.restLen = (self.nodes[0].position-self.nodes[1].position).getMag()

    #this method is overwritten by subclasses
    #included so the overhead of super not needed each update
    def updateColor(self):
        pass

    def updateInfo(self):
        node1Pos = self.nodes[0].position
        node2Pos = self.nodes[1].position

        #vector going from node 1 to node 2
        self.nodeVect = node2Pos - node1Pos
        self.curLen = self.nodeVect.getMag()
        if(self.curLen == 0): self.curLen = 0.01

        self.displacement = self.curLen - self.restLen

        self.lenRatio = self.displacement/self.curLen

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

    #based on code from this tutorial:
    #http://www.gotoandplay.it/_articles/2005/08/advCharPhysics.php
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

    def getEdges(self):
        i = self.environIndex

        (x0, y0) = self.nodes[0].position.getXY()
        (x1, y1) = self.nodes[1].position.getXY()

        xLeft = x0 if x0 < x1 else x1
        xRight = x0 if x0 > x1 else x1

        return [(xLeft, i, "L"), (xRight, i, "R")]


    def isClicked(self, screenX, screenY):
        return False    

class BridgeBeam(Constraint):
    def __init__(self, *args):
        self.colorVals = (180, 180, 180)
        super(BridgeBeam, self).__init__(*args, collidable=False, 
                                         baseColor=rgbString(*self.colorVals))
    
    def updateColor(self):
        #base color values
        (red, green, blue) = self.colorVals

        #displaceRatio is 1 or -1 right at breaking
        displaceRatio = self.lenRatio/self.breakRatio

        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        increaseChange = abs(displaceRatio) * 75
        decreaseChange = abs(displaceRatio) * 180

        if(displaceRatio < 0):
            blue += increaseChange
            red -= decreaseChange
            green -= decreaseChange
        else:
            red += increaseChange
            blue -= decreaseChange
            green -= decreaseChange

        self.color = rgbString(red, green, blue)
        
            
class BridgeBed(Constraint):
    def __init__(self, *args):
        self.colorVals = (100, 100, 100)
        super(BridgeBed, self).__init__(*args, collidable=True, 
                                        baseColor=rgbString(*self.colorVals))

    def updateColor(self):
        #base color values
        (red, green, blue) = self.colorVals

        #displaceRatio is 1 or -1 right at breaking
        displaceRatio = self.lenRatio/self.breakRatio

        if(displaceRatio > 1): 
            displaceRatio = 1
        elif(displaceRatio < -1):
            displaceRatio = -1

        increaseChange = abs(displaceRatio) * 155
        decreaseChange = abs(displaceRatio) * 100

        if(displaceRatio < 0):
            blue += increaseChange
            red -= decreaseChange
            green -= decreaseChange
        else:
            red += increaseChange
            blue -= decreaseChange
            green -= decreaseChange

        self.color = rgbString(red, green, blue)

class LandBeam(Constraint):
    def __init__(self, *args):
        super(LandBeam, self).__init__(*args, collidable=True,
                                       baseColor="green")
