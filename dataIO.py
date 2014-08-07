"""
    DirectObject class in panda for DRAWING the data we get back, this might be run on a remote panda instance?
"""
import zlib
import pickle
from time import sleep
from uuid import uuid4

import numpy as np
from ipython import embed

from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode, PandaNode, NodePath
from panda3d.core import CollisionNode, CollisionSphere
from panda3d.core import BitMask32

from defaults import *

#scene renderer is what we will use to coordinate receiving the set of visible objects to render
#the total set of possible objects could be treated as another sceneRednerer???

#NOTE: we do NOT deal with selection call backs here, instead we use the UUID that they return
#and handle that in our selection code

#XXX use CollisionTube for rectangular stuff, its not perfect (corners) but it is better than the alternative

def buildRequest(selected_uuids, selected_properties):
    """ Build and dispatch a request and return a future 
        indicating that we expect to receive a compiled set
        of objects to render

        The arguments accept a list of uuids and a list of properties for each
        uuid so that we can dispatch multiple requests at once even if they
        are for different coordinate systems
    """
    { uuid:properties for uuid,properties in zip(selected_uuids, selected_properties) }
    return future

class bamCache(object):
    """ A tree structure that holds ranked related bams, probably should
        be a splay tree? not now, use a dict
    """
    def __init__(self):
        pass

class requestPredictor(object):
    """ Given a request for data compute a bunch or related requests.
        Probably needs a record of bams that have already been requested.
    """
    def __init__(self, user):
        if user:
            #TODO retrieve the previous cache for that user
            self.cache = {}
        else:
            self.cache = {}

    def getRelated(self, request):
        """ If we want to get real fancy we can try to do prediction based on
            Previous user request patterns or just all existing requests.
            Probably need a way to do this in parallel and not worry about
            _perfect_ concurrency?
        """
        #1 other views of the same data
        #2 sub trees
        #3 XXX problem: compiling a new bam every time can get really expensive
            #if we want to make small changes :/, it is good for performance
            #bad for keeping things modifiable
        #4 maybe we can get around the problem by caching bams... or by flattening?
            #if we want to leverage the power to scale the size of something by a value
            #then maybe we *should* look at using individual nodes when there are fewer
            #values on screen?
        #5 apparently we can traverse geomNodes and find all their constituent geoms and
            #scale those in place???
        #6 editing of the geom structure in place seems like it might be a better way to manage this
            #when we want to make small changes to the larger structure, just tweak a subset
            #of the verts

    def rankRelated(self, request):
        pass

    def rankCache(self):
        """ Rank the bams in the cahce, probably don't need this since
            The cache should be ranked based on the original rank and
            then just put in in temporal order. Then things at the end
            of the cache will be popped off. Whenever a cached bam is
            requested it and its related (ooop need a tree) bams should
            all be put back at the top.
        """
        #Start by rendering the requested setup to a bam stream and then
        #compute other related views automatically.

class bamReceiver(DirectObject):
    def __init__(self):
        self.cache = {}

class requestBuilder(object):
    """ Generate a json (or the like) request for data
        maybe sqlalchemy? who knows
    """
    def request(self, uuid, properties):
        return ""


class sceneRender(DirectObject):
    def __init__(self,rootNode,collNode): #technically we don't need this becasue render is global? nah, this way we can use things OTHER than render which can be useful for viz
        self.root = rootNode
        self.coll = collNode
        self.sceneCache = {} #dict of hashes of the root for each pair of objects, geometry+collide

    def compileObjects(self,objectList): #this is weak of we want to use 
        """ take whatever strcutre we give to our data objects and compile them
            to points in x,y,z space and create the structure for selecting them
        """
        for obj in objectList:
            pass
            #vectorize the positions
            #vectorize the geometry #XXX all geometry should be reconstructed so its center of mass is 0,0,0 ideally this should be done when we store or generate the geometry
            #vectorize collision type???? hrm how to do this
            #vectorize the uuids

    def collActiveLogic(self, positions, geometry):
        """ Compute semi optimal second level collide nodes that turn on or off the
            main selection collision nodes
        """
        #get the TOTAL number of collion nodes we have
        #numNodes = len(positions)
        #calculate how many higher level nodes we need to gurantee 1000 nodes/level2 node
            #WITHOUT OVERLAP also average l2 z depth should be considered...
        #bccCoverDensity = 1.4635 #(25*pi)/(24 * 5**.5) covering density for bcc
        #numLevel2 = (numNodes * bccCoverDensity ) // 1000  # this gives us worst case for an infinite lattice

        #keep splitting the points into an oct tree until we reach our desired nodes per (500) then sphere up
            #500 gives us 4 deep in z depth with no worries also allows for 4 overlaps at the same time

        #get center of mass for all the points plus max min
        #fastest way to gurantee coverage is to find center of mass and split from there and iterate
        #maybe better to compute the median? yeah but that is orders of magnitude harder

        #find successive centers of mass, create the bounding

        #get max min of collision elements... ideally spheres but we may have to allow other varieies?
        #construct the limits 
        #calculate the number of spheres we need, assume that ideally we want about 500 nodes per 2nd level
            #under the assumption that everything is evenly distribued in space we need this to be smaller
            #since if there is clustering we will actually go OVER our desired number of nodes of ~2000
        #build a bcc lattice of spheres to cover the space and then prune ones with no children

        #calculate the bounding sphere for each geom, this needs to be calculated for further bounding
            #but will also be used as a default of no collision type is specified (ie if the packing
            #of the element in the UI is not expected to overlap) suggest to stick with convex polygons

#just make an oct tree and stick circles on nodes with have >= max points we only need to compute COM and max/min once
#bounding cube has side lengths of 2r
#oct tree order is x, y ,z where x ++++---- y ++--++-- z +-+-+-+- for each quadrant



TREE_LOGIC = np.array([
    [ 1, 1, 1],
    [ 1, 1,-1],
    [ 1,-1, 1],
    [ 1,-1,-1],
    [-1, 1, 1],
    [-1, 1,-1],
    [-1,-1, 1],
    [-1,-1,-1],
])

TREE_MAX_POINTS = 512  # super conventient due to 8 ** 3 = 512 :D basically at the 3rd level we will completely cover our minimum set, so what we do is go back 3 levels ? doesnt seem to work that way really...
#TREE_MAX_POINTS = 1024

def collect_pool(todo):
    output = []
    for thing in todo:
        if thing:
            if hasattr(thing,'__iter__'):
                output += thing  # safe because called all the way down
            else:
                output.append(thing)
    return output

def treeMe(collRoot, positions, uuids, geomCollide, center = None, side = None, radius = None, request_hash = b'Fake', pipe = None):
    """ Divide the space covered by all the objects into an oct tree and then
        replace cubes with 512 objects with spheres radius = (side**2 / 2)**.5
        for some reason this massively improves performance even w/o the code
        for mouse over adding and removing subsets of nodes.
    """
    num_points = len(positions)

    if center == None:
        center = np.mean(positions, axis=0)
        radius = np.max(np.linalg.norm(positions - center))
        side = ((4/3) * radius**2) ** .5
        radius += 2

    if num_points <= 0:
        return False

    bitmasks =  [ np.zeros_like(uuids,dtype=np.bool_) for _ in range(8) ]  # ICK there must be a better way of creating bitmasks
    partition = positions > center
    
    #the 8 conbinatorial cases
    for i in range(num_points):
        index = octit(partition[i])
        bitmasks[index][i] = True

    next_leaves = []
    for i in range(8):
        branch = bitmasks[i]
        new_center = center + TREE_LOGIC[i] * side * .5  #FIXME we pay a price here when we calculate the center of an empty node
        subSet = positions[branch]
        next_leaves.append((collRoot, subSet, uuids[branch], geomCollide[branch], new_center, side * .5, radius * .5))

    #This method can also greatly accelerate the neighbor traversal because it reduces the total number of nodes needed
    if num_points < TREE_MAX_POINTS:
        leaf_max = np.max([len(tup[1]) for tup in next_leaves])
        if num_points < 4:
            c = np.mean(positions, axis=0)
            dists = []
            for p1 in positions:
                for p2 in positions:
                    if p1 is not p2:
                        d = np.linalg.norm(np.array(p2) - np.array(p1))
                        dists.append(d)
            r = np.max(dists) + np.mean(geomCollide) * 2  #max dists is the diameter so this is safe
            l2Node = collRoot.attachNewNode(CollisionNode("%s.%s"%(request_hash,c)))
            l2Node.node().addSolid(CollisionSphere(c[0],c[1],c[2],r))
            l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))
        elif leaf_max > num_points * .90:  # if any leaf has > half the points
            todo = [treeMe(*leaf) for leaf in next_leaves]
            if pipe:  # extremely unlikely edge case
                print("hit an early pip")
                to_send = collect_pool(todo)
                for s in to_send:
                    pipe.send(s)
                pipe.close()
                return None
            else:
                return collect_pool(todo)

        else:
            l2Node = collRoot.attachNewNode(CollisionNode("%s.%s"%(request_hash,center)))
            l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius * 2))
            l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))

        for p,uuid,geom in zip(positions,uuids,geomCollide):
            childNode = l2Node.attachNewNode(CollisionNode("%s"%uuid))  #XXX TODO
            childNode.node().addSolid(CollisionSphere(p[0],p[1],p[2],geom)) # we do it this way because it keeps framerates WAY higher dont know why
            childNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
            childNode.setTag('uuid',uuid)
        return l2Node

    todo = [treeMe(*leaf) for leaf in next_leaves]

    if pipe:
        to_send = collect_pool(todo)
        for s in to_send:
            pipe.send(s)
        pipe.close()
    else:
        return collect_pool(todo)

def treeMeMap(leaf):
    return treeMe(*leaf)

def _treeMe(level2Root, positions, uuids, geomCollide, center = None, side = None, radius = None, request_hash = b'Fake'):  # TODO in theory this could be multiprocessed
    """ Divide the space covered by all the objects into an oct tree and then
        replace cubes with 512 objects with spheres radius = (side**2 / 2)**.5
        for some reason this massively improves performance even w/o the code
        for mouse over adding and removing subsets of nodes.
    """

    num_points = len(positions)

    if center == None:  # branch predictor should take care of this?
        center = np.mean(positions, axis=0)
        radius = np.max(np.linalg.norm(positions - center))
        side = ((4/3) * radius**2) ** .5
        radius += 2

    if num_points <= 0:
        return False

    def nextLevel():
        bitmasks =  [ np.zeros_like(uuids,dtype=np.bool_) for _ in range(8) ]  # ICK there must be a better way of creating bitmasks

        partition = positions > center
        
        #the 8 conbinatorial cases
        for i in range(num_points):
            index = octit(partition[i])
            bitmasks[index][i] = True
        output = []
        for i in range(8):
            branch = bitmasks[i]  # this is where we can multiprocess
            new_center = center + TREE_LOGIC[i] * side * .5  #FIXME we pay a price here when we calculate the center of an empty node
            subSet = positions[branch]
            zap = treeMe(level2Root, subSet, uuids[branch], geomCollide[branch], new_center, side * .5, radius * .5)
            output.append(zap)

        return output

    #This method can also greatly accelerate the neighbor traversal because it reduces the total number of nodes needed
    if num_points < TREE_MAX_POINTS:  # this generates fewer nodes (faster) and the other vairant doesnt help w/ selection :(
        l2Node = level2Root.attachNewNode(CollisionNode("%s.%s"%(request_hash,center)))
        l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius*2))
        l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))
        #l2Node.show()

        for p,uuid,geom in zip(positions,uuids,geomCollide):
            childNode = l2Node.attachNewNode(CollisionNode("%s"%uuid))  #XXX TODO
            childNode.node().addSolid(CollisionSphere(p[0],p[1],p[2],geom)) # we do it this way because it keeps framerates WAY higher dont know why
            childNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
            childNode.setPythonTag('uuid',uuid)
            #childNode.show()
        return True

        if num_points < 3:  # FIXME NOPE STILL get too deep recursion >_< and got it with a larger cutoff >_<
            #print("detect a branch with 1")
            return nextLevel()

    return nextLevel()

def octit(position):  # use this not entirely sure why it is better, maybe fewer missed branches?
    """ take the booleans returned from positions > center and map to cases """
    x, y, z = position
    if x:
        if y:
            if z:
                return 0
            else:
                return 1
        else:
            if z:
                return 2
            else:
                return 3
    else:
        if y:
            if z:
                return 4
            else:
                return 5
        else:
            if z:
                return 6
            else:
                return 7

_octit = {
    (False,False,False):0,
    (False,False,True):1,
    (False,True,False):2,
    (False,True,True):3,
    (True,False,False):4,
    (True,False,True):5,
    (True,True,False):6,
    (True,True,True):7,
}

def profileOctit():
    from prof import profile_me

    data = np.random.rand(1000000,3) - .5 > 0

    @profile_me
    def a(data):
        for d in data:
            z = octit(d)

    @profile_me # using the dict is SUPER slow O_O
    def b(data):
        for d in data:
            z = _octit[tuple(d)]

    a(data)
    b(data)

def main():
    from time import time

    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import loadPrcFileData
    from panda3d.core import PStatClient

    from selection import BoxSel
    from util import ui_text, console, exit_cleanup
    from ui import CameraControl, Axis3d, Grid3d
    from test_objects import makeSimpleGeom
    import sys
    sys.modules['core'] = sys.modules['panda3d.core']

    PStatClient.connect() #run pstats in console
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()

    uiRoot = render.attachNewNode("uiRoot")
    level2Root = render.attachNewNode('collideRoot')

    base.setBackgroundColor(0,0,0)
    ut = ui_text()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    base.disableMouse()
    con = console()
    exit_cleanup()

    #profileOctit()


    #counts = [1,250,510,511,512,513,1000,2000,10000]
    #counts = [1000,1000]
    counts = [999 for _ in range(99)]
    for i in range(len(counts)):
        nnodes = counts[i]
        #positions = np.random.uniform(-nnodes/10,nnodes/10,size=(nnodes,3))
        positions = np.cumsum(np.random.randint(-1,2,(nnodes,3)), axis=0)

        #positions = []
        #for j in np.linspace(-10,10,512):
            #positions += [[0,v+j,0] for v in np.arange(-1000,1000,100)]
        #positions = np.array(positions)
        #nnodes = len(positions)

        #uuids = np.arange(0,nnodes) * (i + 1)
        uuids = np.array(["%s"%uuid4() for _ in range(nnodes)])
        geomCollide = np.ones(nnodes) * .5
        out = treeMe(level2Root, positions, uuids, geomCollide)
        #print(out)
        render.attachNewNode(makeSimpleGeom(positions,np.random.rand(4)))

    #uiRoot = render.find('uiRoot')
    #uiRoot.detach()
    bs = BoxSel(False)  # TODO make it so that all the "root" nodes for the secen are initialized in their own space, probably in with defaults or something globalValues.py?
    #base.camLens.setFov(150)
    run()

if __name__ == "__main__":
    main()
