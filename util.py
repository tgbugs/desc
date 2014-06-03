from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

def genLabelText(text, i): #FIXME
  return OnscreenText(text = text, pos = (-1.3, .95-.05*i), fg=(1,1,1,1),
                      align = TextNode.ALeft, scale = .05)


class Utils(DirectObject):
    def __init__(self):
        self.pos = genLabelText('hello',2)
        self.win = genLabelText('hello',3)
        taskMgr.add(self.posTask, 'posTask')
        taskMgr.add(self.winTask, 'winTask')
    def winTask(self, task):
        x = base.win.getXSize()
        y = base.win.getYSize()
        self.win.setText('%s %s'%(x,y))
        return task.cont
    def posTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            x,y = base.mouseWatcherNode.getMouse()
            self.pos.setText('%1.3f, %1.3f'%(x,y))
        return task.cont
