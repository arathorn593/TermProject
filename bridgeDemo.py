from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time

class BridgeDemo(EventBasedAnimationClass):
    def initEnviron(self):
        self.dt = 1/60.0 #seconts (50 fps)
        self.screenConversion = 50 #pixels/meter

        self.gravity = 10 #m/s**2
        
        self.selectedNode = None

        #create an environment with the origin in the lower left
        self.environ = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)


    def placeStartNodes(self):
        nodePoints = [(2, 2), (2, 5), (12, 2), (12, 5)]

        for point in nodePoints:
            (x, y) = point
            node = Node(Vector(x, y), self.nodeMass, self.environ, True)

    def initAnimation(self):
        #constants for noees/springs
        self.nodeMass = 10 #kg
        self.massIncrement = 10 #how much the mass increases on a click
        self.springK = 2000 
        self.springDampRatio = 1
        self.springBreakRatio = 0.1

        self.initEnviron()

        self.placeStartNodes()

        self.timerDelay = int(self.dt * 1000) #convert to ms

        self.newNode = None
        self.newSpring = None

        self.root.bind("<B1-ButtonRelease>", 
                       lambda event: self.onMouseReleasedWrapper(event))

        self.root.bind("<B1-Motion>", lambda event: 
                       self.onMouseDragWrapper(event))
        self.oldTime = time.time()
        self.fps = 0


    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    def onMousePressed(self, event):
        selection = self.environ.getClickedObj(event.x, event.y)

        if(selection != None and isinstance(selection, Node)):
            if(self.environ.isSimulating):
                selection.accel += Vector(0, -self.massIncrement*10)
            else:
                #make new node that will follow the mouse and not be fixed
                (x, y) = self.environ.getVect(event.x, event.y).getXY()
                self.startNode = selection
                self.newNode = Node(x, y, self.nodeMass, False, self.environ)
                
                #create spring between two nodes 
                #(automatically added to envion)
                self.newSpring = Spring(self.startNode, self.newNode,
                                        self.springK, self.springDampRatio, 
                                        self.springBreakRatio, self.environ)

    def onMouseReleased(self, event):
        if(self.newNode != None):
            #delete node and then create new node if no other node
            self.environ.deleteObj(self.newNode)

            selection = self.environ.getClickedObj(event.x, event.y)
            if(selection != None and isinstance(selection, Node)):
                #if the original node was ended on then delete spring too
                if(selection is self.startNode):
                    self.startNode.removeSpring(self.newSpring)
                    self.environ.deleteObj(self.newSpring)


                #sanity check to make sure node2 was the selected note
                node = self.newSpring.node2
                assert(node is self.newNode)

                self.newSpring.node2 = selection
                selection.addSpring(self.newSpring)

            else:
                #add new node back in
                self.environ.addObj(self.newNode)

            #stop controlling the new node
            self.newNode = None

    def onMouseDrag(self, event):
        if(self.newNode != None):
            self.newNode.position = self.environ.getVect(event.x, event.y)

    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()
        elif(event.keysym == "s"):
            self.environ.start()

    def onTimerFired(self):
        self.environ.update(self.dt)
        newTime = time.time()
        timeDif = newTime - self.oldTime
        if(timeDif != 0):
            self.fps = 1/timeDif

        #print "dt = %f, frame = %f" % (self.dt, timeDif)
        #calculate new time delay so dt stays consistent
        self.timerDelay = 10#max(int((self.dt - timeDif) * 1000), 1)

        self.oldTime = newTime


    def redrawAll(self):
        self.canvas.delete(ALL)
        
        r = self.screenConversion
        self.canvas.create_rectangle(0, 0, r, r, fill="red")

        self.environ.draw(self.canvas)
        self.canvas.create_text(0, 0, text=("%.2f" % self.fps), anchor=NW,
                                font="Arial 20 bold")

demo = BridgeDemo(750, 500)
demo.run()