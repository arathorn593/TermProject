from physObject import PhysObject
from vector import Vector
from physEnvironment import PhysEnvironment
from eventBasedAnimationClass import EventBasedAnimationClass
from Tkinter import *

class FlyingBall(EventBasedAnimationClass):
    def initAnimation(self):
        self.dt = 1/50.0 #seconts (50 fps)
        self.timerDelay = int(self.dt * 1000) #convert to ms

        self.screenConversion = 250 #pixels/meter

        self.gravity = 10 #m/s**2
        
        #create an environment with the origin in the lower left
        self.environment = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)

        self.ballMass = 1 #kg

        self.ball = PhysObject(0, 0, self.ballMass, False, self.environment)

        self.environment.addObj(self.ball)

        self.root.bind("<B1-ButtonRelease>", 
                       lambda event: self.onMouseReleasedWrapper(event))

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    def onMousePressed(self, event):
        self.lineStart = self.environment.getVect(event.x, event.y)

    def onMouseReleased(self, event):

        lineEnd = self.environment.getVect(event.x, event.y)
        velocityVect = (lineEnd - self.lineStart)

        scale = 3 #scale up velocity
        velocityVect *= scale

        self.ball.velocity = velocityVect
        self.environment.start()

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



demo = FlyingBall(1000, 750)
demo.run()