from __future__ import print_function
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
from panda3d.core import Point3,Vec3,Vec4,BitMask32

from panda3d.core import CollisionNode, CollisionSphere
#tools
#from panda3d.core import loadPrcFileData
#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

import sys
from IPython import embed

from monoDict import MonoDict as md

import multiprocessing as mp
from multiprocessing import Pipe
#from multiprocessing.managers import SyncManager
#from queue import Queue #warning on py2...
#import threading #not what we need due to GIL >_<

#for points
#nodePath.setRenderModePerspective()
#nodePath.setRenderModeThickness()

#could use a queue for threadsafe object gen, not that we will really need it :/

import numpy as np

from dragsel import BoxSel

NCORES = 8 #TODO get this live?

def genLabelText(text, i): #FIXME
  return OnscreenText(text = text, pos = (.025, -.05*i), fg=(1,1,1,1),
                      align = TextNode.ALeft, scale = .05)

#get the data from the database? or rather let people set their own custom prefs for whole classes of things on the fly and save it somewhere?

def getRelRenderProperties(relateable):
    """ Get or save the properties for all relatable types, ,col,vertsinitially they should all just be set to a default """
    #need to figure out exactly how we are going to do this...

def makeBins(ndarray,nbins=1000):
    if ndarray.shape[1] == 4 or nbins > 1:
        target = ndarray[ndarray[:,-1].argsort()][:,:-1]

    binWidth = target.shape[0]//nbins
    zipped = zip(range(0,chunk.shape[0]-binWidth,binWidth), #FIXME this may leave final vals out check!
                 range(binWidth,chunk.shape[0],binWidth))

    if ndarray.shape[1] > 4:
        raise TypeError('we dont know what to do with 5d and above data yet')

def makeGeom(index_counter, array,ctup,i,pipe, geomType=GeomPoints):
    """ multiprocessing capable geometery maker """
    #man = indexMan(('127.0.0.1',5000), authkey='none')
    #man.connect()
    #index = man.index()
    index = {}

    fmt = GeomVertexFormat.getV3c4()

    vertexData = GeomVertexData('points', fmt, Geom.UHDynamic) #FIXME use the index for these too? with setPythonTag, will have to 'reserve' some
    #vertexData.setPythonTag('uid',index.reserve()) #maybe we don't need this? the geom should have it all?
    cloudGeom = Geom(vertexData)
    #cloudGeom.setPythonTag('uid',index.reserve())
    cloudNode = GeomNode('bin %s selectable'%(i))
    uid = next(index_counter)
    index[uid] = None
    cloudNode.setPythonTag('uid',uid) #FIXME we return cloudnode elsewhere... maybe on the other end we can set the uid in the index properly?

    points = array

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for point in points:
        index[next(index_counter)]=[point,cloudNode.getPythonTag('uid'),None] #FIXME we're gonna need a decode on the other end?
        verts.addData3f(*point)
        color.addData4f(*ctup)

    points = geomType(Geom.UHDynamic)
    points.addConsecutiveVertices(0,len(array))
    points.closePrimitive()

    cloudGeom.addPrimitive(points)
    cloudNode.addGeom(cloudGeom) #TODO figure out if it is faster to add and subtract Geoms from geom nodes...
    #output[i] = cloudNode
    #print('ping',{i:cloudNode})
    #pipe.send((i,))
    #out = q.get()
    #print('pong',out)
    #q.put(out)
    if pipe == None:
        return cloudNode, index
    pipe.send(cloudNode.encodeToBamStream()) #FIXME make this return a pointer NOPE
    pipe.send(index) #FIXME make this return a pointer NOPE
    #return cloudNode

def _makeGeom(array,ctup,i,pipe, geomType=GeomPoints): #XXX testing multiple Geom version ... for perf seems like it will be super slow
    #SUUUPER slow TONS of draw calls
    #wwwayyy better to make a bunch of geoms ahead of time...
    """ multiprocessing capable geometery maker """
    fmt = GeomVertexFormat.getV3c4()

    cloudNode = GeomNode('bin %s selectable'%(i))
    for point in array:
        vertexData = GeomVertexData('poitn', fmt, Geom.UHStatic)
        GeomVertexWriter(vertexData, 'vertex').addData3f(*point)
        GeomVertexWriter(vertexData, 'color').addData4f(*ctup)
        #verts.addData3f(*point)
        #color.addData4f(*ctup)

        points = geomType(Geom.UHStatic)
        points.addVertex(0)
        points.closePrimitive()

        cloudGeom = Geom(vertexData)
        cloudGeom.addPrimitive(points)
        cloudNode.addGeom(cloudGeom) #TODO figure out if it is faster to add and subtract Geoms from geom nodes...
    #output[i] = cloudNode
    #print('ping',{i:cloudNode})
    #pipe.send((i,))
    #out = q.get()
    #print('pong',out)
    #q.put(out)
    if pipe == None:
        return (cloudNode)
    pipe.send(cloudNode.encodeToBamStream()) #FIXME make this return a pointer NOPE
    #return cloudNode

def convertToGeom(index_counter,target,geomType=GeomPoints): #FIXME works under python2 now...
    """
        take an np.ndarray and convert it to a point cloud
        this will probably be faster than trying to make them
        individual nodepaths, we might even be able to select
        the individual geoms?

        NO: this take an n lenght list of vectors length m where m is the dimensionality
        #we will need to bin the 4th dimension
    """
    #TODO check that target has enough points for the geomType requested!

    if target.ndim > 2:
        raise TypeError('Format should be a list length n of vectors (4d max) ')

    ncores = NCORES #prevent changes to the global variable from affecting a single run
    multiple = 10 #irritatingly broken for multiprocessing using the global index :(
    ctup = np.random.rand(4)
    if target.shape[0] < ncores*multiple: #need at LEAST 10 points per core TODO test for optimal chunking start size
        ncores = 1
        out, index = makeGeom(index_counter, target,ctup,0,None,geomType)
        return lambda:out, index
    else:
        chunks = []
        chunk_size = target.shape[0]//ncores
        czip = zip(range(0,target.shape[0]-chunk_size,chunk_size),
                   range(chunk_size,target.shape[0],chunk_size))
        for start,stop in czip:
            chunks.append(target[start:stop]) #may not need to do this if I can generate it from i?

        processes = []
        pipes = [Pipe() for q in range(ncores)]
        #q = Queue()
        for i in range(ncores):
            #output[i]=makeGeom(chunks[i],ctup,i,None)
            #a = threading.Thread(target=makeGeom, args=(chunks[i],ctup,i))#,cb))

            p = mp.Process(target=makeGeom, args=(index_counter, chunks[i],ctup,i,pipes[i][1],geomType)) #XXX this one
            p.start()
            processes.append(p)
        def runner():
            #print('running')
            output = {} #we can probably just merge the dicts after the fact?
            idx = []
            for i in range(ncores):
                bit = pipes[i][0].recv()
                output[i]=GeomNode.decodeFromBamStream(bit) #it will match since pipes are named, also recv blocks till close
                idx.append( pipes[i][0].recv() )
            out = []
            for i in range(ncores):
                out.append(output[i]) #FIXME risk of missing indicies due to integer //
            #print('done running')
            return zip(out, idx) #FIXME stuipd
        return runner

    #print(pipes[0][0].recv())
    #[output.update(pipes[i][0].recv()) for i in range(ncores)]
    #print(output)
    #[p.join() for p in processes] #FIXME this probably should go elsewhere? like in a class that handles these things?

    #out = q.get()
    #print(out)
    #[output.update(q.get()) for i in range(ncores)]
        #n = 0
        #for start,stop in zipped:
            #mkBinThread = threading.Thread(target=makeGeom, args=(target[start:stop],n)) #TODO fix this so that threads = number of corse instead of spawning bazillions of threads
            #mkBinThread.start()
            #n += 1
        #mkBinThread.join() #FIXME this can fail

    #FIXME block until we are done

    #print(output)

    #elif len(shape) == 4 or project:
        #for i in range(ndarray.shape[0]): #last componenet will always be the 'projected' dimension
            #mkThrd = threading.Thread(target=makeGeom, args=(ndarray[:,Ellipsis,i],dumps))
    #shape = ndarray.shape #[0,0,0,:] : is interpreted as time
    
def convertToColl(target,collType=CollisionSphere): #FIXME this won't work quite right
    ncores = NCORES
    if target.shape[0] < ncores*10:
        ncores = 1
        out = makeColl()

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

class PointsTest(DirectObject):
    def __init__(self,num=99999,its=99):
        self.num = num
        self.its = its
        self.accept("escape", sys.exit)

        #pointcloud
        #self.clouds=[]
        for i in range(its):
            cloudGeom=makePoints(self.num) #save us the pain in this version make it the same one probably a more efficient way to do this
            self.cloudNode = GeomNode('points')
            self.cloudNode.addGeom(cloudGeom) #ooops dont forget this!
            self.cloud = render.attachNewNode(self.cloudNode)
            #self.cloud.setPos(10,10,10)
        #for i in range(its):
            #self.clouds.append(cloudNode)


        #self.poses = np.random.randint(-1000,1000,(its,3))
        #self.cloud = None
        #self.cloud = render.attachNewNode(self.cloudNode)
        #cloud.hprInterval(1.5,Point3(360,360,360)).loop()

        #self.counter = 0
        #self.count = genLabelText('%s'%self.counter,3)
        #self.count.reparentTo(base.a2dTopLeft)

        """
        inst=render.attachNewNode('clound-%s'%self.counter)
        for i in range(its):
            inst=render.attachNewNode('clound-%s'%self.counter)
            inst.setPos(*self.poses[self.counter])
            self.cloud.instanceTo(inst)
            self.counter += 1
        """

        
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
            
class NodeTest(DirectObject):
    def __init__(self,n=9999,bins=99):
        types = [GeomLinestrips]#, GeomTristrips], GeomTrifans] #FIXME allow makeGeom to accept a LIST of geom types!
        bases = [np.cumsum(np.random.randint(-1,2,(n,3)),axis=0) for i in range(bins)]
        runs = []
        for base in bases: #FIXME for some reason this is running slower for extra bins number of bins, should not be
            for type_ in types:
                runs.append(convertToGeom(base,type_)) #this call seems to take longer with additional bins?

        for nodes in runs:
            for node in nodes():
                nd = render.attachNewNode(node)

def smipleMake(index_counter,target,geomType=GeomPoints): #FIXME works under python2 now...
    ctup = np.random.rand(4)
    out, index = makeGeom(index_counter,target,ctup,0,None,geomType)
    return lambda:(out, index) #this is stupid
         
from monoDict import Counter
index_counter = Counter(0,1)
class CollTest(DirectObject):
    def __init__(self,n=9999,bins=9,show=False):
        collideRoot = render.attachNewNode('collideRoot')
        bases = [np.cumsum(np.random.randint(-1,2,(n,3)),axis=0) for i in range(bins)]
        type_ = GeomPoints
        runs = []
        for base in bases:
            runs.append(smipleMake(index_counter,base,type_))
        r = 0
        for nodes in runs:
            #pos = np.random.randint(-100,100,3)
            print(nodes)
            node,_ = nodes()
            nd = render.attachNewNode(node)
            #nd.setPos(*pos)
            #nd.setRenderModeThickness(5)
            #XXX TODO XXX collision objects
            n = 0 
            for position in bases[r]: #FIXME this is hella slow, the correct way to do this is to detach and reattach CollisionNodes as they are needed...
                #TODO to change the color of a selected node we will need something a bit more ... sophisticated
                cNode = collideRoot.attachNewNode(CollisionNode('collider obj,vert %s,%s'%(r,n))) #ultimately used to index??
                cNode.node().addSolid(CollisionSphere(0,0,0,.5))
                cNode.node().setIntoCollideMask(BitMask32.bit(1))
                cNode.setPos(nd,*position)
                if show:
                    cNode.show()
                n+=1
            r+=1

#
#class indexMan(SyncManager):
    #pass
class FullTest(DirectObject):
    def __init__(self,n=1,bins=1):

        #index = md()
        #def get_index():
            #return index
        #indexMan.register('index',get_index)
        #self.iman = indexMan(('127.0.0.1',5000),authkey='none')
        #self.iman.start()
        index = {}
        #index_counter = Counter(0,1)


        collideRoot = render.attachNewNode('collideRoot')
        bases = [np.cumsum(np.random.randint(-1,2,(n,3)),axis=0) for i in range(bins)]
        type_ = GeomPoints
        runs = []

        for base in bases:
            runs.append(convertToGeom(index_counter,base,type_))

        for nodes in runs:
            for node, idx in nodes(): #FIXME stupid
                nd = render.attachNewNode(node)
                index.update(idx) #FIXME this is nasty
                print(idx)
        for uid,list_ in index.items():
            #TODO to change the color of a selected node we will need something a bit more ... sophisticated
            #parent = list_[1][0]
            if list_ == None:
                continue
            cNode = collideRoot.attachNewNode(CollisionNode('collider %s'%uid)) #ultimately used to index??
            cNode.node().addSolid(CollisionSphere(0,0,0,.5))
            cNode.node().setIntoCollideMask(BitMask32.bit(1))
            cNode.setPos(*list_[0])
            cNode.setPythonTag('uid',uid)
            cNode.show()
            list_[2] = cNode #FIXME this is inconsistent and the 'uid' means different things in different contexts!
        print(index_counter.value)


def _main():
    from util import Utils
    from ui import CameraControl, Axis3d, Grid3d
    #from panda3d.core import ConfigVariableBool
    #ConfigVariableString('view-frustum-cull',False)
    from panda3d.core import loadPrcFileData
    from time import time
    from panda3d.core import PStatClient
    PStatClient.connect()
    loadPrcFileData('','view-frustum-cull 0')
    #loadPrcFileData('','threading-model Cull/Draw') #bad for lots of nodes
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = Utils()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    base.disableMouse()
    #pt = PointsTest(999,99999)
    #pt = PointsTest(1,9999999)
    #pt = PointsTest(1,999999) #SLOW AS BALLS: IDEA: render faraway nodes as static meshes and transform them to live as we get closer!
    #pt = PointsTest(9999999,1)
    #pt = PointsTest(99999,100) #runs fine when there is only 1 node >_<
    #pt = PointsTest(999,10) #runs fine when there is only 1 node >_<
    #pt = PointsTest(1,99999) #still slow :/
    #pt = PointsTest(1,9999) #still slow :/ #deep trees segfault!
    #pt = PointsTest(1,4000) #still slow :/ #this one is ok
    #pt = PointsTest(1,999) #still slow
    #pt = PointsTest(1,499) #still slow 15 fps with 0,0,0 positioned geom points
    #pt = PointsTest(1,249) #about 45fps :/
    bins = 1 #999=.057, below 200 ~.044 so hard to tell (for n = 99)
    #FIXME low numbers of points causes major problems!
    #nt = NodeTest(999999,bins) #the inscreased time is more pronounced with larger numbers of nodes... is it the serialization?
    #ct = CollTest(9999,bins) #the inscreased time is more pronounced with larger numbers of nodes... is it the serialization?
    #nt = NodeTest(999,5)
    #base.camLens.setFar(9E12) #view-frustum-cull 0
    bs = BoxSel() #some stuff
    ft = FullTest(999,bins)
    run() #looks like this is the slow case... probably should look into non blocking model loading?

def main():
    from util import Utils
    from ui import CameraControl, Axis3d, Grid3d
    from panda3d.core import loadPrcFileData
    from time import time
    from panda3d.core import PStatClient

    PStatClient.connect()
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = Utils()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    bs = BoxSel() #TODO
    base.disableMouse()

    #render something
    ct = CollTest(2000)
    #ft = FullTest(99,1)

    run() # we don't need threading for this since panda has a builtin events interface


if __name__ == '__main__':
    main()
