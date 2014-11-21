from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time

class PhysModuleDemo(EventBasedAnimationClass):
    def initEnviron(self):
        self.screenConversion = 50 #pixels/meter

        self.gravity = 10 #m/s**2

        #create an environment with the origin in the lower left
        self.environ = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)

    def placeStartNodes(self):
        nodes = []
        nodePoints = [(2, 5, True), (4, 5), (6, 5), (8, 5), (10, 5, True), 
                      (9, 7), (7, 7), (5, 7), (3, 7)]

        for point in nodePoints:
            if(len(point) == 3):
                (x, y, isFixed) = point
            else:
                (x, y) = point
                isFixed = False

            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,isFixed))

        #indexes of the two nodes (in list "nodes")
        constraintIndexes = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
                             (6, 7), (7, 8), (8, 0), (8, 1), (1, 7), (7, 2),
                             (2, 6), (6, 3), (3, 5)]

        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(Constraint(nodes[node1Index],nodes[node2Index], 
                                          self.breakRatio, self.environ))

        self.selectedNode = nodes[2]
        self.selectedNodeForce = Vector(0, 0)

    def initAnimation(self):
        #constants for noees/springs
        self.nodeMass = 10 #kg
        self.forceIncrement = 100 #how much the mass increases on a click
        self.breakRatio = 0.1

        self.initEnviron()

        self.placeStartNodes()

        self.dt = 1/60.0 #seconts (50 fps)
        self.timerDelay = int(self.dt * 1000) #convert to ms

        self.startTime = time.time()
        self.fps = 0


    def onMousePressed(self, event):
        selection = self.environ.getClickedObj(event.x, event.y)

        if(self.environ.isSimulating):
            pos = self.environ.getVect(event.x, event.y)
            Weight(pos, self.nodeMass, self.environ)
            
            self.selectedNodeForce += Vector(0, -self.forceIncrement)

    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()
        elif(event.keysym == "s"):
            self.environ.start()

    def onTimerFiredWrapper(self):
        if(self.timerDelay == None): return

        self.onTimerFired()
        self.redrawAll()

        endTime = time.time()
        timeDif = endTime - self.startTime

        self.timerDelay = 10#max(int(self.dt - timeDif) * 1000, 1)

        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)

        finalEndTime = time.time()
        fpsTimeDif = finalEndTime - self.startTime

        if(fpsTimeDif != 0):
            self.fps = 1/fpsTimeDif

        self.startTime = time.time()

    def onTimerFired(self):
        self.selectedNode.addForce(self.selectedNodeForce)
        self.environ.update(self.dt)

    def redrawAll(self):
        self.canvas.delete(ALL)
        
        r = self.screenConversion
        self.canvas.create_rectangle(0, 0, r, r, fill="red")

        self.environ.draw(self.canvas)
        self.canvas.create_text(0, 0, text=("%.2f" % self.fps), anchor=NW,
                                font="Arial 20 bold")

demo = PhysModuleDemo(750, 500)
demo.run()