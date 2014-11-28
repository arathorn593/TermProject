from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time
import copy

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

    def placeTerrain(self):
        nodePoints = [(0, 8.5), (5,8.5), (5, 7), (15, 8.5), (15, 7), (25, 8.5), (5, 0), (15, 0)]

        nodes = []
        for point in nodePoints:
            (x, y) = point
            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,True,
                              False))

        constraintIndexes = [(0, 1), (1, 2), (2, 6), (3, 4), (4, 7), (3, 5)]
        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(LandBeam(nodes[node1Index],nodes[node2Index], self.breakRatio, self.environ))

    def placeStartNodes(self):
        nodePoints = [(5,8.5), (5, 7), (15, 8.5), (15, 7)]
        
        for point in nodePoints:
            (x, y) = point
            self.selectedNode = Node(Vector(x, y), self.nodeMass, 
                                     self.environ, True)

        self.selectedNodeForce = Vector(0, 0)

    def initStartButtons(self):
        x = self.width/2 - self.buttonWidth/2
        y = self.height / 3
        xIncrement = 0
        yIncrement = self.buttonMargin + self.buttonHeight

        buttonIds = ["Play", "Help"]
        self.startButtons = []
        for identifier in buttonIds:
            self.startButtons.append(Button(x, y, self.buttonWidth, 
                                            self.buttonHeight, 
                                            self.buttonMargin, identifier,
                                            self.buttonColor, 
                                            self.buttonSelectedColor,
                                            identifier))
            x += xIncrement
            y += yIncrement 


    def initBuildButtons(self):
        (x, y) = (0, 0)
        self.buildButtons = []
        xIncrement = 0
        yIncrement = self.buttonMargin + self.buttonHeight
        buttonIds = ["Beam", "Bed"]
        buttons = []        

        for identifier in buttonIds:
            buttons.append(Button(x, y, self.buttonWidth, self.buttonHeight, 
                                  self.buttonMargin, identifier, 
                                  self.buttonColor, 
                                  self.buttonSelectedColor, identifier))
            x += xIncrement
            y += yIncrement

        self.beamButtons = ToggleButtons(buttons)
        self.beamButtons.select("Bed")

        self.buildButtons.append(Button(x, y, self.buttonWidth, 
                                        self.buttonHeight,
                                        self.buttonMargin, "Test", 
                                        self.buttonColor,
                                        self.buttonSelectedColor, "Test"))

    def initTestButtons(self):
        (x, y) = (0, 0)
        self.testButtons = []
        self.testButtons.append(Button(x, y, self.buttonWidth, 
                                       self.buttonHeight,
                                       self.buttonMargin, "Build", 
                                       self.buttonColor,
                                       self.buttonSelectedColor, "Build"))



    def initButtons(self):
        self.buttonMargin = 5
        self.buttonWidth = 100
        self.buttonHeight = 40
        self.buttonColor = "blue"
        self.buttonSelectedColor = "green"
        
        self.initStartButtons()
        self.initBuildButtons()
        self.initTestButtons()

    def initAnimation(self):
        #constants for noees/springs
        self.nodeMass = 10 #kg
        self.forceIncrement = 100 #how much the mass increases on a click
        self.breakRatio = 0.05

        self.mode = "start"

        self.initEnviron()

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
        self.maxBeamLen = 3
        self.buildEnviron = None

    def initBuildMode(self):
        self.placeTerrain()
        self.placeStartNodes()

    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    def onMouseReleased(self, event):
        if(self.mode == "build"):
            if(self.tempNode != None):
                #check if the beam is too long
                if(self.tempConstraint.getLength() < self.maxBeamLen):
                    selection = self.environ.getClickedObj(event.x, event.y)
                    if(selection != None and isinstance(selection, Node)):
                        #if the original node was ended on then delete 
                        self.tempNode.delete()
                        #only make new constraint if the start node 
                        #wasn't ended on
                        if(not (selection == self.startNode)):
                            self.buildType(self.startNode, selection, 
                                           self.breakRatio, self.environ)

                    else:
                        self.tempNode.visible = True
                else:
                    self.tempNode.delete()
                #reset temp variables
                self.tempConstraint = None
                self.tempNode = None
                self.startNode = None

    def onMouseDrag(self, event):
        if(self.tempNode != None and self.mode == "build"):
            self.tempNode.position = self.environ.getVect(event.x, event.y)
            if(self.tempConstraint.getLength() > self.maxBeamLen):
                self.tempConstraint.color = "red"
            else:
                self.tempConstraint.color = self.tempConstraint.baseColor

    def onMousePressed(self, event):
        if(self.mode == "build"):
            #if(self.testButton.isClicked(event.x, event.y)):
            #    self.gotoTestMode()
            self.beamButtons.update(event.x, event.y)
            if(self.beamButtons.selectedId == "Beam"):
                self.buildType = BridgeBeam
            elif(self.beamButtons.selectedId == "Bed"):
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
            if(False):#self.buildButton.isClicked(event.x, event.y)):
                pass#self.gotoBuildMode()
            else:
                pos = self.environ.getVect(event.x, event.y)

                Weight(pos, self.nodeMass*10, self.environ)
                if(not self.isGameOver):
                    self.score += 1
            #self.placeBox(event.x, event.y)
            #self.selectedNodeForce += Vector(0, -self.forceIncrement*2)

    def gotoTestMode(self):
        self.mode = "test"
        self.buildEnviron = copy.deepcopy(self.environ)
        self.environ.start()

    def gotoBuildMode(self):
        self.mode = "build"
        if(self.buildEnviron != None):
            self.environ = self.buildEnviron
        else:
            self.initBuildMode()
        self.isGameOver = False
        self.score = 0            

    def onStartKeyPress(self, event):
        pass
    def onTestKeyPress(self, event):
        pass


    def onBuildKeyPress(self, event):
        pass

    def onKeyPressed(self, event):
        if(self.mode == "start"):
            self.onStartKeyPress(event)
        elif(self.mode == "test"):
            self.onTestKeyPress(event)
        elif(self.mode == "build"):
            self.onBuildKeyPress(event)

        if(event.keysym == "r"):
            self.initAnimation()
        elif(event.keysym == "s"):
            if(self.mode == "start"):
                self.gotoBuildMode()
            else:
                self.gotoTestMode()
        elif(event.keysym == "b"):
            if(self.mode == "test"):
                self.gotoBuildMode()
        elif(event.keysym == "d"):
            self.debug = not self.debug
            self.environ.debug = not self.environ.debug
        elif(event.keysym == "p"):
            self.environ.pause()

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

        self.timerDelay = 10#max(frameRemaining, 1)

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

    def drawStartScreen(self):
        self.canvas.create_text(0, 0, anchor=NW, text="START")
        for button in self.startButtons:
            button.draw(self.canvas)

    def drawBuildScreen(self):
        self.beamButtons.draw(self.canvas)
        for button in self.buildButtons:
            button.draw(self.canvas)

    def drawTestScreen(self):
        for button in self.testButtons:
            button.draw(self.canvas)

    def drawGame(self):
        self.drawScore()
        self.environ.draw(self.canvas, self.debug)
        if(self.isGameOver): self.drawGameOver()
        if(self.mode == "start"):
            self.drawStartScreen()
        if(self.mode == "build"):
            self.drawBuildScreen()
        elif(self.mode == "test"):
            self.drawTestScreen()

    def redrawAll(self):
        self.canvas.delete(ALL)
        if(self.debug): self.drawDebug()
        self.drawGame()
        

        

demo = PhysModuleDemo(1250, 750)
demo.run()