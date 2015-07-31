#!/usr/bin/env python3.4

import numpy as np

from panda3d.core import NodePath, CollisionNode, CollisionSphere, BitMask32

from .defaults import BITMASK_COLL_MOUSE
from .defaults import BITMASK_COLL_CLICK
from .prof import profile_me
from .util.ipython import embed

TREE_MAX_POINTS = 512

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

def octit(position):
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

def octTree(positions, indexes = None, center = None, side = None, radius = None):
    """ Given a set of positions (and optionally uuids and radii)
        make and oct tree. Starting parent should be None
    """
    num_points = len(positions)

    if not num_points:
        return None

    if center == None:
        center = np.mean(positions, axis=0)
        norms = np.linalg.norm(positions - center, axis = 1)
        radius = np.max(norms) * .5
        side = ((4/3) * radius**2) ** .5
        indexes = np.arange(num_points)

    l2Node = []

    bitmasks =  [ np.zeros(num_points, dtype=np.bool_) for _ in range(8) ]  # ICK there must be a better way of creating bitmasks
    partition = positions > center
    
    #the 8 conbinatorial cases
    for i in range(num_points):
        index = octit(partition[i])
        bitmasks[index][i] = True

    next_leaves = []
    for i in range(8):
        branch = bitmasks[i]
        new_center = center + TREE_LOGIC[i] * side * .5
        subSet = positions[branch]
        if len(subSet):
            next_leaves.append((subSet, indexes[branch], new_center, side * .5, radius * .5))

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
            r = np.max(dists)  # this is the diameter, so assuming the geomCollide for each position is not huge
            l2Node.append((c, r))
        elif leaf_max > num_points * .90:  # if any leaf has > half the points
            l2Node.append((center, radius *2))
            l2Node.append([octTree(*leaf) for leaf in next_leaves])
            return l2Node  # just for kicks even though all this is in place

        else:
            l2Node.append((center, radius *2))

        l2Node.append(indexes)
        return l2Node
    else:  # we are a containing node
        l2Node.append((center, radius *2))

    l2Node.append([octTree(*leaf) for leaf in next_leaves])
    #l2Node.append([n for n in [octTree(*leaf) for leaf in next_leaves] if n != None])  # don't need, return None should never happen
    return l2Node

def treeMe(parent, positions, uuids, geomCollide, center = None, side = None, radius = None, request_hash = b'Fake', pipe = None):
    """ Divide the space covered by all the objects into an oct tree and then
        replace cubes with 512 objects with spheres radius = (side**2 / 2)**.5
        for some reason this massively improves performance even w/o the code
        for mouse over adding and removing subsets of nodes.
    """
    num_points = len(positions)

    if not num_points:
        return None

    if center == None:  # must use equality due to id changing across interpreters
        center = np.mean(positions, axis=0)
        norms = np.linalg.norm(positions - center, axis = 1)
        radius = np.max(norms) * .5
        side = ((4/3) * radius**2) ** .5
        if parent == None:
            l2Node = NodePath(CollisionNode('ObjectRoot for %s 0'%request_hash))  # TODO naming for search
        else:
            l2Node = parent.attachNewNode(CollisionNode('ObjectRoot for %s 0'%request_hash))
    else:
        #l2Node = parent.attachNewNode(CollisionNode('%s.%s. %s'%(request_hash, center, int(parent.getName()[-2:]) + 1)))
        l2Node = parent.attachNewNode(CollisionNode(' %s'%(int(parent.getName()[-2:]) + 1)))

    #base_mask = np.zeros_like(uuids, dtype=np.bool_)  # FIXME INSANE INTERACTION WITH SOMETHING panda related
    bitmasks = []
    for _ in range(8):
        bitmasks.append(np.array([False] * len(uuids)))  # must pass by value otherwise we have 8 of the same thing

    #bitmasks =  [ np.zeros_like(uuids,dtype=np.bool_) for _ in range(8) ]  # ICK there must be a better way of creating bitmasks
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
        if len(subSet):
            next_leaves.append((l2Node, subSet, uuids[branch], geomCollide[branch], new_center, side * .5, radius * .5, request_hash))

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
            #l2Node.setName('leaf %s.%s. %s'%(request_hash, c, int(parent.getName()[-2:]) + 1))
            l2Node.node().addSolid(CollisionSphere(c[0],c[1],c[2],r))
            l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))
        elif leaf_max > num_points * .90:  # if any leaf has > half the points
            for leaf in next_leaves:
                treeMe(*leaf)
            #[treeMe(*leaf) for leaf in next_leaves]
            #l2Node.setName('branch '+l2Node.getName())
            l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius * 2))
            l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))  # this does not collide
            if pipe:  # extremely unlikely edge case
                print("hit an early pip")
                pipe.send(l2Node)
                pipe.close()
                return None
            else:
                return l2Node  # just for kicks even though all this is in place

        else:
            #l2Node.setName('leaf '+l2Node.getName())
            l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius * 2))
            l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))

        for p,uuid,geom in zip(positions,uuids,geomCollide):
            childNode = l2Node.attachNewNode(CollisionNode("%s"%uuid))  #XXX TODO
            childNode.node().addSolid(CollisionSphere(p[0],p[1],p[2],geom)) # we do it this way because it keeps framerates WAY higher dont know why
            childNode.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
            childNode.setTag('uuid',uuid)
        return l2Node
    else:  # we are a containing node
        #l2Node.setName('branch '+l2Node.getName())
        l2Node.node().addSolid(CollisionSphere(center[0],center[1],center[2],radius * 2))
        l2Node.node().setIntoCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))  # this does not collide

    for leaf in next_leaves:
        treeMe(*leaf)
    #[treeMe(*leaf) for leaf in next_leaves]

    if pipe:
        pipe.send(l2Node)  # TODO we are going to solve this by sending childs? no, NODE GRRR
        #for c in l2Node.getChildren():
            #pipe.send(c)
            #l2Node.removeChild(c)
        #l2Node.removeAllChildren()
        #pipe.send(l2Node)

        
        #for s in to_send:
            #pipe.send(s)
        pipe.close()
    else:
        #embed()
        return l2Node  # just for kicks even though all this is in place

def main():
    n = 9999
    positions = np.cumsum(np.random.randint(-1,2,(n,3)), axis=0)
    out = octTree(positions)
    #[print(n) for n in out]

if __name__ == "__main__":
    main()
    

