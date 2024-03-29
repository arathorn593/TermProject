from eventBasedAnimationClass import EventBasedAnimationClass
from physics import *
from Tkinter import *
import tkMessageBox
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
    def __init__(self, x, y, width, height, margin, text, color, selectColor, 
                 identifier, textColor=None):
        (self.x0, self.y0) = (x + margin, y + margin)
        (self.x1, self.y1) = (self.x0+width-margin*2, self.y0+height-margin*2)

        self.text = text

        self.color = color
        self.selectedColor = selectColor
        #initialize text color
        if(textColor == None):
            if(self.color in ["black", "blue"]):
                self.textColor = "white"
            else:
                self.textColor = "black"
        else:
            self.textColor = textColor
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

        canvas.create_text(cx, cy, text=self.text, font="Arial 15", 
                           fill=self.textColor)

#this is a class that is a list of buttons where only one can be selected 
#*args is a list of buttons
class ToggleButtons(object):
    def __init__(self, *args):
        #if there is only one argument that is a list, that argument becomes
        #the button list
        if(len(args) == 1 and type(args[0]) == list or type(args[0]) == tuple):
            args = args[0]

        self.buttons = list(args)
        self.selectedId = None

    #update which button is selected given the x, y coordinates
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

    #draw all the buttons (button that is selected draws itself a dif color)
    def draw(self, canvas):
        for button in self.buttons:
            button.draw(canvas)

    #selects a certain button (for setting default selections)
    def select(self, identifier):
        for button in self.buttons:
            if(button.id == identifier):
                button.selected = True
                self.selectedId = identifier

class PyBridge(EventBasedAnimationClass):
    #set up the environment for the physics simulation
    def initEnviron(self):
        self.screenConversion = 50 #pixels/meter

        self.gravity = 5 #m/s**2

        #create an environment with the origin in the lower left
        self.environ = PhysEnvironment(self.gravity, self.screenConversion,
                                           0, self.height)

    #takes a list of tuples (x, y) or (x, y, True) for fixed nodes
    #and returns a list of node objects (well...references to node objects)
    def getNodeList(self, pointList):
        nodes = []
        #create all of the nodes
        for point in pointList:
            if(len(point) == 3):
                (x, y, isFixed) = point
            else:
                (x, y) = point
                isFixed = False

            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,isFixed,
                              True))

        return nodes

    #places the truss bridge that is at the bottom of the start & pick screens
    def placeBridge(self):
        #x and y of the middle of the bridge bed
        x = float(self.width/self.screenConversion)/2
        y = 2

        #points for the nodes of the bridge (true element if they are fixed)
        nodePoints = [(x-4, y, True),(x-2, y), (x, y), (x+2, y),(x+4, y, True),
                      (x-3, y+2), (x-1, y+2), (x+1, y+2), (x+3, y+2)]

        nodes = self.getNodeList(nodePoints)

        #indexes of the two nodes (in list "nodes")
        bedIndexes = [(0, 1), (1, 2), (2, 3), (3, 4)] 
        beamIndexes = [(0, 5), (5, 1), (1, 6), (6, 2), (2, 7), (7, 3), (3, 8),
                       (8, 4), (5, 6), (6, 7), (7, 8)]

        #create the constraints
        for indexes in bedIndexes:
            (node1Index, node2Index) = indexes
            BridgeBed(nodes[node1Index],nodes[node2Index], self.breakRatio, 
                      self.environ)

        for indexes in beamIndexes:
            (node1Index, node2Index) = indexes
            BridgeBeam(nodes[node1Index],nodes[node2Index], self.breakRatio, 
                      self.environ)

    #takes a list in text form and convert it to a list of numbers
    #if there were sublists or tuples, the elements in those are just
    #added to the number list where the tuple or sub list was
    def textToList(self, text):
        #remove all spaces
        text = text.replace(" ", "")

        #remove parens around tuples and brackets around list
        text = text.replace("(", "")
        text = text.replace(")", "")
        text = text.replace("[", "")
        text = text.replace("]", "")

        numList = text.split(",")

        #convert the strings to numbers
        for i in xrange(len(numList)):
            if("." in numList[i]):
                numList[i] = float(numList[i])
            else:
                numList[i] = int(numList[i])

        return numList

    #takes a list of tuples in text form and converts it to a regular list
    #assumes it is a list of tuples
    def textToTupleList(self, text):
        numList = self.textToList(text)

        #pair off the nubmers again (since they were unpaired when converted
        #to a number list)
        finalList = []
        for i in xrange(0, len(numList), 2):
            finalList.append((numList[i], numList[i+1]))

        return finalList

    #takes a path to a level file and returns a tuple of the node list, 
    #constraint list, start node list, and high score
    def getLevelInfo(self, path):
        #which line the lists are on in the file
        nodeListLineIndex = 0
        constraintListLineIndex = 1
        startNodeListLineIndex = 2
        highScoreIndex = 3

        text = readFile(path)
        text = text.splitlines()

        nodeList = self.textToTupleList(text[nodeListLineIndex])
        constraintList = self.textToTupleList(text[constraintListLineIndex])
        startNodeList = self.textToList(text[startNodeListLineIndex])
        highScore = text[highScoreIndex]

        return (nodeList, constraintList, startNodeList, highScore)

    #takes the appropriate lists and creates adds the specified objects to 
    #the environment. Also sets up high score
    def prepareLevel(self, nodePoints, constraintIndexes,startNodes,highScore):
        nodes = []
        #create list of nodes
        for point in nodePoints:
            (x, y) = point
            nodes.append(Node(Vector(x, y),self.nodeMass,self.environ,True,
                              False))

        #create land beams
        constraints = []
        for indexes in constraintIndexes:
            (node1Index, node2Index) = indexes
            constraints.append(LandBeam(nodes[node1Index],nodes[node2Index], 
                                        self.breakRatio, self.environ))

        #convert given nodes to fixed nodes
        for index in startNodes:
            nodes[index].visible = True

        self.highScore = int(highScore)

    #set up the buttons for the start menu
    def initStartButtons(self):
        #drawing constants
        buttonWidth = 300
        buttonHeight = 75
        buttonMargin = 10

        #start x, y
        x = self.width/2 - buttonWidth/2
        y = self.height / 3

        xIncrement = 0
        yIncrement = buttonHeight

        #ids/text for the buttons
        buttonIds = ["Play", "Make Level", "Help"]

        self.startButtons = self.getButtonList(x, y, xIncrement, yIncrement, 
                                               buttonWidth, buttonHeight, 
                                               buttonMargin, self.buttonColor, 
                                               self.buttonSelectedColor, 
                                               buttonIds)

    #creates a list of buttons from the given info. 
    #idList is the list of ids to use for the buttons and textList is the list
    #of text for the buttons. if no text list, idList is used for text too
    def getButtonList(self, x, y, xInc, yInc, width, height, margin, color,
                      selectedColor, idList, textList=None):
        #if no textList given, use the idList
        if(textList == None): textList = idList
        #make sure there are enough lables for the buttons
        assert(len(textList) == len(idList))

        buttons = []
        #add buttons to list
        for i in xrange(len(idList)):
            buttons.append(Button(x, y, width, height, margin, textList[i], 
                                  color, selectedColor, idList[i]))
            x += xInc
            y += yInc

        return buttons

    #set up buttons for the make screen
    def initMakeButtons(self):
        (x, y) = (0, 0)
        (xInc, yInc) = (0, self.buttonHeight)
        #set up toggle buttons
        toggleIdList = ["Node", "Land"]
        toggleList = self.getButtonList(x, y, xInc, yInc, self.buttonWidth, 
                                        self.buttonHeight, self.buttonMargin, 
                                        self.buttonColor, 
                                        self.buttonSelectedColor, toggleIdList)

        self.terrainButtons = ToggleButtons(toggleList)

        #set up other buttons (takin into account they are two below the top
        #of the toggle buttons since there are two toggle buttons)
        makeButtonIdList = ["Save", "Name", "Quit"]
        self.makeButtons = self.getButtonList(x, y+yInc*len(toggleIdList), 
                                              xInc, yInc, self.buttonWidth, 
                                              self.buttonHeight, 
                                              self.buttonMargin, 
                                              self.buttonColor, 
                                              self.buttonSelectedColor,
                                              makeButtonIdList)

    #set up buttons for build screen
    def initBuildButtons(self):
        (x, y) = (0, 0)
        xInc = 0
        yInc = self.buttonMargin + self.buttonHeight

        #set up toggle buttons for beam selection
        buttonIds = ["Beam", "Bed"]
        buttons = self.getButtonList(x, y, xInc, yInc, self.buttonWidth, 
                                    self.buttonHeight, self.buttonMargin, 
                                    self.buttonColor, 
                                    self.buttonSelectedColor, buttonIds)

        self.beamButtons = ToggleButtons(buttons)
        self.beamButtons.select("Bed")

        #set up other build buttons
        otherIds = ["Test", "Play", "Clear", "Menu"]
        self.buildButtons = self.getButtonList(x, y+yInc*len(buttonIds), 
                                               xInc, yInc, self.buttonWidth, 
                                               self.buttonHeight, 
                                               self.buttonMargin, 
                                               self.buttonColor, 
                                               self.buttonSelectedColor, 
                                               otherIds)

    #set up buttons for testing mode
    def initTestButtons(self):
        (x, y) = (0, 0)
        self.testButtons = []
        #test mode only has one button
        self.testButtons.append(Button(x, y, self.buttonWidth, 
                                       self.buttonHeight,
                                       self.buttonMargin, "Build", 
                                       self.buttonColor,
                                       self.buttonSelectedColor, "Build"))

    #set up the buttons for pick mode
    def initPickButtons(self):
        #non-default drawing constants
        width = 300
        height = 75
        margin = 15
        #different color for menu button
        menuColor = "blue"
        color = "green"
        (x, y) = (0, self.height/8)

        xInc = 0
        yInc = height

        self.pickButtons = []
        self.pickButtons.append(Button(x, y, width, height, margin, "Menu",
                                        menuColor, menuColor, "Menu"))
        y += yInc

        (idList, textList) = zip(*self.levelList)
        (idList, textList) = (list(idList), list(textList))

        #add on the level buttons
        self.pickButtons += self.getButtonList(x, y, xInc, yInc, width, 
                                               height, margin, color, color, 
                                               idList, textList)

    #initialize all buttons and button constants (except for pick buttons 
    #since they are initialized on the fly so the most updated level list is 
    #shown)
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

    def initTimingConstants(self):
        self.dt = 1/30.0 #seconds (30 fps (for physics simulation))
        self.timerDelay = 10

        self.startTime = time.time()
        self.fps = 0

    def initPhysConstants(self):
        #constants for nodes/springs
        self.nodeMass = 10 #kg
        self.weightIncrement = 100 #how much the mass increases on a click
        self.breakRatio = 0.05
        self.weightUnits = "kg"

    #initialize variables used in the game
    def initGameVariables(self):
        self.tempConstraint = None
        self.tempNode = None
        self.startNode = None

        self.debug = False
        self.isGameOver = False

        self.score = 0

        #type of object to build with
        self.buildType = None
        self.buildEnviron = None
        self.isHelpShown = False
        #the total force applied to the movable bridge bed nodes
        self.testWeight = 0

        #path to the level file
        self.levelPath = None

    #initialize constants used in the game
    def initGameConstants(self):
        self.initButtons()
        
        self.maxBeamLen = 3        

        self.levelFolder = "levels"
        self.levelPrefix = "level_"
        self.fixedNodeColor = "brown"
        self.nodeColor = "black"

        #how much self.testWeight is increased each click
        self.testWeightIncrement = 250

        #one is largest text, two is second largest, etc
        self.titleWeight = 1
        self.subTitleWeight = 2
        self.normTextWeight = 3

    #initialize the animation constants and such
    def initAnimation(self):
        self.initPhysConstants()

        self.gotoStartMode()

        self.initTimingConstants()

        self.initGameConstants()
        self.initGameVariables()

        self.root.bind("<B1-ButtonRelease>", 
                       lambda event: self.onMouseReleasedWrapper(event))

        self.root.bind("<B1-Motion>", lambda event: 
                       self.onMouseDragWrapper(event))
        
    #returns the level name of the level file at the given path
    def getLevelName(self, path):
        #key is the begining of the level file name
        key = self.levelPrefix
        keyIndex = path.find(key)

        levelIndex = keyIndex + len(key)

        fileExtensionLen = 4 #.txt

        return path[levelIndex:-fileExtensionLen]

    #initialize build mode
    def initBuildMode(self, path=None):
        if(path==None): path = self.levelPath
        self.initEnviron()
        self.levelName = self.getLevelName(path)
        self.prepareLevel(*self.getLevelInfo(path))
        #make sure bed beams selected
        self.beamButtons.select("Bed")
        self.buildType = BridgeBed

        #clear undo, redo ques
        self.undoQue = []
        self.redoQue = []

    def onMouseDragWrapper(self, event):
        self.onMouseDrag(event)
        self.redrawAll()

    def onMouseReleasedWrapper(self, event):
        self.onMouseReleased(event)
        self.redrawAll()

    #place the constraint in the tempconstraint variable
    #create new end node if need be
    def placeTempConstraint(self, event):
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

    #handles mouse relesed whenever it is a construction mode
    def constructMouseReleased(self, event):
        if(self.tempNode != None):
            #check if the beam is too long
            if(self.mode == "make" or 
               self.tempConstraint.getLength() < self.maxBeamLen):
                self.placeTempConstraint(event)
            else:
                self.tempNode.delete()
            #reset temp variables
            self.tempConstraint = None
            self.tempNode = None
            self.startNode = None
            self.redoQue = []

    #handles mouse releases in build mode
    def onBuildMouseReleased(self, event):
        self.constructMouseReleased(event)

    #handles mouse releases in make mode
    def onMakeMouseReleased(self, event):
        self.constructMouseReleased(event)

    #handles all mouse releases
    def onMouseReleased(self, event):
        if(self.mode == "build"):
            self.onBuildMouseReleased(event)
        elif(self.mode == "make"):
            self.onMakeMouseReleased(event)

    #handles mouse drags for modes where things are being constructed
    def constructMouseDrag(self, event):
        #only matters if there is a temp node that is being tracked
        if(self.tempNode != None):
            #update the position of the temp node to the cursor's position
            self.tempNode.position = self.environ.getVect(event.x, event.y)

            #change color to red if it is to long and the mode is build
            #aka it is a mode where length is limited
            if(self.tempConstraint.getLength() > self.maxBeamLen and 
               self.mode == "build"):
                self.tempConstraint.color = "red"
            else:
                self.tempConstraint.color = self.tempConstraint.baseColor

    #handles mouse drag events in build mode
    def onBuildMouseDrag(self, event):
        self.constructMouseDrag(event)

    #handles mouse drag events in make mode
    def onMakeMouseDrag(self, event):
        self.constructMouseDrag(event)

    #handles all mouse drag events
    def onMouseDrag(self, event):
        if(self.mode == "build"):
            self.onBuildMouseDrag(event)
        elif(self.mode == "make"):
            self.onMakeMouseDrag(event)

    #update the beam toggle buttons and take correct action based on 
    #the selected button
    def updateBeamButtons(self, event):
        #update the toggle buttons
        self.beamButtons.update(event.x, event.y)

        #set the build type to the selected button
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
        elif(buttonId == "Clear"):
            self.initBuildMode()

        return buttonId != None

    #makes a new constraint, taking into account if a node was selected and
    #which node was selected (selection)
    #also, where the click happened (pos(used for creating the object))
    def makeNewConstraint(self, selection, pos):
        #if it is a node that can be selected
        if(isinstance(selection, Node)):
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
            #if in make mode, create a whole new constraint, even if
            #no node was clicked to start at

            #create a new startNode, tempNode, and constraint
            self.startNode = Node(pos, self.nodeMass, self.environ,
                                  True, True)
            self.tempNode = Node(pos, self.nodeMass, self.environ,
                                 True, False)
            self.tempConstraint = self.buildType(self.startNode,
                                                 self.tempNode,
                                                 self.breakRatio,
                                                 self.environ)

    #construct a bridge or terrain
    def constructMousePressed(self, event):
        #what was clicked
        selection = self.environ.getClickedObj(event.x, event.y)
        pos = self.environ.getVect(event.x, event.y)
        if(self.buildType != Node):
            self.makeNewConstraint(selection, pos)
        elif(self.mode == "make"):
            #if a node was selected, change it to a fixed node
            if(isinstance(selection, Node)):
                self.undoQue.append((selection.color, selection))
                selection.color = self.fixedNodeColor
            else:
                #otherwise, create a new fixed node
                self.undoQue.append((Node(pos, self.nodeMass, self.environ, 
                                          True, True, self.fixedNodeColor),))

    #handles mouse pressed events in build mode
    def onBuildMousePressed(self, event):
        self.updateBeamButtons(event)

        #if none of the buttons clicked, then check if the bridge was being
        #built
        if(not self.checkBuildButtons(event)):
            self.constructMousePressed(event)

    #check buttons in test mode and take necesary actions if need be
    def checkTestButtons(self, event):
        buttonId = self.checkButtonList(self.testButtons, event)

        if(buttonId == "Build"):
            self.gotoBuildMode()

        return (buttonId != None)

    #get the list of levels by looking at the levels folder
    def initLevelList(self):
        path = self.levelFolder
        prefixLen = 6 #prefix to each file is level_
        postfixLen = 4 #len of file extension (.txt)

        self.levelList = []
        
        for fileName in os.listdir(path):
            filePath = path + os.sep + fileName
            #if it is a file and matches the file naming format
            if(not os.path.isdir(filePath) and 
               fileName[:prefixLen]==self.levelPrefix):
                #add it to the level list with the prefix and suffix removed
                self.levelList.append((filePath, 
                                       fileName[prefixLen:-postfixLen]))

    #change to pick mode
    def gotoPickMode(self):
        self.mode = "pick"
        self.initLevelList()
        #so buttons are most updated
        self.initPickButtons()

    #add a weight to the environment and increment score if needed
    def addWeight(self, event):
        pos = self.environ.getVect(event.x, event.y)

        Weight(pos, self.nodeMass*10, self.environ)

    #handles mouse pressed events for play mode
    def onPlayMousePressed(self, event):
        if(not self.checkTestButtons(event)):
            self.addWeight(event)

    #handles mouse pressed events in start mode
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

    #handles mouse pressed events in pick mode
    def onPickMousePressed(self, event):
        buttonId = self.checkButtonList(self.pickButtons, event)

        if(buttonId == "Menu"):
            self.gotoStartMode()
        elif(buttonId != None):
            self.levelPath = buttonId
            self.gotoBuildMode(buttonId)
        else:
            self.addWeight(event)

    #update toggle buttons used in level creation
    def updateTerrainButtons(self, event):
        #update toggle buttons
        self.terrainButtons.update(event.x, event.y)
        #adjust build type if need be
        if(self.terrainButtons.selectedId == "Land"):
            self.buildType = LandBeam
        elif(self.terrainButtons.selectedId == "Node"):
            self.buildType = Node

    #go through the current environment and get lists of terrain
    #and start nodes so they can be saved
    def getSavableNodeLists(self):
        terrainNodes = []
        startNodes = []
        #go through all objects and pick out nodes
        for obj in self.environ.objects:
            if(isinstance(obj, Node)):
                terrainNodes.append(obj.position.getXY())
                #if the node has been marked as a fixed node, save that
                if(obj.color == self.fixedNodeColor):
                    nodeIndex = len(terrainNodes) - 1
                    startNodes.append(nodeIndex)

        return (terrainNodes, startNodes)

    #get a list of the current constraints in the environmnet in a 
    #savable format
    def getSavableConstraintList(self, nodeList):
        constraints = []
        #go through constraints and find their nodes
        for index in self.environ.constraintIndexes:
            constraint = self.environ.objects[index]

            (node1, node2) = (constraint.nodes[0], constraint.nodes[1])

            node1Pos = node1.position.getXY() 
            node2Pos = node2.position.getXY()

            nodeIndexes = [-1, -1]
            #find node indexes in node list
            for i in xrange(len(nodeList)):
                if(nodeList[i] == node1Pos):
                    nodeIndexes[0] = i
                elif(nodeList[i] == node2Pos):
                    nodeIndexes[1] = i

            constraints.append(tuple(nodeIndexes))

        return constraints

    #save the terrain in the make mode to a file
    def saveTerrain(self):
        highScore = 0 #high score starts off at zero
        (terrainNodes, startNodes) = self.getSavableNodeLists()

        constraints = self.getSavableConstraintList(terrainNodes)

        fileContents = (str(terrainNodes) + "\n" + str(constraints) + "\n" + 
                        str(startNodes) + "\n" + str(highScore))

        fileName = self.levelPrefix + self.levelName + ".txt"
        path = self.levelFolder + os.sep + fileName
        writeFile(path, fileContents)
        assert(os.path.exists(path))

        #notify user that the file was saved
        message = "Your level has been saved!"
        title = "Level Saved"
        tkMessageBox.showinfo(title, message)

    #handles mouse pressed events in make mode
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

    #handles mouse pressed events in test mode
    def onTestMousePressed(self, event):
        if(not self.checkTestButtons(event) and not self.isGameOver):
            self.testWeight += self.testWeightIncrement
            self.score += self.testWeightIncrement

    #handles all mouse pressed events
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

    #switch to make mode (level creation)
    def gotoMakeMode(self):
        self.mode = "make"
        self.levelName = "untitled"
        self.isNaming = False
        self.terrainButtons.select("Land")
        self.buildType = LandBeam
        self.initEnviron()
        self.undoQue = []
        self.redoQue = []

    #switch to the start menu
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

    #switch to test mode
    def gotoTestMode(self):
        #only switch if the bridge spans the gap
        if(self.environ.doesBridgeCover(self.width)):
            self.mode = "test"
            self.score = 0
            self.testWeight = 0
            self.buildEnviron = copy.deepcopy(self.environ)
            self.bedNodes = self.getBedNodeList()
            self.environ.start()
        else:
            message = "Your bridge does not span the gap"
            title = "Invalid Bridge"
            tkMessageBox.showerror(title, message)

    #switch to play mode (ball dropping mode)
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

    #handles key press events in start mode
    def onStartKeyPress(self, event):
        if(event.keysym == "space" or event.keysym == "s"):
            self.gotoPickMode()
        elif(event.keysym == "d"):
            self.switchDebug()

    #handles key press events in test mode
    def onTestKeyPress(self, event):
        if(event.keysym == "b"):
            self.gotoBuildMode()
        elif(event.keysym == "p"):
            self.environ.pause()

    #undos a color change (color is what the obj origionally was) and returns
    #what should be added to the other que
    def undoColorChange(self, colorTuple):
        (oldColor, obj) = colorTuple
        newColor = obj.color
        obj.color = oldColor
        return (newColor, obj)

    #undoes a move when building a bridge or level
    def undoMove(self):
        if(len(self.undoQue) > 0):
            objToRemove = list(self.undoQue.pop())
            #check if both nodes of the constraint should be deleted
            if(self.mode == "make"):
                #check all objects in the tuple
                for obj in objToRemove:
                    if(isinstance(obj, Constraint)):
                        #check all nodes of the constraint to see if any have
                        #no other constraints left
                        for node in obj.nodes:
                            if(node not in objToRemove and 
                               len(node.constraints) == 1):
                                objToRemove.append(node)

            #check if it is a color change
            if(type(objToRemove[0]) == str):
                self.redoQue.append(self.undoColorChange(objToRemove))
            else:
                for obj in objToRemove:
                    obj.delete()

                self.redoQue.append(tuple(objToRemove))

    #redoes a move when building a bridge or level
    def redoMove(self):
        if(len(self.redoQue) > 0):
            objToAdd = self.redoQue.pop()

            #check if it is a color change
            if(type(objToAdd[0]) == str):
                self.undoQue.append(self.undoColorChange(objToAdd))
            else:
                for obj in objToAdd:
                    obj.environIndex = self.environ.add(obj)

                self.undoQue.append(objToAdd)

    #switch to debug mode
    def switchDebug(self):
        self.debug = not self.debug
        self.environ.debug = not self.environ.debug

    #handle key press events when in build mode
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

    #handle key press events when naming a level in make mode
    def onNamingKeyPress(self, event):
        if(event.keysym == "BackSpace" and len(self.levelName) > 0):
            self.levelName = self.levelName[:-1]
        elif(event.keysym == "space"):
            self.levelName += " "
        elif(event.keysym in string.printable):
            self.levelName += event.keysym

    #handles key presses during make mode
    def onMakeKeyPress(self, event):
        #check if the level is being named
        if(self.isNaming):
            self.onNamingKeyPress(event)
        else:
            if(event.keysym == "u"):
                self.undoMove()
            elif(event.keysym == "r"):
                self.redoMove()
            elif(event.keysym == "d"):
                self.switchDebug()

    #handle all key press events
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

        if(self.debug):
            oldTime = self.startTime
            self.startTime = time.time()
            if(self.startTime == oldTime):
                self.fps = -1
            else:
                self.fps = 1/(self.startTime - oldTime) 

        self.onTimerFired()
        self.redrawAll()

        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)

    #write the new high score to the level file
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
                nodeForce = -1*float(self.testWeight)/len(self.bedNodes)
                for node in self.bedNodes:
                    node.addForce(Vector(0, nodeForce))

            #if any BridgeBed broke
            isBroken = self.environ.update(self.dt, self.width, self.height)
            
            #if there was a BridgeBed that broke
            if(isBroken and self.mode == "test"): 
                self.isGameOver = True
                if(self.score > self.highScore):
                    self.gameOverText = "New High Score!"
                    self.updateHighScore(self.score)
                else:
                    self.gameOverText = "Game Over"

    #draw debug items
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
    #draw the score
    def drawScore(self):
        (x, y) = (self.width, 0)
        lineHeight = 30
        scoreText = "Score: %d %s" % (self.score, self.weightUnits)
        highScoreText = "HighScore: %d %s" % (self.highScore, self.weightUnits)

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

    #draw a list of tuples (text, weight) where 1 is the largest text and 
    #3 is the smallest
    def drawWeightedText(self, x, y, textList):
        for weightedLine in textList:
            (text, weight) = weightedLine
            if(weight == self.titleWeight): 
                font = "Arial 30 bold"
                lineHeight = 70
            elif(weight == self.subTitleWeight):
                font = "Arial 20 bold"
                lineHeight = 40
            elif(weight == self.normTextWeight):
                font = "Arial 15"
                lineHeight = 30

            self.canvas.create_text(x, y, text=text, font=font, anchor=N)
            y += lineHeight

    def getStartHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), ("Click on \"Play\" to select a level", norm),
                ("Click on \"Make\" to design your own level", norm),
                ("Press h or ? at any time to show or hide help", norm),
                ("Each screen has its own help screen", norm)]

        return text

    def getPickHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), ("Click on a level to play it", norm),
                ("Click on \"Menu\" to go back to the start menu", norm)]

        return text

    def getMakeHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), 
                ("Select if you want to place a fixed node or a piece of land" 
                 " with the \"Node\"/\"Land\" Buttons", norm), 
                ("Click to place a fixed node and click and drag to place a "
                 "land piece", norm), 
                ("Clicking the \"Name\" button toggles the ability to rename "
                 "the Level", norm), 
                ("Just delete the existing text when it is blue and type your "
                 "level's name", norm), 
                ("Click \"Save\" to save your level", norm), 
                ("Click \"Quit\" to go back to the start menu", norm), 
                ("Press \"u\" to undo a move", norm), 
                ("Press \"r\" to redo a move", norm)]

        return text

    def getBuildHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), ("Click \"Test\" to test your bridge", norm), 
                ("Click \"Play\" to drop balls on your bridge", norm), 
                ("Click \"Menu\" to go back to the start menu", norm), 
                ("Select \"Bed\" to build the bed of the bridge", norm), 
                ("The bed of the bridge will have weight added to it and balls"
                 " will collide with it", norm), 
                ("Select \"Beam\" to build non-collidable bridge beams", norm),
                ("Press \"u\" to undo a move", norm), 
                ("Press \"r\" to redo a move", norm)]

        return text

    def getTestHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), 
                ("Click \"Build\" to go back to build mode", norm), 
                ("Click to add weight to the bridge bed", norm)]

        return text

    def getPlayHelpText(self):
        (title, sub, norm) = (self.titleWeight, self.subTitleWeight, 
                              self.normTextWeight)
        text = [("Help", title), 
                ("Click \"Build\" to go back to build mode", norm), 
                ("Click to add a ball", norm)]

        return text

    def drawHelpScreen(self):
        if(self.mode == "start"):
            helpText = self.getStartHelpText()
        elif(self.mode == "make"):
            helpText = self.getMakeHelpText()            
        elif(self.mode == "pick"):
            helpText = self.getPickHelpText()
        elif(self.mode == "build"):
            helpText = self.getBuildHelpText()
        elif(self.mode == "test"):
            helpText = self.getTestHelpText()
        elif(self.mode == "play"):
            helpText = self.getPlayHelpText()

        self.drawWeightedText(self.width/2, 10, helpText)

    #draw a list of buttons
    def drawButtons(self, buttons):
        for button in buttons:
            button.draw(self.canvas)

    def drawPickScreen(self):
        self.canvas.create_text(0, 0, text="Pick a Level", anchor=NW, 
                           font="Arial 40 bold")

        self.drawButtons(self.pickButtons)

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

demo = PyBridge(1250, 750)
demo.run()