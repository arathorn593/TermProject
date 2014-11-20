from eventBasedAnimationClass import EventBasedAnimationClass
from Tkinter import *
import math

class OneDimDemo(EventBasedAnimationClass):
    def initAnimation(self):
        #decorators - convert values on the fly

        self.dt = 1/60.0
        self.timerDelay = int(self.dt * 1000)
        self.dt = self.timerDelay / 1000.0

        self.x = self.width/2
        self.y = self.height/2
        self.r = 5

        self.gravity = 10 #m/s**2
        self.velocity = 2.5 #m/s
        self.elasticity = .5

        self.screenConversion = 250 #pixels/meter

        self.screenGrav = self.gravity * self.screenConversion
        self.screenVelocity = self.velocity * self.screenConversion



    def onTimerFired(self):
        self.screenVelocity -= self.screenGrav * self.dt
        self.y += self.screenVelocity * self.dt

        if(self.y - self.r < 0):
            self.y = self.r
            self.screenVelocity *= -1 * self.elasticity

    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()

    def redrawAll(self):
        self.canvas.delete(ALL)

        self.canvas.create_rectangle(0, 0, self.screenConversion, 
                                     self.screenConversion, fill="red")

        (x, y, r) = (self.x, self.y, self.r)
        y = self.height - y
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="black")


class OneDimSpring(object):
    def __init__(self, x, y0, y1, k, mass, length, damp, grav):
        self.x = x
        self.top = max(y0, y1)
        self.bot = min(y0, y1)
        print "top=%d, bot=%d" % (self.top, self.bot)
        self.botV = 0

        self.length = length
        self.k = k
        self.displacement = (self.length - abs(self.top - self.bot))
        self.mass = mass
        self.damp = damp
        self.grav = grav

        self.updateSpringForce()
        self.massForce = -grav * self.mass# + self.springForce

    def updateSpringForce(self):
        self.displacement = (self.length - abs(self.top - self.bot))
        dampForce = -self.damp * self.botV
        self.springForce = -1*self.k*self.displacement + dampForce

    def update(self, dt):
        self.updateSpringForce()
        gravForce = -self.grav * self.mass
        self.massForce = gravForce + self.springForce

        botAccel = self.massForce / self.mass

        self.botV += botAccel * dt
        self.bot += self.botV * dt

    def draw(self, canvas, height):
        print "top=%d, bot=%d" % (self.top, self.bot)
        r = 5
        (cx0, cy0) = (self.x, height - self.top)
        (cx1, cy1) = (self.x, height - self.bot)

        canvas.create_oval(cx0-r, cy0-r, cx0+r, cy0+r, fill="black")
        canvas.create_oval(cx1-r, cy1-r, cx1+r, cy1+r, fill="black")
        canvas.create_line(cx0, cy0, cx1, cy1)

class OneDimSpringDemo(OneDimDemo):
    def initAnimation(self):
        super(OneDimSpringDemo, self).initAnimation()

        self.springLen = 200
        self.springK = 20000
        self.mass = 10
        startStetch = 50
        self.dampRatio = 1.3
        self.springDamp = (self.dampRatio * 2 * 
                           math.sqrt(self.mass * self.springK))

        print self.dampRatio, self.springDamp
        
        self.spring = OneDimSpring(self.x, self.y, 
                                   self.y + self.springLen + startStetch, 
                                   self.springK, self.mass, self.springLen,
                                   self.springDamp, self.gravity)

        self.counter = 0
        self.graphY0 = 200
        self.graph = []

    def onTimerFired(self):
        self.spring.update(self.dt)
        self.counter += 1
        self.graph.append((self.counter, self.graphY0 + 
                           self.spring.displacement))

    def drawGraph(self):
        for i in xrange(1, len(self.graph)):
            self.canvas.create_line(self.graph[i-1], self.graph[i], 
                                    fill="blue")

    def redrawAll(self):
        self.canvas.delete(ALL)
        self.spring.draw(self.canvas, self.height)
        self.drawGraph()


demo = OneDimSpringDemo()
demo.run()

demo = OneDimDemo()
demo.run()