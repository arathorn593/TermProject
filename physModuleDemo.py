from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time

#handles buttons
class Button(object):
    #creates a button at x, y of specified dimensions with the given text and
    #color. selectedColor is what color the button is when selected.
    #id is an identifier for the button. 
    def __init__(self, x, y, width, height, margin, text, color, selectColor, 
                 identifier):
        (self.x0, self.y0) = (x + margin, y + margin)
        (self.x1, self.y1) = (self.x0+width-margin*2, self.y0+height-margin*2)

        self.text = text

        self.color = color
        self.selectedColor = selectColor
        self.selected = False

        self.id = identifier

    #check if button was clicked
    def isClicked(self, xClick, yClick):
        return (xClick > self.x0 and xClick < self.x1 and 
                yClick > self.y0 and yClick < self.y1)

    #draw button
    def draw(self, canvas):
        color = self.selectedColor if self.selected else self.color
        canvas.create_rectangle(self.x0, self.y0, self.x1, self.y1, 
                                fill=color)

        cx = (self.x0 + self.x1) / 2
        cy = (self.y0 + self.y1) / 2

        canvas.create_text(cx, cy, text=self.text, font="Arial 15")

#this is a class that is a list of buttons where only one can be selected 
#*args is a list of buttons
class ToggleButtons(object):
    def __init__(self, *args):
        #if there is only one argument
        if(len(args) == 1 and type(args[0]) == list or type(args[0]) == tuple):
            args = args[0]

        self.buttons = list(args)
        self.selectedId = None

    def update(self, xClick, yClick):
        selectedIndex = -1
        for i in xrange(len(self.buttons)):
            if(self.buttons[i].isClicked(xClick, yClick)):
                selectedIndex = i
                self.selectedId = self.buttons[i].id
                break

        #if a button was selected
        if(selectedIndex != -1):
            for i in xrange(len(self.buttons)):
                if(i != selectedIndex):
                    self.buttons[i].selected = False
                else:
                    self.buttons[i].selected = True

    def draw(self, canvas):
        for button in self.buttons:
            button.draw(canvas)

    def select(self, identifier):
        for button in self.buttons:
            if(button.id == identifier):
                button.selected = True
                self.selectedId = identifier



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
            constraints.append(self.buildType(nodes[node1Index],nodes[node2Index], 
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

            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,isFixed,
                              True))

        #indexes of the two nodes (in list "nodes")
        constraintIndexes = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
                             (6, 7), (7, 8), (8, 0), (7, 1), (1, 8), (7, 2),
                             (2, 6), (6, 3), (3, 5)]

        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(self.buildType(nodes[node1Index],nodes[node2Index], 
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

    def initButtons(self):
        buttonMargin = 5
        buttonWidth = 100
        buttonHeight = 40
        color = "blue"
        selectedColor = "green"
        (x, y) = (0, 0)
        xIncrement = 0
        yIncrement = buttonMargin + buttonHeight
        buttonIds = ["Beam", "Bed"]
        buttons = []

        for identifier in buttonIds:
            buttons.append(Button(x, y, buttonWidth, buttonHeight, 
                                  buttonMargin, identifier, color, 
                                  selectedColor, identifier))

            x += xIncrement
            y += yIncrement

        self.toggleButtons = ToggleButtons(buttons)
        self.toggleButtons.select("Bed")

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

        self.debug = False
        self.isGameOver = False

        self.score = 0

        self.initButtons()
        self.buildType = BridgeBed

    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    def onMouseReleased(self, event):
        if(self.mode == "build"):
            if(self.tempNode != None):
                selection = self.environ.getClickedObj(event.x, event.y)
                if(selection != None and isinstance(selection, Node)):
                    #if the original node was ended on then delete spring too
                    self.tempNode.delete()
                    #only make new constraint if the start node wasn't ended on
                    if(not (selection == self.startNode)):
                        self.buildType(self.startNode, selection, self.breakRatio,
                                   self.environ)

                else:
                    self.tempNode.visible = True

                #reset temp variables
                self.tempConstraint = None
                self.tempNode = None
                self.startNode = None

    def onMouseDrag(self, event):
        if(self.tempNode != None and self.mode == "build"):
            self.tempNode.position = self.environ.getVect(event.x, event.y)

    def onMousePressed(self, event):
        if(self.mode == "build"):
            self.toggleButtons.update(event.x, event.y)
            if(self.toggleButtons.selectedId == "Beam"):
                self.buildType = BridgeBeam
            elif(self.toggleButtons.selectedId == "Bed"):
                self.buildType = BridgeBed

            selection = self.environ.getClickedObj(event.x, event.y)

            if(isinstance(selection, Node)):
                if(self.tempConstraint == None):
                    pos = self.environ.getVect(event.x, event.y)
                    #make new node/constraint
                    self.startNode = selection
                    self.tempNode = Node(pos, self.nodeMass, self.environ,
                                         False, False)
                    self.tempConstraint = self.buildType(self.startNode, 
                                                     self.tempNode,
                                                     self.breakRatio, 
                                                     self.environ)
        elif(self.mode == "test"):
            pos = self.environ.getVect(event.x, event.y)

            Weight(pos, self.nodeMass*10, self.environ)
            if(not self.isGameOver):
                self.score += 1
            #self.placeBox(event.x, event.y)
            #self.selectedNodeForce += Vector(0, -self.forceIncrement*2)


    def onKeyPressed(self, event):
        if(event.keysym == "r"):
            self.initAnimation()
        elif(event.keysym == "s"):
            self.mode = "test"
            self.environ.start()
        elif(event.keysym == "b"):
            if(self.mode == "build"):
                self.placeBridge()
        elif(event.keysym == "d"):
            self.debug = not self.debug

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
        
        #print "timeDif = %.5f dt = %.5f remaining = %.2f" % (timeDif, 
        #                                              self.dt, frameRemaining)

        self.timerDelay = max(frameRemaining, 1)

        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)

    def onTimerFired(self):
        if(self.mode == "test"):
            self.selectedNode.addForce(self.selectedNodeForce)
            #the number of objects that left the bottom of the screen
            bottomObjCount = self.environ.update(self.dt,
                                                 self.width, self.height)
            if(bottomObjCount > 0): 
                self.isGameOver = True

    def drawDebug(self):
        #unit square for scale
        r = self.screenConversion
        self.canvas.create_rectangle(0, 0, r, r, fill="red")
        #frame rate
        self.canvas.create_text(0, 0, text=("%.2f" % self.fps), anchor=NW,
                                font="Arial 20 bold")

    def drawGameOver(self):
        (x, y) = (self.width/2, self.height/2)
        self.canvas.create_text(x, y, text="GAME OVER", font="Arial 30 bold",
                                fill="black")

    def drawScore(self):
        (x, y) = (self.width, 0)

        self.canvas.create_text(x, y, text=self.score, font="Arial 15 bold",
                                fill="black", anchor=NE)

    def drawBuildScreen(self):
        self.toggleButtons.draw(self.canvas)

    def drawGame(self):
        self.drawScore()
        self.environ.draw(self.canvas)
        if(self.isGameOver): self.drawGameOver()
        if(self.mode == "build"):
            self.drawBuildScreen()

    def redrawAll(self):
        self.canvas.delete(ALL)
        if(self.debug): self.drawDebug()
        self.drawGame()
        

        

demo = PhysModuleDemo(750, 500)
demo.run()