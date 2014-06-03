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
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Vec3,Vec4

from panda3d.core import AmbientLight

#tools
#from panda3d.core import loadPrcFileData
#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

import sys
from IPython import embed

import threading
#from queue import Queue #warning on py2...


#for points
#nodePath.setRenderModePerspective()
#nodePath.setRenderModeThickness()

#could use a queue for threadsafe object gen, not that we will really need it :/

import numpy as np


from dragsel import BoxSel


def genLabelText(text, i): #FIXME
  return OnscreenText(text = text, pos = (.025, -.05*i), fg=(1,1,1,1),
                      align = TextNode.ALeft, scale = .05)

#get the data from the database? or rather let people set their own custom prefs for whole classes of things on the fly and save it somewhere?

def getRelRenderProperties(relateable):
    """ Get or save the properties for all relatable types, initially they should all just be set to a default """
    #need to figure out exactly how we are going to do this...

def makeGrid(rng = 1000, spacing = 10): #FIXME make this scale based on zoom???
    ctup = (.3,.3,.3,1)
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
        color.addData4f(*ctup)
        color.addData4f(*ctup)

    for i,d in enumerate(ys):
        switch1 = (-1) ** i * rng
        switch2 = (-1) ** i * -rng
        verts.addData3f(switch1, d, 0)
        verts.addData3f(switch2, d, 0)
        color.addData4f(*ctup)
        color.addData4f(*ctup)

    gridLines = GeomLinestrips(Geom.UHStatic)
    gridLines.addConsecutiveVertices(0, vertexData.getNumRows())
    gridLines.closePrimitive()

    grid = Geom(vertexData)
    grid.addPrimitive(gridLines)
    return grid

def makeAxis(): #FIXME make this scale based on zoom???
    colors = (
        (1,0,0,1),
        (0,1,0,1),
        (0,0,1,1),

        (1,0,0,1),
        (0,1,0,1),
        (0,0,1,1),
    )
    points = (
        (0,0,0),
        (0,0,0),
        (0,0,0),
        (1,0,0),
        (0,1,0),
        (0,0,1),
    )

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    #fmt = GeomVertexFormat.getV3() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')


    for p,c in zip(points,colors):
        verts.addData3f(*p)
        color.addData4f(*c)

    axisX = GeomLinestrips(Geom.UHStatic)
    axisX.addVertices(0,3)
    axisX.closePrimitive()

    axisY = GeomLinestrips(Geom.UHStatic)
    axisY.addVertices(1,4)
    axisY.closePrimitive()

    axisZ = GeomLinestrips(Geom.UHStatic)
    axisZ.addVertices(2,5)
    axisZ.closePrimitive()

    axis = Geom(vertexData)
    axis.addPrimitive(axisX)
    axis.addPrimitive(axisY)
    axis.addPrimitive(axisZ)
    return axis


def convertToPoints(ndarray,project=False,nbins=1000):
    """
        take an np.ndarray and convert it to a point cloud
        this will probably be faster than trying to make them
        individual nodepaths, we might even be able to select
        the individual geoms?

        NO: this take an n lenght list of vectors length m where m is the dimensionality
        #we will need to bin the 4th dimension
    """
    #TODO dtypes should be annotated! or should they...
    #if you dtype an existing array, you probably will need to c=c[:,0] to fix wrapping
        #FIXME unfrotunately this breaks slicing >_<
    #dumps = Queue()
    output = {} #not fast, but whatever
    def makeGeom(array,n):
        fmt = GeomVertexFormat.getV3c4()
        vertexData = GeomVertexData('poitns', fmt, Geom.UHStatic)
        points = array
        ctup = np.random.rand(4)

        verts = GeomVertexWriter(vertexData, 'vertex')
        color = GeomVertexWriter(vertexData, 'color')

        for point in points:
            verts.addData3f(*point)
            color.addData4f(*ctup)

        points = GeomPoints(Geom.UHStatic)
        points.addConsecutiveVertices(0,len(array))
        points.closePrimitive()

        cloudGeom = Geom(vertexData)
        cloudGeom.addPrimitive(points)
        cloudNode = GeomNode('bin %s'%n)
        cloudNode.addGeom(cloudGeom)
        output[n] = cloudNode


    if ndarray.ndim > 2:
        raise TypeError('Format should be a list length n of vectors (4d max) ')
    if ndarray.shape[1] > 4:
        raise TypeError('we dont know what to do with 5d and above data yet')

    if ndarray.shape[1] == 4 or project:
        target = ndarray[ndarray[:,-1].argsort()][:,:-1]
        binWidth = ndarray.shape[0]//nbins
        zipped = zip(
            range(0,target.shape[0]-binWidth,binWidth), #FIXME this may leave final vals out check!
            range(binWidth,target.shape[0],binWidth))
        n = 0
        for start,stop in zipped:
            mkBinThread = threading.Thread(target=makeGeom, args=(target[start:stop],n))
            mkBinThread.start()
            n += 1

    #FIXME block until we are done

    while 1:
        try:
            return [output[i] for i in range(n)] #FIXME alternately use
        except:
            pass



    

    #elif len(shape) == 4 or project:
        #for i in range(ndarray.shape[0]): #last componenet will always be the 'projected' dimension
            #mkThrd = threading.Thread(target=makeGeom, args=(ndarray[:,Ellipsis,i],dumps))

    #shape = ndarray.shape #[0,0,0,:] : is interpreted as time
    


def makePoints(n=1000):
    """ make a cloud of points that are a single node VS branching and making subnodes to control display """

    #points = np.random.uniform(-10,10,(n,4))
    #points = np.random.randn(n,3)
    points = np.cumsum(np.random.randint(-1,2,(n,3)), axis=0) #classic random walk
    #colors = np.random.rand(n,4)
    clr4 = np.random.rand(1,4)

    #points = [(0,0,0)]

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    #for point,clr4 in zip(points,colors):
    for point in points:
        verts.addData3f(*point)
        #color.addData4f(*point)
        color.addData4f(*clr4[0])
        #color.addData4f(.1,.1,.1,1)

    #pointCloud = GeomLinestrips(Geom.UHStatic) #this is fucking cool!
    #pointCloud = GeomTristrips(Geom.UHStatic) #this is fucking cool!
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

class HasSelectables: #mixin see chessboard example
    def __init__(self):
        #selection detection
        self.picker = CollisionRraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addCollider(self.pickerNP, self.pq)

        #box selection detection HINT: start with drawing the 2d thing yo!

        self.__shift__ = False
        self.accept("shift", self.shiftOn)
        self.accept("shift-up", self.shiftOff)

        #mouse handling
        self.accept("mouse1", self.clickHandler)
        self.accept("mouse1-up", self.releaseHandler)

        #dragging
        self.dragTask = taskMgr.add(self.dragTask, 'dragTask')

    def clickHandler(self):
        pass

    def releaseHandler(self):
        pass

    def dragTask(self, task):
        pass


    def clickSelectObject(self): #shif to multiselect... ?? to unselect invidiual??
        pass

    def dragSelectObjects(self): #always drag in the plane of the camera
        pass

class Grid3d(DirectObject):
    def __init__(self):
        gridNode = GeomNode('grid')
        gridGeom = makeGrid()
        gridNode.addGeom(gridGeom)
        grid = render.attachNewNode(gridNode)

class Axis3d(DirectObject): #FIXME not the best way to do this, making all these new direct objects if they need to be controlled
    def __init__(self, scale=10):
        axisNode = GeomNode('axis')
        axisGeom = makeAxis()
        axisNode.addGeom(axisGeom)
        axis = render.attachNewNode(axisNode)
        axis.setScale(scale,scale,scale)
        axis.setRenderModeThickness(2)

class PointsTest(DirectObject):
    def __init__(self,num=99999,its=99):
        self.num = num
        self.its = its
        #self.escapeText = genLabelText("ESC: Quit", 0)
        self.accept("escape", sys.exit)

        #pointcloud
        #self.clouds=[]
        for i in range(its):
            cloudGeom=makePoints(self.num) #save us the pain in this version make it the same one probably a more efficient way to do this
            self.cloudNode = GeomNode('points')
            self.cloudNode.addGeom(cloudGeom) #ooops dont forget this!
            self.cloud = render.attachNewNode(self.cloudNode)
            self.cloud.setPos(10,10,10)
        #for i in range(its):
            #self.clouds.append(cloudNode)
        self.its = its

        self.counter = 0
        self.count = genLabelText('%s'%self.counter,3)
        self.count.reparentTo(base.a2dTopLeft)

        #self.poses = np.random.randint(-1000,1000,(its,3))
        #self.cloud = None
        #self.cloud = render.attachNewNode(cloudNode)
        #cloud.hprInterval(1.5,Point3(360,360,360)).loop()
        #inst=render.attachNewNode('clound-%s'%self.counter)

        #for i in range(its):
            #inst=render.attachNewNode('clound-%s'%self.counter)
            #inst.setPos(*self.poses[self.counter])
            #self.cloud.instanceTo(inst)
            #self.counter += 1

        nodes = convertToPoints(np.random.randint(-1000,1000,(1000,4)))

        for node in nodes:
            render.attachNewNode(node)#.reparentTo(render)


        
        #self.update()

        #self.timer = globalClock.getRealTime()
        #taskMgr.add(self.spawnTask,'MOAR')

    def spawnTask(self, task):
        #every frame move a point and change its color
        #self.cloudGeom
        #dt = .05
        #now = globalClock.getRealTime()
        #if now - self.timer > dt:
            #self.timer = now
            #for i in range(np.random.randint(1,10)):
                #self.update()
        #return Task.cont
        self.update()
        return task.cont

    def update(self):
        #if self.cloud:
            #self.cloud.detachNode()
        #self.cloud = render.attachNewNode(self.clouds[np.random.randint(0,self.its)])
        if self.counter < self.its-100:
            for i in range(1000):

                inst=render.attachNewNode('clound-%s'%self.counter)
                inst.setPos(*self.poses[self.counter])
                self.cloud.instanceTo(inst)
                self.counter += 1
            self.count.setText('%s'%self.counter)
        else:
            taskMgr.remove('MOAR')
            
def main():
    from util import Utils
    from camera import CameraControl
    #from panda3d.core import ConfigVariableBool
    #ConfigVariableString('view-frustum-cull',False)
    from panda3d.core import loadPrcFileData
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = Utils()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    bs = BoxSel()
    #pt = PointsTest(999,99999)
    #pt = PointsTest(1,9999999)
    #pt = PointsTest(1,999999) #SLOW AS BALLS: IDEA: render faraway nodes as static meshes and transform them to live as we get closer!
    #pt = PointsTest(9999999,1)
    #pt = PointsTest(99999,10) #runs fine when there is only 1 node >_<
    pt = PointsTest(999,10) #runs fine when there is only 1 node >_<
    #pt = PointsTest(1,99999) #still slow :/
    #pt = PointsTest(1,9999) #still slow :/ #deep trees segfault!
    #pt = PointsTest(1,4000) #still slow :/ #this one is ok
    #pt = PointsTest(1,999) #still slow
    #pt = PointsTest(1,499) #still slow 15 fps with 0,0,0 positioned geom points
    #pt = PointsTest(1,249) #about 45fps :/
    base.disableMouse()
    #base.camLens.setFar(9E12) #view-frustum-cull 0
    run()

if __name__ == '__main__':
    main()
