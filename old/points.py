import direct.directbase.DirectStart
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
#from panda3d.core import PandaNode,NodePath
from panda3d.core import TextNode
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


#for points
#nodePath.setRenderModePerspective()
#nodePath.setRenderModeThickness()

import numpy as np

def genLabelText(text, i): #FIXME
  return OnscreenText(text = text, pos = (-1.3, .95-.05*i), fg=(1,1,0,1),
                      align = TextNode.ALeft, scale = .05)

def makePoints(n=1000):
    """ make a cloud of points that are a single node VS branching and making subnodes to control display """

    #points = np.random.uniform(-10,10,(n,4))
    points = np.random.randn(n,3)
    colors = np.random.rand(n,4)

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for point,clr4 in zip(points,colors):
    #for point in points:
        verts.addData3f(*point)
        #color.addData4f(*point)
        color.addData4f(*clr4)
        #color.addData4f(.1,.1,.1,1)

    #pointCloud = GeomLinestrips(Geom.UHStatic) #this is fucking cool!
    pointCloud = GeomTristrips(Geom.UHStatic) #this is fucking cool!
    #pointCloud = GeomPoints(Geom.UHStatic)
    #pointCloud.addVerticies(*range(n))
    pointCloud.addConsecutiveVertices(0,n) #warning may error since n-1?
    pointCloud.closePrimitive()

    cloud = Geom(vertexData)
    cloud.addPrimitive(pointCloud)
    return cloud

#cloud.setRenderModeThickness(10)
#cloud.setRenderModePerspective(1)

#light = AmbientLight('sceneLight')
#light.setColor(Vec4(1,1,1,1))
#sceneLight = render.attachNewNode(light)
#render.setLight(sceneLight)

def makeTriStrip(): #don't need, will use GeomPoint
    pass

def make_object():
    pass

def addObject(obj:Geom):
    pass

class PointsTest(DirectObject):
    def __init__(self):
        self.escapeText = genLabelText("ESC: Quit", 0)
        self.accept("escape", sys.exit)

        cloudNode = GeomNode('points')
        #self.cloudGeom=makePoints(999999)
        self.cloudGeom=makePoints(9999)
        cloudNode.addGeom(self.cloudGeom) #ooops dont forget this!

        cloud = render.attachNewNode(cloudNode)
        cloud.hprInterval(20,Point3(360,0,0)).loop() #scale this with zoom

        taskMgr.add(self.spawnTask,'newInput')

    def spawnTask(self, task):
        #every frame move a point and change its color
        self.cloudGeom
        return Task.cont

    def update(self):
        pass

base.setBackgroundColor(0,0,0)
pt = PointsTest()
base.run()

