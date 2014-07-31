import sys
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, Point3
from IPython import embed

def genLabelText(text, i): #FIXME
  #return OnscreenText(text = text, pos = (-1.3, .95-.05*i), fg=(1,1,1,1),
  return OnscreenText(text = text, pos = (.025, -.05*i), fg=(1,1,1,1),
                      align = TextNode.ALeft, scale = .05)

class console(DirectObject):
    def __init__(self):
        self.accept('i',self.ipython)
    def ipython(self):
        embed()  # this works becasue you can access all the things via render :)

class exit_cleanup(DirectObject):
    """ in order to get everything to exit 'cleanly'
        we need to close the asyncio loop before we
        call sys.exit() to terminate run() otherwise
        the code following run() in the main thread
        will never execute
    """
    def __init__(self, event_loop=None):
        self.event_loop = event_loop
        self.accept("escape",self.exit)

    def exit(self):
        #we must call stop before sys.exit() or we can't stop the loop
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        sys.exit()

class ui_text(DirectObject):
    def __init__(self):
        self.pos = genLabelText('hello',1)
        self.pos.reparentTo(base.a2dTopLeft)
        self.win = genLabelText('hello',2)
        self.win.reparentTo(base.a2dTopLeft)

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
            ap2 = aspect2d.getRelativePoint(render2d, Point3(x, y, 0))
            self.pos.setText('%1.3f, %1.3f'%(ap2.x,ap2.y))
        return task.cont

def main():
    from direct.showbase.ShowBase import ShowBase
    base = ShowBase()
    asdf = ui_text()
    run()

if __name__ == '__main__':
    main()
