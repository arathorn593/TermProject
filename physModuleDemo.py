from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time

class PhysModuleDemo(EventBasedAnimationClass):
    def initEnviron(self):
        self.screenConversion = 50 #pixels/meter

        self.gravity = 5 #m/s**2

        #create an environment with the origin in the lower left
        self.environ = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)

    def placeBox(self, screenX, screenY):
        boxR = self.environ.getEnvironScalar(15)
        pos = self.environ.getVect(screenX, screenY)

        nodePoints = [pos + Vector(0, boxR), #top corner
                      pos + Vector(boxR, 0), #right corner
                      pos + Vector(0, -boxR), #bottom corner
                      pos + Vector(-boxR, 0)] #left corner

        nodes = []
        for point in nodePoints:
            nodes.append(Node(point, 0.1 ,self.environ,False))

        #indexes of the two nodes (in list "nodes")
        constraintIndexes = [(0, 1), (1, 2), (2, 3), (3, 0)]

        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(Constraint(nodes[node1Index],nodes[node2Index], 
                                          1, self.environ))

    def placeBridge(self):
        nodes = []
        nodePoints = [(2, 5, True), (4, 5), (6, 5), (8, 5), (10, 5, True), 
                      (9, 7), (7, 7), (5, 7), (3, 7)]

        for point in nodePoints:
            if(len(point) == 3):
                (x, y, isFixed) = point
            else:
                (x, y) = point
                isFixed = False

            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,isFixed, False))

        #indexes of the two nodes (in list "nodes")
        constraintIndexes = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
                             (6, 7), (7, 8), (8, 0), (7, 1), (1, 8), (7, 2),
                             (2, 6), (6, 3), (3, 5)]

        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(Constraint(nodes[node1Index],nodes[node2Index], 
                                          self.breakRatio, self.environ))

        self.selectedNode = nodes[2]
        self.selectedNodeForce = Vector(0, 0)

    def placeStartNodes(self):
        nodePoints = [(2, 2), (2, 5), (12, 2), (12, 5)]

        for point in nodePoints:
            (x, y) = point
            self.selectedNode = Node(Vector(x, y), self.nodeMass, 
                                     self.environ, True)

        self.selectedNodeForce = Vector(0, 0)

    def initAnimation(self):
        #constants for noees/springs
        self.nodeMass = 10 #kg
        self.forceIncrement = 100 #how much the mass increases on a click
        self.breakRatio = 0.05

        self.initEnviron()

        self.placeStartNodes()

        self.mode = "build"

        self.dt = 1/30.0 #seconts (30 fps)
        self.timerDelay = int(self.dt * 1000) #convert to ms

        self.startTime = time.time()
        self.fps = 0

        self.tempConstraint = None
        self.tempNode = None
        self.startNode = None

        self.root.bind("<B1-ButtonRelease>", 
                       lambda event: self.onMouseReleasedWrapper(event))

        self.root.bind("<B1-Motion>", lambda event: 
                       self.onMouseDragWrapper(event))

    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()


    def onMouseReleased(self, event):
        if(self.tempNode != None):
            selection = self.environ.getClickedObj(event.x, event.y)
            if(selection != None and isinstance(selection, Node)):
                #if the original node was ended on then delete spring too
                self.tempNode.delete()
                #only make new constraint if the start node wasn't ended on
                if(not (selection == self.startNode)):
                    Constraint(self.startNode, selection, self.breakRatio,
                               self.environ)

            else:
                self.tempNode.visible = True

            #reset temp variables
            self.tempConstraint = None
            self.tempNode = None
            self.startNode = None

    def onMouseDrag(self, event):
        if(self.tempNode != None):
            self.tempNode.position = self.environ.getVect(event.x, event.y)

    def onMousePressed(self, event):
        selection = self.environ.getClickedObj(event.x, event.y)

        if(self.environ.isSimulating):
            pos = self.environ.getVect(event.x, event.y)

            Weight(pos, self.nodeMass*10, self.environ)
            #self.placeBox(event.x, event.y)
            #self.selectedNodeForce += Vector(0, -self.forceIncrement*2)
        else:
            if(isinstance(selection, Node)):
                if(self.tempConstraint == None):
                    pos = self.environ.getVect(event.x, event.y)
                    #make new node/constraint
                    self.startNode = selection
                    self.tempNode = Node(pos, self.nodeMass, self.environ,
                                         False, False)
                    self.tempConstraint = Constraint(self.startNode, 
                                                     self.tempNode,
                                                     self.breakRatio, 
                                                     self.environ)

    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()
        elif(event.keysym == "s"):
            self.environ.start()
        elif(event.keysym == "b"):
            if(not self.environ.isSimulating):
                self.placeBridge()

    def onTimerFiredWrapper(self):
        if(self.timerDelay == None): return
        oldTime = self.startTime
        self.startTime = time.time()
        if(self.startTime == oldTime):
            self.fps = -1
        else:
            self.fps = 1/(self.startTime - oldTime) 

        self.onTimerFired()
        self.redrawAll()

        endTime = time.time()
        timeDif = endTime - self.startTime

        frameRemaining = int((self.dt - timeDif) * 1000)
        
        #print "timeDif = %.5f dt = %.5f remaining = %.2f" % (timeDif, self.dt, 
        #                                                     frameRemaining)

        self.timerDelay = max(frameRemaining, 1)

        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)

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