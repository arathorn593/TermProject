from vector import Vector
from eventBasedAnimationClass import EventBasedAnimationClass

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

        self.drawQue = []
        self.updateQue = []

    def start(self):
        if(not self.hasStarted):
            #init all objects for starting the animation
            for obj in self.updateQue:
                obj.initForSim()

        self.isSimulating = True

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
    def addObj(self, obj):
        self.drawQue.append(obj)
        self.updateQue.append(obj)

        #sort both ques (reverse so high numbers come first in updateque)
        self.updateQue.sort(lambda x, y:cmp(x.updatePriority,y.updatePriority),
                            reverse=True)
        self.drawQue.sort(lambda x, y: cmp(x.drawPriority, y.drawPriority))

    def deleteObj(self, deleteObj):
        for i in xrange(len(self.updateQue)):
            if(self.updateQue[i] is deleteObj):
                del self.updateQue[i]
                break

        #remove from drawQue as well
        for i in xrange(len(self.drawQue)):
            if(self.drawQue[i] is deleteObj):
                del self.drawQue[i]
                break



    #update each object in the list, assume each is a physObject
    def update(self, dt):
        if(self.isSimulating):
            for obj in self.updateQue:
                obj.update(dt)

    #draw all the objects in the simulation
    def draw(self, canvas):
        #draw objects so springs are in front but behind nodes
        for obj in self.drawQue:
            obj.draw(canvas)

    #returns the object at the given screen coords or none
    def getClickedObj(self, screenX, screenY):
        #look at draw que because that will get the top object
        for obj in self.drawQue:
            if(obj.isClicked(screenX, screenY)):
                return obj

def testPhysEnvironment():
    grav = 10
    screenConv = 100
    x0 = 0
    y0 = 250

    environment = PhysEnvironment(grav, screenConv, x0, y0)

    #object at 1, 1.5 in meters
    position = Vector(1, 1.5)

    assert(environment.getScreenXY(position) == (100, 100))

    screenPos = Vector(150, 175)
    assert(environment.getVect(screenPos) == (1.5, .75))
    '''
    class EnvironTest(EventBasedAnimationClass):
        def initAnimation(self):
            self.grav = 10 #m/s**2
            self.screenConversion = 100 #pixels/meter
            x0 = 0
            y0 = self.height

            self.position = Vector(0, 0)
    '''

#testPhysEnvironment()