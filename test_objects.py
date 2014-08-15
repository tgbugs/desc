#!/usr/bin/env python
from __future__ import print_function
#import direct.directbase.DirectStart #FIXME showbase
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectSlider
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
#from panda3d.core import PandaNode#, NodePath
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
from ipython import embed
from uuid import uuid4

from monoDict import MonoDict as md
from defaults import *
from keys import HasKeybinds, event_callback, AcceptKeys
from ui import GuiFrame
from trees import treeMe

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
import zlib

sys.modules['core'] = sys.modules['panda3d.core']

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


def makeSimpleGeom(array, ctup, geomType = GeomPoints, fix = False):
    fmt = GeomVertexFormat.getV3c4()

    vertexData = GeomVertexData('points', fmt, Geom.UHDynamic) #FIXME use the index for these too? with setPythonTag, will have to 'reserve' some
    cloudGeom = Geom(vertexData)
    cloudNode = GeomNode('just some points')

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    if fix:
        if len(ctup) == len(array):
            for point,c in zip(array, ctup):
                verts.addData3f(*point)
                color.addData4f(*c)
        else:
            for point in array:
                verts.addData3f(*point)
                color.addData4f(*ctup)
    else:
        for point in array:
            verts.addData3f(*point)
            color.addData4f(*ctup)

    points = geomType(Geom.UHDynamic)
    points.addConsecutiveVertices(0,len(array))
    points.closePrimitive()

    cloudGeom.addPrimitive(points)
    cloudNode.addGeom(cloudGeom) #TODO figure out if it is faster to add and subtract Geoms from geom nodes...

    if fix:
        return cloudNode.__reduce__()
    else:
        return cloudNode  # decoding fails becuase ForkingPickler is called for reasons beyond comprehension

 

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
                cNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
                cNode.setPos(nd,*position)
                if show:
                    cNode.show()
                n+=1
            r+=1
        embed()

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
            cNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
            cNode.setPos(*list_[0])
            cNode.setPythonTag('uid',uid)
            cNode.show()
            list_[2] = cNode #FIXME this is inconsistent and the 'uid' means different things in different contexts!
        print(index_counter.value)


def _main():
    from util import ui_text
    from ui import CameraControl, Axis3d, Grid3d
    #from panda3d.core import ConfigVariableBool
    #ConfigVariableString('view-frustum-cull',False)
    from panda3d.core import loadPrcFileData
    from time import time
    from panda3d.core import PStatClient
    from dragsel import BoxSel
    PStatClient.connect()
    loadPrcFileData('','view-frustum-cull 0')
    #loadPrcFileData('','threading-model Cull/Draw') #bad for lots of nodes
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = ui_text()
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

def WRAP_PROC(asdf):
    return makeSimpleGeom(*asdf)

from multiprocessing import Pool
from process_fixed import ProcessPoolExecutor 
pool = ProcessPoolExecutor()
#pool = Pool()


def make4d(array4, ctup, geomType = GeomPoints):
    """
        array4 should be indexed as follows:
        (time steps, number of points, xyz)
    """
    def make_iter():
        #if hasattr(ctup,'__iter__'):
            #for array3, ctup_ in zip(array4, ctup):
                #yield array3, ctup_, GeomPoints, True
        #else:
        if len(ctup) == len(array4[0]):
            for array3 in array4:
                yield array3, ctup, geomType, True
        else:
            for array3,c in zip(array4,ctup):
                yield array3, c, geomType, True

    zipped = make_iter()
    #out = []
    a = pool.map(WRAP_PROC, zipped)
    #out = [i[0](i[1][0],i[1][1]) for i in a]  # for whatever reason this thinks pickle...
    out = [i for i in a]
    out = [nt.decodeFromBamStream(data) for f,(nt,data) in out]
    
    #embed()
    
    """
    for array3, ctup__ in zip(array4,ctup):  # FIXME ppe?
    #for array3 in array4:
        g = makeSimpleGeom(array3, ctup__, geomType)  # FIXME fmt slow
        out.append(g)
    #"""
    return out

class fourObject:  # should probably inherit from our base object class
    def __init__(self, geomList, collList = None):
        #self.geomList = geomList
        #print(geomList)
        geomRoot = render.find('geomRoot')
        self.parent = geomRoot.attachNewNode(GeomNode(''))
        collRoot = render.find('collideRoot')
        self.coll_parent = collRoot.attachNewNode(CollisionNode('ObjectRoot'))
        self.__geom_list__ = []
        for geomNode in geomList:
            nodepath = self.parent.attachNewNode(geomNode)
            nodepath.stash()
            self.__geom_list__.append(nodepath)

        self.__coll_list__ = []
        if collList:
            self.__coll_list__ = collList
            for collNode in self.__coll_list__:
                collNode.reparentTo(self.coll_parent)
                collNode.stash()
        #print(self.__geom_list__)
        self.__geom__ = None
        self.__coll__ = None
        self.__set_index__(0)
        self._all = False

    def stash(self):
        self.parent.stash()
        self.coll_parent.stash()

    def unstash(self):
        self.parent.unstash()
        self.coll_parent.unstash()

    def set_size(self, size):
        self.parent.setRenderModeThickness(size)

    def __set_index__(self, index):
        geom = self.__geom_list__[index]  # error check first
        coll = self.__coll_list__[index]  # error check first
        if self.__geom__:
            self.__geom__.stash()
        self.__geom__ = geom
        self.__geom__.unstash()
        if self.__coll__:
            self.__coll__.stash()
        self.__coll__ = coll
        self.__coll__.unstash()
        self.__index__ = index
        print('set index to', index)

    def next_index(self):
        next_ = (self.__index__ + 1) % len(self.__geom_list__)
        self.__set_index__(next_)

    def prev_index(self):
        prev_ = (self.__index__ - 1) % len(self.__geom_list__)
        self.__set_index__(prev_)

    def goto_index(self, index):
        try:
            self.__set_index__(index)
        except IndexError:
            print('Invalid index.')

    def show_all(self):
        if not self._all:
            self.coll_parent.unstash()
            for n,c in zip(self.__geom_list__,self.__coll_list__):
                n.unstash()
                c.unstash()
            self._all = True

    def hide_all(self):
        if self._all:
            for n,c in zip(self.__geom_list__,self.__coll_list__):
                n.stash()
                c.stash()
            #self.goto_index(self.__index__)
            self._all = False

    def __len__(self):
        return len(self.__geom_list__)

class nObject:
    """ This would probably represent a single TYPE level entity, with each
        column set of the row vectors being data pretaining to the same single
        TOKEN

        we need to enforce the idea that each MEASUREMENT property must be scalar
        COMPUTED properties, such as averages or arbitrary functions over multiple
        measurements, the key difference probably being uniformity of sampling in time
        
        so then what is a time serries? a whole bunch of repeated measurements of a quantity
        break our data up as follows:
        (NOTE: assumptions about the stability of the system for non-concurrent no or partial order
        no order
        pre order
        partial order
        total order
        total order with gurantees about sampling

        TODO: gurantees about independence? statistical assertions about said type?
    """
    fmt = GeomVertexFormat.getV3c4()
    geomType = GeomPoints  # FIXME this should probably be instance or even render specific
    def __init__(self, prop_vecs, prop_names):
        # TODO continuous or discrete sample space aka timeserries w/ regular intervals?
        self.prop_vecs = prop_vecs  # iterable of property vectors, all of the same length
        self.props = {name:index for index,name in enumerate(prop_names)}

        self._x = None
        self._y = None
        self._z = None
        self._t = None

        self.parent = render.find('geomRoot').attachNewNode(GeomNode(''))  # FIXME naming
        self.__node__ = None
        self.__coll_node__ = None
        self.__old_nodes__ = []  # FIXME dict by hash_
        self.__old_coll_nodes__ = []  # FIXME dict by hash_
        self.__t_index__ = 0

    def msgVec(self, ctup, x, y, z):
        vertexData = GeomVertexData('points', self.fmt, Geom.UHDynamic)
        cloudGeom = Geom(vertexData)
        cloudNode = GeomNode('just some points')

        verts = GeomVertexWriter(vertexData, 'vertex')
        color = GeomVertexWriter(vertexData, 'color')

        for x_, y_, z_, c in zip(x, y, z, ctup):
            verts.addData3f(x_, y_, z_)
            color.addData4f(*c)

        points = self.geomType(Geom.UHDynamic)  # FIXME static?
        points.addConsecutiveVertices(0,len(x))
        points.closePrimitive()

        cloudGeom.addPrimitive(points)
        cloudNode.addGeom(cloudGeom) #TODO figure out if it is faster to add and subtract Geoms from geom nodes...
        print(cloudNode)
        return cloudNode

    def draw(self):
        print('drawing')
        if self._t:
            sorted_ = np.argsort(self.prop_vecs[self._t])
            out = [self.prop_vecs[dim][sorted_] for dim in [self._x, self._y, self._z]]  # FIXME timeserries >_< WHARGH
            # FIXME, solution is to have multiple nObjects, but that is not performant :/
        else:
            out = self.prop_vecs[[self._x, self._y, self._z]]

        ctup = np.random.rand(len(out[0]), 4)  # FIXME

        if self.__node__:
            self.__node__.stash()  # FIXME going to need a way to retrieve previous view modes
            self.__old_nodes__.append(self.__node__)
        self.__node__ = self.parent.attachNewNode(self.msgVec(ctup, *out))
        self.set_size(2)

        if self.__coll_node__:
            self.__coll_node__.stash()
            self.__old_coll_nodes__.append(self.__coll_node__)

        # collision stuff  slow :(
        in_ = np.array([list(a) for a in zip(*out)])
        uui = np.array([ '%s'%uuid4() for _ in range(len(in_))]) # in this context these are token uuids?
        # TODO want to be able to keep those points hilighted even when we change the view
        gc = np.ones(len(in_))

        node = treeMe(None, in_, uui, gc)
        node.reparentTo(render.find('collideRoot'))
        self.__coll_node__ = node

    def set_size(self, size):
        self.__node__.setRenderModeThickness(size)

    def set_x(self, prop_name, *args):
        self._x = self.props[prop_name]
        print(self._x, self._y, self._z)
        if self._x is not None and self._y is not None and self._z is not None:
            self.draw()
    def set_y(self, prop_name, *args):
        self._y = self.props[prop_name]
        print(self._x, self._y, self._z)
        if self._x is not None and self._y is not None and self._z is not None:
            self.draw()
    def set_z(self, prop_name, *args):
        self._z = self.props[prop_name]
        print(self._x, self._y, self._z)
        if self._x is not None and self._y is not None and self._z is not None:
            self.draw()
    def set_t(self, prop_name, *args):
        self._t = self.props[prop_name]
        print(self._x, self._y, self._z)
        if self._x is not None and self._y is not None and self._z is not None:
            self.draw()


class Order:
    TYPES = {
        'NONE':0,  # pretty rare that we will get an unorderable set
        'PRE':2,  # a list of two length tuples of indexes defining the preorder relation on the set
        'PARTIAL':2,  #
        'TOTAL':1,  # if the data type is a number, then we don't need to worry about it
        'INTRIN':0,
    }
    def __init__(self, type_):
        pass

class Set:
    """
        dimensions = 0 => scalar
    """
    def __init__(self, instances, order):
        pass

class RelationClass:  # there will be many different realtion classes with their own meanings (hello tripples), but the orders that they can take are limited
    """
        A relation class contains the adjascency matrix for a set of nodes and edges
        As well as the preorder for reachability to speed up sorting opperations
        It also defines the type or order that particular set of objects will have
    """
    def __init__(self, name):
        self.name = name
        self.adj_matrix = None
        self.reachability = None

        unordered = True
        if unorderd:
            for f in [ 'lt', 'le', 'gt', 'ge']:
                setattr(self, f, lambda : raise NotImplementedError('This class is unordered, stop trying to compare it.'))


    def add_member(self, member):  # FIXME we could also use this function to just create a member without extra code?
        """
            when creating a new vertex for a given relation class or object participating in an order
            simply call rc.add_member(self) during object __init__
        """
        #add the member as a vertex

    def del_member(self, member):
        # will we ever use this?
        pass

    def add_edge(self, start, end):
        pass

    def del_edge(self, start, end):
        pass

    # I think with this combination of things we can implement everything down to preorders by controling how <= >= and == interact
    def lt(self, a, b):
        pass
    def le(self, a, b):
        pass
    def eq(self, a, b):
        pass
    def ne(self, a, b):
        pass
    def gt(self, a, b):
        pass
    def ge(self, a, b):
        pass

class RCMember:
    def __init__(self, relation_class):
        self.relation_class = relation_class
        self.realtion_class.add_member(self)

    def __lt__(self, other):
        if self.relation_class.lt(self, other):
            return True
        else:
            return False

    def __le__(self, other):
        if self.relation_class.le(self, other):
            return True
        else:
            return False

    def __eq__(self, other):
        if self.relation_class.eq(self, other):
            return True
        else:
            return False

    def __ne__(self, other):
        if self.relation_class.eq(self, other):
            return False
        else:
            return True

    def __gt__(self, other):
        if self.relation_class.gt(self, other):
            return True
        else:
            return False

    def __ge__(self, other):
        if self.relation_class.ge(self, other):
            return True
        else:
            return False





class Property:  # FIXME should inherit from something like a time serries?
    """ a type level property object
        instances (values) in a property object should have a way of ordering themselves
        or raise an error if they fail
    """

    # TODO, for graphs, we we do not precompute reachability (the preorder) then implementing orderability calcs
    # will require repeatedly walking edges >_<, also, loads of work to add new orderable types
    # or we require a ton of memory using adj lists
    def __init__(self, name, instances):
        self.name = name
        self.instances = instances
        self.instance_type = 

    def __iter__(self):
        for instance in self.instances:
            yield instance

    def __repr__(self):
        return self.name+' with %s tokens'%len(self.instances)


class Prop_Computed(Property):
    """
        A property computed from a collection of other properties
    """
    def __init__(self, name, function, *properties):
        # how do we figure out the output type without a type system!?
        #expected_length = len(properties[0])  # FIXME, probably should raise a warning, otherwise assume that all props are same lenght, and alert that zip() goes w/ shortest, return ERROR or something?
        #for i, p in enumerate(properties):
            #if len(p) != expected_length:
                #raise ValueError('Property lengths do not match! Your %sth column (and possibly other) did not match.'%i)  # XXX TypeError? check numpy
        self.properties = properties

    def __iter__(self):
        for props in zip(*properties):  # I wonder if this is really inefficient
            yield function(*args)


class HasProperties:
    def __init__(self, properties):
        self.properties = properties

class dond(DirectObject, HasKeybinds):
    def __init__(self):
        #n_tokens = 99999  # 100k not so bad...
        n_tokens = 9999
        n_props = 6
        data1 = np.random.uniform(-100,100,(n_props/2,n_tokens))
        data2 = np.random.normal(0,100,(n_props/2,n_tokens))
        data = np.vstack([data2, data1])
        self.names = ['%s'%uuid4() for _ in range(n_props)]
        self.no = nObject(data, self.names)
        self.frame = GuiFrame('Object selector','f')
        self.accept('z',self.refresh)
    def refresh(self):  # FIXME adding repeatedly rather than updating
        for name in self.names:
            self.frame.add_item('x_'+name, self.no.set_x, (name,))
            self.frame.add_item('y_'+name, self.no.set_y, (name,))
            self.frame.add_item('z_'+name, self.no.set_z, (name,))
            self.frame.add_item(' ')

class do4d(DirectObject, HasKeybinds):
    def __init__(self):
        tsteps = 10  # this is really molecules
        npoints = 999  # this is realy timesteps
        self.slider = DirectSlider(range=(0,1), value=0, pageSize=1, thumb_frameSize=(0,.04,-.02,.02), command=self.t_set)
        self.slider.setPos((0,0,-.9))

        data = np.cumsum(np.random.randint(-1,2,(tsteps,npoints,3)), axis=1)
        data2 = [data[:,i,:] for i in range(len(data[0]))]
        #embed()
        ctup = np.random.rand(tsteps, 4)
        tm1 = [treeMe(None, d, np.array(['%s'%uuid4() for _ in d]),np.ones(len(d))) for d in data]
        self.f1 = fourObject(make4d(data,ctup, geomType = GeomLinestrips), tm1 )
        sc1 = lambda: self.set_selected(self.f1)
        self.f1.coll_parent.setPythonTag('selection_callbacks', [sc1])
        self.set_selected(self.f1)

        tm2 = [treeMe(None, d, np.array(['%s'%uuid4() for _ in d]),np.ones(len(d))) for d in data2]
        self.f2 = fourObject(make4d(data2,ctup), tm2)
        self.f2.set_size(3)
        self.f2.stash()
        sc2 = lambda: self.set_selected(self.f2)
        self.f2.coll_parent.setPythonTag('selection_callbacks', [sc2])

        # TODO make clicking not on the button set the slider position?
        self.accept('s',self.set_selected, [self.f2])

    def set_selected(self, fourObject):  # TODO type check?
        self.selected = fourObject
        self.selected.unstash()
        self.slider['range'] = (0,len(self.selected)-1)
        self.slider['value'] = fourObject.__index__
        print('selected set to', fourObject)

    @event_callback('a')
    def t_all(self):
        if not self.selected._all:
            self.selected.show_all()
        else:
            self.selected.hide_all()
    

    def t_set(self):
        value = int(self.slider['value'])
        if value != self.selected.__index__:
            self.selected.goto_index(value)

    @event_callback((']',']-repeat'))
    def t_up(self):
        #self.selected.next_index()
        self.slider['value'] = (self.slider['value'] + 1) % len(self.selected)

    @event_callback(('[','[-repeat'))
    def t_down(self):
        #self.selected.prev_index()
        self.slider['value'] = (self.slider['value'] - 1) % len(self.selected)


def main():
    from util import ui_text, frame_rate, exit_cleanup, startup_data
    from ui import CameraControl, Axis3d, Grid3d
    from panda3d.core import loadPrcFileData
    from time import time
    from panda3d.core import PStatClient

    from selection import BoxSel
    from render_manager import renderManager


    PStatClient.connect()
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = ui_text()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    base.disableMouse()
    frame_rate()
    startup_data()

    #render something
    #ct = CollTest(2000)
    #ft = FullTest(99,1)

    renderManager()
    frames = {'data':GuiFrame('data','f')}
    bs = BoxSel(frames) # FIXME must be started after renderManager >_<

    dnd = dond()
    #d4d = do4d()

    ec = exit_cleanup()
    ac = AcceptKeys()
    run() # we don't need threading for this since panda has a builtin events interface


if __name__ == '__main__':
    main()
