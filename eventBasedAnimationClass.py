from Tkinter import *

class EventBasedAnimationClass(object):
    def onMousePressed(self, event): pass
    def onKeyPressed(self, event): pass
    def onTimerFired(self): pass
    def initAnimation(self): pass
    def redrawAll(self): pass

    def __init__(self, width=300, height=300):
        self.width = width
        self.height = height

        self.timerDelay = 250 #onMousePressed

    def onMousePressedWrapper(self, event):
        self.onMousePressed(event)
        self.redrawAll()

    def onKeyPressedWrapper(self, event):
        self.onKeyPressed(event)
        self.redrawAll()

    def onTimerFiredWrapper(self):
        if(self.timerDelay == None):
            return
        self.onTimerFired()
        self.redrawAll()
        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)

    def run(self):
        self.root = Tk()
        self.canvas = Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack()

        self.initAnimation()

        def mouse(event):
            self.onMousePressedWrapper(event)

        self.root.bind("<Button-1>", mouse)
        self.root.bind("<Key>", lambda event: self.onKeyPressedWrapper(event))

        self.onTimerFiredWrapper()

        self.root.mainloop()
