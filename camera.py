from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import NodePath
from panda3d.core import TextNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Vec3,Vec4

from numpy import sign

from collections import defaultdict
import sys
from threading import Thread
from IPython import embed

keybinds = {
    'view': {
        #'':'mouse1',
        #'':'mouse2',
        #'':'mouse3',
        #'zoom':'mouse2', #this should allow L->R to zoom out etc up down is too awkward
        #'pitch':'shift-mouse3',
        'rotate':'mouse3',
        'pan':'shift-mouse3',
        'look':'mouse2', #note mouse 2 is middle mouse
        'roll':'shift-mouse2',
        'zoom_in':'wheel_up',
        'zoom_out':'wheel_down',
        'zoom_in_slow':'shift-wheel_up',
        'zoom_out_slow':'shift-wheel_down',
        'zoom_in_fast':'control-wheel_up',
        'zoom_out_fast':'control-wheel_down',
        'home':'h',
    },
    'zmode': {
        'pitch':'', #not needed the mouse does this
        'yaw':'', #the mouse does this
        'roll':'mouse2',
    }
}

def makeEquiTri():
    colors = (
        (1,1,1,1),
        (1,0,0,1),
        (0,0,1,1),
        (0,1,0,1),
        (1,1,1,1),
        (1,0,0,1),
    )
    points = (
        (-1,0,0),
        (1,0,0),
        (0,3**.5/2,3**.5),
        (0,3**.5,0),
        #(-1,0,0),
        #(1,0,0),
    )

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    #fmt = GeomVertexFormat.getV3() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for p,c in zip(points,colors):
        verts.addData3f(*p)
        color.addData4f(*c)

    targetTris = GeomTristrips(Geom.UHStatic)
    targetTris.addConsecutiveVertices(0,4)
    targetTris.addVertex(0)
    targetTris.addVertex(1)
    targetTris.closePrimitive()

    target = Geom(vertexData)
    target.addPrimitive(targetTris)
    return target



def main():
    from direct.showbase.ShowBase import ShowBase
    from test_objects import Grid3d,Axis3d
    from util import ui_text
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = ui_text()
    cc = CameraControl()
    grid = Grid3d()
    axis = Axis3d()
    base.disableMouse()
    run()

if __name__ == '__main__':
    main()

