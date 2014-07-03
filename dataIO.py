"""
    DirectObject class in panda for DRAWING the data we get back, this might be run on a remote panda instance?
"""

import numpy as np
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CollisionNode, CollisionSphere
from panda3d.core import BitMask32

from defaults import *
#scene renderer is what we will use to coordinate receiving the set of visible objects to render
#the total set of possible objects could be treated as another sceneRednerer???

#NOTE: we do NOT deal with selection call backs here, instead we use the UUID that they return
#and handle that in our selection code

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

def treeMe(level2Root, positions, uuids, geomCollide, center = None, side = None, radius = None):  # TODO in theory this could be multiprocessed
    """ Divide the space covered by all the objects into an oct tree and then
        replace cubes with 512 objects with spheres radius = (side**2 / 2)**.5
        for some reason this massively improves performance even w/o the code
        for mouse over adding and removing subsets of nodes.
    """
    max_points = 512  # super conventient due to 8 ** 3 = 512 :D basically at the 3rd level we will completely cover our minimum set, so what we do is go back 3 levels ? doesnt seem to work that way really...
    num_points = len(positions)

    if center == None:  # branch predictor should take care of this?
        mins = [np.min(positions[:,i])-1 for i in range(3)]  #FIXME geom radius? fixed with -1 and only a concern at the corners really
        maxs = [np.max(positions[:,i])+1 for i in range(3)]
        sides = [maxs[i]-mins[i] for i in range(3)]
        side = max(sides)
        center = [side * .5 + mins[i] for i in range(3)]  # the real center
        radius = (side**2 / 2)**.5

    if num_points <= 0:
        return False
    elif num_points < max_points:
        l2Node = level2Root.attachNewNode(CollisionNode("%s"%center))
        l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius*2))  # does this take a diameter??!
        l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))
        #l2Node.show()
        for p,uuid,geom in zip(positions,uuids,geomCollide):
            childNode = l2Node.attachNewNode(CollisionNode("%s"%uuid))  #XXX TODO
            childNode.node().addSolid(CollisionSphere(p[0],p[1],p[2],geom)) #FIXME need to calculate this from the geometry? (along w/ uuids etc)
            childNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
            childNode.setPythonTag('uuid',uuid)
            #childNode.show()
        return True

    bitmasks =  [ np.bool_(np.zeros_like(uuids)) for _ in range(8) ]  # ICK there must be a better way of creating bitmasks

    partition = positions > center
    #centered = positions - center  #this lets us check against 0
    
    #the 8 conbinatorial cases
    for i in range(num_points):
        index = octit(partition[i])
        bitmasks[index][i] = True

    logic = np.array([
        [ 1, 1, 1],
        [ 1, 1,-1],
        [ 1,-1, 1],
        [ 1,-1,-1],
        [-1, 1, 1],
        [-1, 1,-1],
        [-1,-1, 1],
        [-1,-1,-1],
    ])

    output = []
    for i in range(8):
        branch = bitmasks[i]  # this is where we can multiprocess
        new_center = center + logic[i] * side * .5  #FIXME we pay a price here when we calculate the center of an empty node
        subSet = positions[branch]
        out = treeMe(level2Root, subSet, uuids[branch], geomCollide[branch], new_center, side * .5, radius * .5)
        output.append(out)

    return output




def walkTree(tree,side,center):
    collNodes = []
    if hasattr(tree,'__iter__'): #not at a leaf
        pass
    elif tree:
        pass
    else:  # there were zero nodes in this leaf
        pass


def octit(position):  # use this not entirely sure why it is better, maybe fewer missed branches?
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

def altoctit(position):  # slower
    x, y, z = position
    if   x and y and z:             #+++
        return 0
    elif x and y and not z:         #++-
        return 1
    elif x and not y and z:         #+-+
        return 2
    elif x and not y and not z:     #+--
        return 3
    elif not x and y and not z:     #-++
        return 4
    elif not x and y and not z:     #-+-
        return 5
    elif not x and not y and z:     #--+
        return 6
    elif not x and not y and not z: #---
        return 7


def fixCOM(geom):
    """ Expects a numpy array of points such that point 1 is geom[0]
        we will slice such that xs = geom[:,0] etc
    """
    com = np.mean(geom,axis=0)
    return geom-com


def profileOctit():
    from prof import profile_me

    data = np.random.rand(10000000,3) - .5 > 0

    @profile_me
    def a(data):
        for d in data:
            altoctit(d)

    @profile_me #faster
    def b(data):
        for d in data:
            octit(d)

    a(data)
    b(data)


def main():
    from time import time

    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import loadPrcFileData
    from panda3d.core import PStatClient

    from dragsel import BoxSel
    from util import Utils
    from ui import CameraControl, Axis3d, Grid3d
    from test_objects import makeSimpleGeom

    PStatClient.connect() #run pstats in console
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = Utils()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    bs = BoxSel() #TODO
    base.disableMouse()

    #profileOctit()
    level2Root = render.attachNewNode('collideRoot')
    #counts = [1,250,510,511,512,513,1000,2000,10000]
    #counts = [1000,1000]
    counts = [9999 for _ in range(99)]
    for i in range(len(counts)):
        nnodes = counts[i]
        #positions = np.random.uniform(-nnodes/10,nnodes/10,size=(nnodes,3))
        positions = np.cumsum(np.random.randint(-1,2,(nnodes,3)), axis=0)
        uuids = np.arange(0,nnodes) * (i + 1)
        geomCollide = np.ones(nnodes) * .5
        out = treeMe(level2Root, positions, uuids, geomCollide)
        print(out)
        render.attachNewNode(makeSimpleGeom(positions,np.random.rand(4)))

    run()

if __name__ == "__main__":
    main()
