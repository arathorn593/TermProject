from physObject import PhysObject
from vector import Vector
from physEnvironment import PhysEnvironment
from eventBasedAnimationClass import EventBasedAnimationClass
from spring import Spring
from spring import Node
from Tkinter import *

class SpringDemo(EventBasedAnimationClass):
    def initAnimation(self):
        self.dt = 1/50.0 #seconts (50 fps)
        self.timerDelay = int(self.dt * 1000) #convert to ms

        self.screenConversion = 250 #pixels/meter

        self.gravity = 10 #m/s**2
        
        #create an environment with the origin in the lower left
        self.environment = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)

        self.nodeMass = 10 #kg
        self.springK = 200
        self.springDampRatio = 0
        #node 1 will be fixed
        self.node1 = Node(1.5, 2.5, self.nodeMass, True, self.environment)

        self.node2 = Node(2.5, 2.5, self.nodeMass, False, self.environment)

        self.node3 = Node(3.5, 2.5, self.nodeMass, True, self.environment)

        self.spring1 = Spring(self.node1, self.node2, self.springK,
                             self.springDampRatio, 1, self.environment)

        self.spring2 = Spring(self.node2, self.node3, self.springK,
                              self.springDampRatio, 1, self.environment)

        self.environment.start()

        self.root.bind("<B1-ButtonRelease>", 
                       lambda event: self.onMouseReleasedWrapper(event))

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    def onMousePressed(self, event):
        self.lineStart = self.environment.getVect(event.x, event.y)

    def onMouseReleased(self, event):

        pass
        '''
        lineEnd = self.environment.getVect(event.x, event.y)
        velocityVect = (lineEnd - self.lineStart)

        scale = 3 #scale up velocity
        velocityVect *= scale

        self.ball.velocity = velocityVect
        self.environment.isSimulating = True
        '''

    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()

    def onTimerFired(self):
        self.environment.update(self.dt)

    def redrawAll(self):
        self.canvas.delete(ALL)
        
        r = self.screenConversion
        self.canvas.create_rectangle(0, 0, r, r, fill="red")

        self.environment.draw(self.canvas)



demo = SpringDemo(1000, 750)
demo.run()