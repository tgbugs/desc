#!/usr/bin/env python
"""
    setRenderModeThickness bug demo

    Bug occures after calling base.run() and using DirectObject.accept
    to call node.setRenderModeThickness(number) while the engine is running.

    See PointsTest.test_task for the call.

    To produce the the bug run this script and press r, g, b, m, or n
    to call setRenderModeThickness on the red, green, blue, or magenta points
    or on geomRoot. Compare the print statements in the terminal to what you see.
    
    When running with only 2 states (1, 5):
        Fun things to press first:
        m everything except the node itself is set to 10
        n only the node that is NOT a child of geomRoot is set to 10

        Fun sequences:
        press m first then n repeatedly
        press n first then press m twice

    When running with 3 states (1, 5, 10):
        My mind is still reeling from the behavior here.

    node graph:

    render
    | |
    | blue
    geomRoot
    | |
    | green
    red
    |
    magenta


"""

from __future__ import print_function
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomPoints
from panda3d.core import GeomNode

import sys

def makePoint(x, y, z, color_tup, geomType=GeomPoints):
    fmt = GeomVertexFormat.getV3c4()

    vertexData = GeomVertexData('points', fmt, Geom.UHDynamic)
    cloudGeom = Geom(vertexData)
    cloudNode = GeomNode('just a point')

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    verts.addData3f(x, y, z)
    color.addData4f(*color_tup)

    points = geomType(Geom.UHDynamic)
    points.addVertex(0)
    points.closePrimitive()

    cloudGeom.addPrimitive(points)
    cloudNode.addGeom(cloudGeom)

    return cloudNode

class PointsTest(DirectObject):
    def __init__(self, num_states):
        self.accept("escape", sys.exit)
        self.accept("r", self.test_task, extraArgs=['red'])
        self.accept("g", self.test_task, extraArgs=['green'])
        self.accept("b", self.test_task, extraArgs=['blue'])
        self.accept("m", self.test_task, extraArgs=['magenta'])
        self.accept("n", self.test_task, extraArgs=['geomRoot'])
        self.geomRoot = render.attachNewNode('geomRoot')
        self.geoms = {'geomRoot':self.geomRoot}
        self.num_states = num_states
        self.rmt_state = {'red':0,
                          'green':0,
                          'blue':0,
                          'magenta':0,
                          'geomRoot':0}

    def load_point(self, x, y, z, color, name=None):
        geom = makePoint(x, y, z, color)
        geomnode = self.geomRoot.attachNewNode(geom)
        if name:
            geomnode.setName(name)
        self.geoms[name]=geomnode
        return geomnode

    def test_task(self, key):
        """
            ****************
            BUG CREATED HERE
            ****************
        """
        print(key)
        if self.rmt_state[key] == 0:
            thickness = 1
        elif self.rmt_state[key] == 1:
            thickness = 5
        elif self.rmt_state[key] == 2:
            thickness = 10
        else:
            raise BaseException('WTF RU DOIN')
        
        print('setting', self.geoms[key], 'to', thickness, 'thickness')
        self.geoms[key].setRenderModeThickness(thickness)  # XXX call is here
        self.rmt_state[key] = (self.rmt_state[key] + 1) % self.num_states  # cycle to next mode

def main():
    base = ShowBase()
    base.disableMouse()
    base.setBackgroundColor(0,0,0)


    # WARNING: testing with 3 states will melt your brain
    pt = PointsTest(num_states=3)  # XXX comment out when testing 2
    #pt = PointsTest(num_states=2)  # XXX uncomment to test with 2 states

    m = pt.load_point(-1.5, 5, 0, (1, 0, 1, 1), 'magenta')
    r = pt.load_point(-.5, 5, 0, (1, 0, 0, 1), 'red')
    g = pt.load_point(.5, 5, 0, (0, 1, 0, 1), 'green')
    b = pt.load_point(1.5, 5, 0, (0, 0, 1, 1), 'blue')

    b.reparentTo(render)
    m.reparentTo(r)

    render.setRenderModeThickness(1)
    print([n for n in render.findAllMatches('*')])

    base.run()

if __name__ == '__main__':
    main()
