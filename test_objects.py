#import direct.directbase.DirectStart #FIXME showbase
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
#from panda3d.core import PandaNode,NodePath
from panda3d.core import TextNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
#from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Vec3,Vec4

from panda3d.core import AmbientLight


import sys
from threading import Thread
from IPython import embed


#for points
#nodePath.setRenderModePerspective()
#nodePath.setRenderModeThickness()

#could use a queue for threadsafe object gen, not that we will really need it :/

import numpy as np



def genLabelText(text, i): #FIXME
  return OnscreenText(text = text, pos = (-1.3, .95-.05*i), fg=(1,1,1,1),
                      align = TextNode.ALeft, scale = .05)

#get the data from the database? or rather let people set their own custom prefs for whole classes of things on the fly and save it somewhere?


def getRelRenderProperties(relateable):
    """ Get or save the properties for all relatable types, initially they should all just be set to a default """
    #need to figure out exactly how we are going to do this...

def makeObject(relateable):
    pass


def makeGrid(rng = 1000, spacing = 10): #FIXME make this scale based on zoom???
    xs = np.arange(-rng,rng+1,spacing)
    ys = xs

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    #fmt = GeomVertexFormat.getV3() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for i,d in enumerate(xs):
        switch1 = (-1) ** i * rng
        switch2 = (-1) ** i * -rng
        #print(d,switch1,0)
        verts.addData3f(d, switch1, 0)
        verts.addData3f(d, switch2, 0)
        color.addData4f(1,1,1,.2)
        color.addData4f(1,1,1,.2)

    for i,d in enumerate(ys):
        switch1 = (-1) ** i * rng
        switch2 = (-1) ** i * -rng
        verts.addData3f(switch1, d, 0)
        verts.addData3f(switch2, d, 0)
        color.addData4f(1,1,1,.2)
        color.addData4f(1,1,1,.2)

    gridLines = GeomLinestrips(Geom.UHStatic)
    gridLines.addConsecutiveVertices(0, vertexData.getNumRows())
    gridLines.closePrimitive()

    grid = Geom(vertexData)
    grid.addPrimitive(gridLines)
    return grid

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
    pointCloud = GeomPoints(Geom.UHStatic)
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

class PointsTest(DirectObject):
    def __init__(self,num=99999,its=99):
        self.num = num
        self.its = its
        self.escapeText = genLabelText("ESC: Quit", 0)
        self.accept("escape", sys.exit)

        #grid
        gridNode = GeomNode('grid')
        gridGeom = makeGrid()
        gridNode.addGeom(gridGeom)
        grid = render.attachNewNode(gridNode)



        #self.cloudGeom=makePoints(9999999)
        self.clouds=[]
        for i in range(its):
            cloudNode = GeomNode('points')
            cloudGeom=makePoints(self.num)
            cloudNode.addGeom(cloudGeom) #ooops dont forget this!
            self.clouds.append(cloudNode)

        self.cloud = None
        self.update()
        #self.cloud = render.attachNewNode(cloudNode)
        #cloud.hprInterval(1.5,Point3(360,360,360)).loop()

        self.timer = globalClock.getRealTime()
        #taskMgr.add(self.spawnTask,'newInput')

    def spawnTask(self, task):
        #every frame move a point and change its color
        #self.cloudGeom
        dt = .01
        now = globalClock.getRealTime()
        if now - self.timer > dt:
            self.timer = now
            self.update()
        return Task.cont

    def update(self):
        if self.cloud:
            self.cloud.detachNode()
        self.cloud = render.attachNewNode(self.clouds[np.random.randint(0,self.its)])
        pass

base = ShowBase()
base.setBackgroundColor(0,0,0)
pt = PointsTest(99999,1)
run()

