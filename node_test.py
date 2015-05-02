from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import GeomNode, Geom, GeomPoints
from panda3d.core import OmniBoundingVolume

from time import time

import numpy as np
from IPython import embed

import sys

from .ui import makeAxis

def makePoint():
    point = (0,0,0)
    clr4 = np.random.rand(4)
    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)
    verts = GeomVertexWriter(vertexData, 'vertex')
    verts.addData3f(*point)
    color = GeomVertexWriter(vertexData, 'color')
    color.addData4f(*clr4)
    pointCloud = GeomPoints(Geom.UHStatic)
    pointCloud.addVertex(0)
    pointCloud.closePrimitive()
    cloud = Geom(vertexData)
    cloud.addPrimitive(pointCloud)
    cloudNode = GeomNode('point')
    cloudNode.addGeom(cloud)
    return cloudNode

class geomTest(DirectObject):
    def __init__(self,n):
        self.accept('escape',sys.exit)
        poses = np.random.randint(-100,100,(n,3))
        geomParent = render.attachNewNode('geomParent')
        geoms = GeomNode('container')
        for _ in range(n):
            ax = makeAxis()
            #ax.setPos(np.random.randint(-100,100))  #FIXME
            geoms.addGeom(ax)

        geomParent.attachNewNode(geoms)


class emptyTest(DirectObject):
    def __init__(self,n):
        self.accept('escape',sys.exit)
        poses = np.random.randint(-100,100,(n,3))
        geomParent = render.attachNewNode('geomParent')
        basePoint = geomParent.attachNewNode(makePoint())
        for i in range(n):
            point = geomParent.attachNewNode('%s'%i)
            point.setPos(*poses[i])
            basePoint.instanceTo(point)
            #point.node().setBounds(OmniBoundingVolume()) #XXX turns out culling of geom nodes takes a MASSIVE amount of time
            #point.node().setFinal(True)

        #basePoint.node().setBounds(OmniBoundingVolume()) #XXX turns out culling of geom nodes takes a MASSIVE amount of time
        #basePoint.node().setFinal(True)
        #geomParent.node().setBounds(OmniBoundingVolume())
        #geomParent.node().setFinal(True)

        #tick = time()
        #geomParent.flattenStrong() #FIXME extremely slow, almost certainly will be faster to rebuild the geoms from scratch
        #tock = time()
        #metric = (tock-tick) / n
        #print(tock-tick)
        #print('run time / bins = %s'%metric)

def main():
    from panda3d.core import PStatClient
    from panda3d.core import loadPrcFileData
    from .ui import CameraControl, Axis3d, Grid3d
    #loadPrcFileData('','threading-model Cull/Draw') #XXX wow, not good for this use case...
    base = ShowBase()
    base.disableMouse()
    base.setBackgroundColor(0,0,0)

    cc = CameraControl()
    ax = Axis3d()
    gd = Grid3d()

    #nt = emptyTest(2000)
    gt = geomTest(2000)
    PStatClient.connect()
    run()

if __name__ == '__main__':
    main()
