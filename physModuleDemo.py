from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import time
import copy
import os
import string

#also from notes, #reads from a file
def readFile(filename, mode="rt"):
    # rt = "read text"
    with open(filename, mode) as fin:
        return fin.read()

#again, from notes, writes to a file
def writeFile(filename, contents, mode="wt"):
    # wt = "write text"
    with open(filename, mode) as fout:
        fout.write(contents)

#handles buttons (from HW 8/9 (the one with farm game))
class Button(object):
    #creates a button at x, y of specified dimensions with the given text and
    #color. selectedColor is what color the button is when selected.
    #id is an identifier for the button. 
    def __init__(self, x, y, width, height, margin, text, color, selectColor, identifier):
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
        #x and y of the middle of the bridge bed
        x = float(self.width/self.screenConversion)/2
        y = 2
        nodePoints = [(x-4, y, True),(x-2, y), (x, y), (x+2, y),(x+4, y, True),
                      (x-3, y+2), (x-1, y+2), (x+1, y+2), (x+3, y+2)]

        for point in nodePoints:
            if(len(point) == 3):
                (x, y, isFixed) = point
            else:
                (x, y) = point
                isFixed = False

            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,isFixed,
                              True))

        #indexes of the two nodes (in list "nodes")
        bedIndexes = [(0, 1), (1, 2), (2, 3), (3, 4)] 
        beamIndexes = [(0, 5), (5, 1), (1, 6), (6, 2), (2, 7), (7, 3), (3, 8),
                       (8, 4), (5, 6), (6, 7), (7, 8)]

        for indexes in bedIndexes:
            (node1Index, node2Index) = indexes
            BridgeBed(nodes[node1Index],nodes[node2Index], self.breakRatio, 
                      self.environ)

        for indexes in beamIndexes:
            (node1Index, node2Index) = indexes
            BridgeBeam(nodes[node1Index],nodes[node2Index], self.breakRatio, 
                      self.environ)

    #takes a list of tuples in text form and converts it to a regular list
    #assumes it is a list of tuples
    def textToList(self, text):
        #remove all spaces
        text = text.replace(" ", "")

        #remove parens around tuples and brackets around list
        text = text.replace("(", "")
        text = text.replace(")", "")
        text = text.replace("[", "")
        text = text.replace("]", "")

        numList = text.split(",")

        finalList = []
        for i in xrange(0, len(numList), 2):
            if("." in numList[i]): num1 = float(numList[i])
            else: num1 = int(numList[i])

            if("." in numList[i+1]): num2 = float(numList[i+1])
            else: num2 = int(numList[i+1])

            finalList.append((num1, num2))

        return finalList

    def getLevelInfo(self, path):
        #which line the lists are on in the file
        nodeListLineIndex = 0
        constraintListLineIndex = 1
        startNodeListLineIndex = 2
        highScoreIndex = 3

        text = readFile(path)
        text = text.splitlines()

        nodeList = self.textToList(text[nodeListLineIndex])
        constraintList = self.textToList(text[constraintListLineIndex])
        startNodeList = self.textToList(text[startNodeListLineIndex])
        highScore = text[highScoreIndex]

        return (nodeList, constraintList, startNodeList, highScore)

    def prepareLevel(self, nodePoints, constraintIndexes,startNodes,highScore):
        nodes = []
        for point in nodePoints:
            (x, y) = point
            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,True,
                              False))

        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(LandBeam(nodes[node1Index],nodes[node2Index], self.breakRatio, self.environ))

        self.placeStartNodes(startNodes)
        self.highScore = int(highScore)

    def placeStartNodes(self, nodePoints):
        for point in nodePoints:
            (x, y) = point
            self.selectedNode = Node(Vector(x, y), self.nodeMass, 
                                     self.environ, True)

        self.selectedNodeForce = Vector(0, 0)

    def initStartButtons(self):
        buttonWidth = 300
        buttonHeight = 75
        buttonMargin = 10

        x = self.width/2 - buttonWidth/2
        y = self.height / 3

        xIncrement = 0
        yIncrement = buttonHeight

        buttonIds = ["Play", "Make Level", "Help"]
        self.startButtons = []
        for identifier in buttonIds:
            self.startButtons.append(Button(x, y, buttonWidth, 
                                            buttonHeight, buttonMargin, 
                                            identifier, self.buttonColor, 
                                            self.buttonSelectedColor,
                                            identifier))
            x += xIncrement
            y += yIncrement 

    def getButtonList(self, x, y, xInc, yInc, width, height, margin, color,              selectedColor, idList, textList=None):
        if(textList == None): textList = idList
        #make sure there are enough lables for the buttons
        assert(len(textList) == len(idList))

        buttons = []
        for i in xrange(len(idList)):
            buttons.append(Button(x, y, width, height, margin, textList[i], color, selectedColor, idList[i]))
            x += xInc
            y += yInc

        return buttons

    def initMakeButtons(self):
        (x, y) = (0, 0)
        (xInc, yInc) = (0, self.buttonHeight)
        toggleIdList = ["Node", "Land"]
        toggleList = self.getButtonList(x, y, xInc, yInc, self.buttonWidth, 
                                        self.buttonHeight, self.buttonMargin, 
                                        self.buttonColor, 
                                        self.buttonSelectedColor, toggleIdList)

        self.terrainButtons = ToggleButtons(toggleList)

        makeButtonIdList = ["Save", "Name", "Quit"]
        self.makeButtons = self.getButtonList(x, y+yInc*2, xInc, yInc, 
                                              self.buttonWidth, 
                                              self.buttonHeight, 
                                              self.buttonMargin, 
                                              self.buttonColor, 
                                              self.buttonSelectedColor,
                                              makeButtonIdList)

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

        otherButtons = ["Test", "Play", "Menu"]
        for identifier in otherButtons:
            self.buildButtons.append(Button(x, y, self.buttonWidth, 
                                            self.buttonHeight, 
                                            self.buttonMargin, identifier, 
                                            self.buttonColor, 
                                            self.buttonSelectedColor, 
                                            identifier))
            x += xIncrement
            y += yIncrement

    def initTestButtons(self):
        (x, y) = (0, 0)
        self.testButtons = []
        self.testButtons.append(Button(x, y, self.buttonWidth, 
                                       self.buttonHeight,
                                       self.buttonMargin, "Build", 
                                       self.buttonColor,
                                       self.buttonSelectedColor, "Build"))

    def initLevelButtons(self):
        width = 300
        height = 75
        margin = 15
        color = "light green"
        (x, y) = (0, self.height/5)
        yInc = height

        self.levelButtons = []
        for level in self.levelList:
            #path is the identifier, name is the text on the button
            (path, name) = level
            self.levelButtons.append(Button(x, y, width, height, margin, name, 
                                            color, color, path))
            y += yInc

    def initButtons(self):
        self.buttonMargin = 5
        self.buttonWidth = 100
        self.buttonHeight = 40
        self.buttonColor = "blue"
        self.buttonSelectedColor = "green"
        
        self.initStartButtons()
        self.initBuildButtons()
        self.initTestButtons()
        self.initMakeButtons()

    #create the environment for the start screen
    def initStartEnviron(self):
        self.initEnviron()
        self.placeBridge()

    def initAnimation(self):
        #constants for noees/springs
        self.nodeMass = 10 #kg
        self.forceIncrement = 100 #how much the mass increases on a click
        self.breakRatio = 0.05

        self.gotoStartMode()

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

        self.isHelpShown = False

        self.levelFolder = "levels"
        self.levelPrefix = "level_"

        #the force applied to each no-movable node in connected to a bridge bed
        self.testForce = 0
        self.testForceIncrement = 100

    def getLevelName(self, path):
        key = self.levelPrefix
        keyIndex = path.find(key)
        levelIndex = keyIndex + len(key)
        fileExtensionLen = 4 #.txt
        return path[levelIndex:-fileExtensionLen]

    def initBuildMode(self, path):
        self.initEnviron()
        self.levelName = self.getLevelName(path)
        self.prepareLevel(*self.getLevelInfo(path))
        #make sure bed beams selected
        self.beamButtons.select("Bed")
        self.buildType = BridgeBed

        self.undoQue = []
        self.redoQue = []

    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    #handles mouse relesed whenever it is a construction mode
    def constructMouseReleased(self, event):
        if(self.tempNode != None):
            #check if the beam is too long
            if(self.mode == "make" or 
               self.tempConstraint.getLength() < self.maxBeamLen):
                selection = self.environ.getClickedObj(event.x, event.y)
                if(selection != None and isinstance(selection, Node)):
                    #if the original node was ended on then delete 
                    self.tempNode.delete()
                    #only make new constraint if the start node 
                    #wasn't ended on
                    if(not (selection == self.startNode)):
                        self.undoQue.append((self.buildType(self.startNode, 
                                            selection, self.breakRatio, 
                                            self.environ),))
                    elif(self.mode == "make" and len(self.startNode.constraints) == 0):
                        self.startNode.delete()

                else:
                    self.tempNode.visible = True
                    self.undoQue.append((self.tempConstraint, self.tempNode))
            else:
                self.tempNode.delete()
            #reset temp variables
            self.tempConstraint = None
            self.tempNode = None
            self.startNode = None
            self.redoQue = []

    def onBuildMouseReleased(self, event):
        self.constructMouseReleased(event)

    def onMakeMouseReleased(self, event):
        self.constructMouseReleased(event)

    def onMouseReleased(self, event):
        if(self.mode == "build"):
            self.onBuildMouseReleased(event)
        elif(self.mode == "make"):
            self.onMakeMouseReleased(event)

    def constructMouseDrag(self, event):
        if(self.tempNode != None):
            self.tempNode.position = self.environ.getVect(event.x, event.y)
            if(self.tempConstraint.getLength() > self.maxBeamLen and self.mode != "make"):
                self.tempConstraint.color = "red"
            else:
                self.tempConstraint.color = self.tempConstraint.baseColor

    def onBuildMouseDrag(self, event):
        self.constructMouseDrag(event)

    def onMakeMouseDrag(self, event):
        self.constructMouseDrag(event)

    def onMouseDrag(self, event):
        if(self.mode == "build"):
            self.onBuildMouseDrag(event)
        elif(self.mode == "make"):
            self.onMakeMouseDrag(event)

    def updateBeamButtons(self, event):
        self.beamButtons.update(event.x, event.y)
        if(self.beamButtons.selectedId == "Beam"):
            self.buildType = BridgeBeam
        elif(self.beamButtons.selectedId == "Bed"):
            self.buildType = BridgeBed

    #checks to see if a list of buttons was clicked
    #returns the identifier of the clicked button or none
    def checkButtonList(self, buttons, event):
        buttonId = None
        for button in buttons:
            if(button.isClicked(event.x, event.y)):
                buttonId = button.id
                break

        return buttonId

    #check build buttons,respond appropriately, return true if a button pressed
    def checkBuildButtons(self, event):
        buttonId = self.checkButtonList(self.buildButtons, event)

        if(buttonId == "Play"):
            self.gotoPlayMode()
        elif(buttonId == "Menu"):
            self.initAnimation()
        elif(buttonId == "Test"):
            self.gotoTestMode()

        return buttonId != None

    #construct a bridge or terrain
    def constructMousePressed(self, event):
        selection = self.environ.getClickedObj(event.x, event.y)
        pos = self.environ.getVect(event.x, event.y)
        if(self.buildType != Node):
            #if it is a node that can be selected
            if(isinstance(selection, Node) and selection.color == "black"):
                if(self.tempConstraint == None):
                    #make new node/constraint
                    self.startNode = selection
                    self.tempNode = Node(pos, self.nodeMass, self.environ,
                                         False, False)
                    self.tempConstraint = self.buildType(self.startNode, 
                                                     self.tempNode,
                                                     self.breakRatio, 
                                                     self.environ)
            elif(self.mode == "make"):
                pos = self.environ.getVect(event.x, event.y)
                #create a new startNode, tempNode, and constraint
                self.startNode = Node(pos, self.nodeMass, self.environ,
                                      True, True)
                self.tempNode = Node(pos, self.nodeMass, self.environ,
                                     True, False)
                self.tempConstraint = self.buildType(self.startNode,
                                                     self.tempNode,
                                                     self.breakRatio,
                                                     self.environ)
        else:
            self.undoQue.append((Node(pos, self.nodeMass, self.environ, True, True, "brown"),))

    def onBuildMousePressed(self, event):
        self.updateBeamButtons(event)

        #if none of the buttons clicked, then check if the bridge was being
        #built
        if(not self.checkBuildButtons(event)):
            self.constructMousePressed(event)

    def checkTestButtons(self, event):
        buttonId = self.checkButtonList(self.testButtons, event)

        if(buttonId == "Build"):
            self.gotoBuildMode()

        return (buttonId != None)

    def initLevelList(self):
        path = self.levelFolder
        prefixLen = 6 #prefix to each file is level_
        postfixLen = 4 #len of file extension
        self.levelList = []
        for fileName in os.listdir(path):
            filePath = path + os.sep + fileName
            if(not os.path.isdir(filePath) and fileName[:prefixLen]==self.levelPrefix):
                self.levelList.append((filePath, 
                                       fileName[prefixLen:-postfixLen]))

    def gotoPickMode(self):
        self.mode = "pick"
        self.initLevelList()
        #so buttons are most updated
        self.initLevelButtons()

    #add a weight to the environment and increment score if needed
    def addWeight(self, event):
        pos = self.environ.getVect(event.x, event.y)

        Weight(pos, self.nodeMass*10, self.environ)

    def onPlayMousePressed(self, event):
        if(not self.checkTestButtons(event)):
            self.addWeight(event)

    def onStartMousePressed(self, event):
        buttonId = self.checkButtonList(self.startButtons, event)

        if(buttonId == "Play"):
            self.gotoPickMode()
        elif(buttonId == "Help"):
            self.isHelpShown = True
        elif(buttonId == "Make Level"):
            self.gotoMakeMode()
        else:
            self.addWeight(event)

    def onPickMousePressed(self, event):
        buttonId = self.checkButtonList(self.levelButtons, event)

        if(buttonId != None):
            self.gotoBuildMode(buttonId)
        else:
            self.addWeight(event)

    def updateTerrainButtons(self, event):
        self.terrainButtons.update(event.x, event.y)
        if(self.terrainButtons.selectedId == "Land"):
            self.buildType = LandBeam
        elif(self.terrainButtons.selectedId == "Node"):
            self.buildType = Node

    def saveTerrain(self):
        terrainNodes = []
        constraints = []
        startNodes = []
        highScore = 0
        for obj in self.environ.objects:
            if(isinstance(obj, Node)):
                if(obj.color == "black"):
                    terrainNodes.append(obj.position.getXY())
                else:
                    startNodes.append(obj.position.getXY())

        #go through constraints and find their nodes
        for index in self.environ.constraintIndexes:
            constraint = self.environ.objects[index]
            (node1, node2) = (constraint.nodes[0], constraint.nodes[1])
            node1Pos = node1.position.getXY() 
            node2Pos = node2.position.getXY()
            nodeIndexes = [-1, -1]
            for i in xrange(len(terrainNodes)):
                if(terrainNodes[i] == node1Pos):
                    nodeIndexes[0] = i
                elif(terrainNodes[i] == node2Pos):
                    nodeIndexes[1] = i
            constraints.append(tuple(nodeIndexes))

        fileContents = str(terrainNodes) + "\n" + str(constraints) + "\n" + str(startNodes) + "\n" + str(highScore)

        fileName = self.levelPrefix + self.levelName + ".txt"
        path = self.levelFolder + os.sep + fileName
        writeFile(path, fileContents)
        assert(os.path.exists(path))

    def onMakeMousePressed(self, event):
        selectedButton = self.terrainButtons.selectedId
        self.updateTerrainButtons(event)
        #check other buttons only if terrain buttons not clicked
        if(selectedButton == self.terrainButtons.selectedId):
            buttonId = self.checkButtonList(self.makeButtons, event)
            if(buttonId == "Quit"):
                self.gotoStartMode()
            elif(buttonId == "Save"):
                self.saveTerrain()
            elif(buttonId == "Name"):
                self.isNaming = not self.isNaming 
            else:
                self.constructMousePressed(event)

    def onTestMousePressed(self, event):
        if(not self.checkTestButtons(event)):
            self.testForce += self.testForceIncrement
            self.score += 1

    def onMousePressed(self, event):
        if(self.mode == "build"):
            self.onBuildMousePressed(event)
        elif(self.mode == "play"):
            self.onPlayMousePressed(event)
        elif(self.mode == "start"):
            self.onStartMousePressed(event)
        elif(self.mode == "pick"):
            self.onPickMousePressed(event)
        elif(self.mode == "make"):
            self.onMakeMousePressed(event)
        elif(self.mode == "test"):
            self.onTestMousePressed(event)

    def gotoMakeMode(self):
        self.mode = "make"
        self.levelName = "untitled"
        self.isNaming = False
        self.terrainButtons.select("Land")
        self.buildType = LandBeam
        self.initEnviron()
        self.undoQue = []
        self.redoQue = []

    def gotoStartMode(self):
        self.mode = "start"
        self.initStartEnviron()
        self.environ.start()

    #go through all objects in the environment and find all nodes
    #connected to a bridge beam. return them as a list
    def getBedNodeList(self):
        bedNodes = []
        for obj in self.environ.objects:
            if(isinstance(obj, Node) and not obj.isFixed):
                #now check if it has a bed beam
                for beam in obj.constraints:
                    if(isinstance(beam, BridgeBed)):
                        bedNodes.append(obj)
                        break

        return bedNodes

    def gotoTestMode(self):
        if(self.environ.doesBridgeCover(self.width)):
            print "bridge covers"
            self.mode = "test"
            self.score = 0
            self.testForce = 0
            self.buildEnviron = copy.deepcopy(self.environ)
            self.bedNodes = self.getBedNodeList()
            self.environ.start()
        else:
            print "bridge does not cover"
            #alert box

    def gotoPlayMode(self):
        self.mode = "play"
        self.buildEnviron = copy.deepcopy(self.environ)
        self.environ.start()

    #go to build mode with the terrain in the file at the given path
    def gotoBuildMode(self, path=None):
        self.mode = "build"
        if(self.buildEnviron != None):
            self.environ = self.buildEnviron
            #clear out ques
            self.undoQue = []
            self.redoQue = []
        elif(path != None):
            self.initBuildMode(path)
        else:
            raise Exception("no level to load D:")
        self.isGameOver = False
        self.score = 0

    def restartLevel(self):
        self.buildEnviron = None
        self.gotoBuildMode()

    def restartSim(self):
        self.environ = self.buildEnviron
        self.environ.start()
        self.score = 0
        self.isGameOver = False

    def onStartKeyPress(self, event):
        if(event.keysym == "space" or event.keysym == "s"):
            self.gotoBuildMode()

    def onTestKeyPress(self, event):
        if(event.keysym == "b"):
            self.gotoBuildMode()
        elif(event.keysym == "r"):
            self.restartSim()
        elif(event.keysym == "p"):
            self.environ.pause()

    def undoMove(self):
        if(len(self.undoQue) > 0):
            objToRemove = list(self.undoQue.pop())
            #check if both nodes of the constraint should be deleted
            if(self.mode == "make"):
                for obj in objToRemove:
                    if(isinstance(obj, Constraint)):
                        for node in obj.nodes:
                            if(node not in objToRemove and len(node.constraints) == 1):
                                objToRemove.append(node)

            for obj in objToRemove:
                self.environ.deleteObj(obj, obj.environIndex)

            self.redoQue.append(tuple(objToRemove))

    def redoMove(self):
        if(len(self.redoQue) > 0):
            objToAdd = self.redoQue.pop()
            for obj in objToAdd:
                obj.environIndex = self.environ.add(obj)

            self.undoQue.append(objToAdd)

    def switchDebug(self):
        self.debug = not self.debug
        self.environ.debug = not self.environ.debug

    def onBuildKeyPress(self, event):
        if(event.keysym == "c"):
            self.restartLevel()
        elif(event.keysym == "s"):
            self.gotoPlayMode()
        elif(event.keysym == "d"):
            self.switchDebug()
        elif(event.keysym == "u"):
            self.undoMove()
        elif(event.keysym == "r"):
            self.redoMove()

    def onNamingKeyPress(self, event):
        if(event.keysym == "BackSpace" and len(self.levelName) > 0):
            self.levelName = self.levelName[:-1]
        elif(event.keysym in string.printable):
            self.levelName += event.keysym

    def onMakeKeyPress(self, event):
        if(self.isNaming):
            self.onNamingKeyPress(event)
        else:
            if(event.keysym == "u"):
                self.undoMove()
            elif(event.keysym == "r"):
                self.redoMove()
            elif(event.keysym == "d"):
                self.switchDebug()

    def onKeyPressed(self, event):
        if(event.keysym == "h" or event.keysym == "question"):
            self.isHelpShown = not self.isHelpShown
        elif(self.mode == "start"):
            self.onStartKeyPress(event)
        elif(self.mode == "play"):
            self.onTestKeyPress(event)
        elif(self.mode == "build"):
            self.onBuildKeyPress(event)
        elif(self.mode == "make"):
            self.onMakeKeyPress(event)

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

    def updateHighScore(self, newScore):
        filePath = (self.levelFolder + os.sep + self.levelPrefix + 
                    self.levelName + ".txt")
        highScoreIndex = 3

        contents = readFile(filePath)
        contents = contents.splitlines()
        #update high schore
        self.highScore = self.score
        contents[highScoreIndex] = str(self.highScore)
        contents = "\n".join(contents)

        writeFile(filePath, contents)

    def onTimerFired(self):
        if(self.mode in ["play", "start", "pick", "test"]):
            #add force to all bed Nodes if the game isn't over
            if(self.mode == "test" and not self.isGameOver):
                for node in self.bedNodes:
                    node.addForce(Vector(0, -self.testForce))

            #if anything
            isBroken = self.environ.update(self.dt, self.width, self.height)
            
            if(isBroken and self.mode == "test"): 
                self.isGameOver = True
                if(self.score > self.highScore):
                    self.gameOverText = "New High Score!"
                    self.updateHighScore(self.score)
                else:
                    self.gameOverText = "Game Over"

    def drawDebug(self):
        #unit square for scale
        r = self.screenConversion
        self.canvas.create_rectangle(0, 0, r, r, fill="red")
        #frame rate
        self.canvas.create_text(0, 0, text=("%.2f" % self.fps), anchor=NW,
                                font="Arial 20 bold")

    def drawGameOver(self):
        (x, y) = (self.width/2, self.height/2)
        self.canvas.create_text(x, y, text=self.gameOverText, 
                                font="Arial 30 bold", fill="black")

    def drawScore(self):
        (x, y) = (self.width, 0)
        lineHeight = 30
        scoreText = "Score: %d" % self.score
        highScoreText = "HighScore: %d" % self.highScore

        self.canvas.create_text(x, y, text=scoreText, font="Arial 15 bold",
                                fill="black", anchor=NE)
        y += lineHeight
        self.canvas.create_text(x, y, text=highScoreText, font="Arial 15 bold",
                                fill="black", anchor=NE)

    def drawStartScreen(self):
        (x, y) = (self.width/2, self.height/10)
        self.canvas.create_text(x, y, anchor=N, text="PyBridge", 
                                font="Arial 50 bold")

        for button in self.startButtons:
            button.draw(self.canvas)

    def drawLevelName(self, color="black"):
        (x, y) = (self.buttonWidth, 0)
        self.canvas.create_text(x, y, text=self.levelName, anchor=NW, 
                           font="Arial 30 bold", fill=color)

    def drawBuildScreen(self):
        self.beamButtons.draw(self.canvas)
        for button in self.buildButtons:
            button.draw(self.canvas)

        self.drawLevelName()

    def drawTestScreen(self):
        if(self.isGameOver): self.drawGameOver()
        self.drawScore()
        for button in self.testButtons:
            button.draw(self.canvas)

        self.drawLevelName()

    def drawPlayScreen(self):
        for button in self.testButtons:
            button.draw(self.canvas)

        self.drawLevelName()

    def drawHelpScreen(self):
        #one is largest text, two is second largest, etc
        title = 1
        subTitle = 2
        normText = 3

        #list of tuples ("text", textSize)
        helpText = [("Help", title), 
                    ("press h or ? to show/hide the help screen", normText),
                    ("", normText), 
                    ("Build Screen", subTitle), 
                    ("Click on a black dot to start a bridge beam", normText),
                    ("Drag and release to create the beam", normText),
                    ("Oversized beams will be red and not stay", normText),
                    ("Click on the \"Beam\" and \"Bed\" buttons", normText),
                    ("to switch which beam you create", normText),
                    ("Beams don't collide with objects, but bridge beds do",
                     normText), ("Test Screen", subTitle),
                    ("Click to drop a weight onto the bridge", normText)]

        startHeight = 30
        (x, y) = (self.width/2, startHeight)
        for line in helpText:
            (text, weight) = line
            if(weight == 1): 
                font = "Arial 30 bold"
                lineHeight = 70
            elif(weight == 2):
                font = "Arial 20 bold"
                lineHeight = 40
            elif(weight == 3):
                font = "Arial 15"
                lineHeight = 25

            self.canvas.create_text(x, y, text=text, font=font, anchor=N)
            y += lineHeight

    def drawButtons(self, buttons):
        for button in buttons:
            button.draw(self.canvas)

    def drawPickScreen(self):
        self.canvas.create_text(0, 0, text="Pick a Level", anchor=NW, 
                           font="Arial 40 bold")

        self.drawButtons(self.levelButtons)

    def drawMakeScreen(self):
        self.terrainButtons.draw(self.canvas)
        self.drawButtons(self.makeButtons)
        if(self.isNaming):
            self.drawLevelName("blue")
        else:
            self.drawLevelName()

    def drawGame(self):
        if(self.isHelpShown):
            self.drawHelpScreen()
            return
        
        self.environ.draw(self.canvas, self.debug)
        if(self.mode == "start"):
            self.drawStartScreen()
        if(self.mode == "build"):
            self.drawBuildScreen()
        elif(self.mode == "play"):
            self.drawPlayScreen()
        elif(self.mode == "pick"):
            self.drawPickScreen()
        elif(self.mode == "make"):
            self.drawMakeScreen()
        elif(self.mode == "test"):
            self.drawTestScreen()

    def redrawAll(self):
        self.canvas.delete(ALL)
        if(self.debug): self.drawDebug()
        self.drawGame()

def testTextToList():
    print "Testing textToList...",
    c = PhysModuleDemo()
    text = "[(1, 3), (3, 0), (1, 3), (1, 4)]"
    print c.textToList(text)
    assert(c.textToList(text) == eval(text))
    print "...passed!"

def testInitLevelList():
    print "Testing initLevelList...",
    c = PhysModuleDemo()
    c.initLevelList()
    assert(c.levelList == [("levels\\level_1.txt", "1"), 
                           ("levels\\level_terrain.txt", "terrain")])

demo = PhysModuleDemo(1250, 750)
demo.run()