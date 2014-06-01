#import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
#from panda3d.core import PandaNode,NodePath
from panda3d.core import TextNode, PandaNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Vec3,Vec4

from panda3d.core import AmbientLight


import sys
from threading import Thread
from IPython import embed


def makeSelectRect():
    ctup = (1,1,1,1)
    fmt = GeomVertexFormat.getV3c4()
    vertexData = GeomVertexData('points', fmt, Geom.UHDynamic)

    points = ( #makes nice for Tristrips
        (0,0,0),
        (0,1,0),
        (1,0,0),
        (1,1,0),
    )

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for point in points:
        verts.addData3f(*point)
        color.addData4f(*ctup)

    boxLines = GeomLinestrips(Geom.UHDynamic)
    boxLines.addConsecutiveVertices(0,3)
    boxLines.closePrimitive()

    boxTris = GeomTristrips(Geom.UHDynamic)
    boxTris.addConsecutiveVertices(0,3)
    boxTris.closePrimitive()

    box = Geom(vertexData)
    box.addPrimitive(boxLines)
    #box.addPrimitive(boxTris)

    return box
    
#use render 2d?

class BoxSel(DirectObject):
    def __init__(self):

        self.__mouseDown__ = False

        #setup the selection box
        #self.__startNode__ = render2d.attachNewNode(PandaNode()) #empty node
        boxNode = GeomNode('selectBox')
        boxNode.addGeom(makeSelectRect())
        self.__baseBox__ = render2d.attachNewNode(boxNode)
        self.__baseBox__.hide()

        self.accept('mouse1',self.gotClick)
        self.accept('mouse1-up',self.gotRelease)
        self.accept("escape", sys.exit)

        #taskMgr.add(self.clickTask, 'clickTask')
        
    def gotClick(self):
        if not self.__mouseDown__:
            self.__mouseDown__ = True
            target = self.getClickTarget()  #this isnt an RTS so we want click/drag
            if not target:
                x,y = base.mouseWatcherNode.getMouse()
                self.__baseBox__.setPos(x,y,0)
                self.__baseBox__.setScale(0) #setSx setSy
                self.__baseBox__.show()
                taskMgr.add(self.boxTask, 'boxTask')

    def getClickTarget(self):
        """ See if we were clicking ON an object """
        #this will use the ray tracing hit detection
        #so no need for x and y
        return False

    def gotRelease(self):
        self.__mouseDown__ = False
        self.__baseBox__.hide()
        taskMgr.remove('boxTask')


    #def clickTask(self, task): #this will probably need to handle many possible click targets
        #if type(self.__mouseDown__) is tuple:
            #self.__mouseStart__ = self.__mouseDown__
        #elif self.__mouseDown__:
            #pass #dragging?
        #return task.cont

    def boxTask(self, task): #this will only be active if mouse down and not click
        x,y = base.mouseWatcherNode.getMouse()
        cx,cy,cz = self.__baseBox__.getPos()
        self.__baseBox__.setSx(x-cx)
        self.__baseBox__.setSy(y-cy)
        self.__baseBox__.setSz(y-cz)
        return task.cont


def main():
    base = ShowBase()
    dt = BoxSel()
    run()

if __name__ == '__main__':
    main()
