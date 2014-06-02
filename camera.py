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

import sys
from threading import Thread
from IPython import embed

keybinds = {
    'view': {
        '':'mouse1',
        '':'mouse2',
        '':'mouse3',
        'pan':'mouse3',
        'zoom':'mouse2', #this should allow L->R to zoom out etc up down is too awkward
        'rotate':'mouse1',
        'pitch':'',
        'yaw':'',
        'roll':'',
        'zoom in':'wheel_up',
        'zoom out':'wheel_down',
    },
    'zmode': {
        'pitch':'', #not needed the mouse does this
        'yaw':'', #the mouse does this
        'roll':'mouse2',
    }
}


class CameraControl(DirectObject):
    """ adds controls to a given camera, usually base.camera"""
    def __init__(self,camera=base.camera):
        self.camera = camera
        for function,key in keybinds['view'].items():
            #self.accept(key,taskMgr.addTask,(getattr(self,function),function+'Task'))
            self.accept(key, self.makeTask, function)
            if key in {'mouse1','mouse2','mouse3'}:
            self.accept(key+'-up',taskMgr.remove(function+'Task')) #FIXME doesnt work with modifiers
        #self.accept('mouse1') #mouse 1 by itself does selection?
        #self.accpet('mouse3') #pan
        #self.accpet('mouse2')

        #--camera moves relatvie to arbitrary origin--
        #pan in plane
        #zoom #this needs to be on a log scale, linear is balls
        #rotate
        #--camera in place--
        #roll camera in place
        #yaw
        #pitch
        #look at selection/origin/center of mass of
        #--camera lense changes--
        #fov (for perspective)
        #perspective/orthographic
        #--worldcraft--
        #z mode wasd + mouse to orient for zooming

        #--selection functions we need to leave space for--
        #drop origin if we don't have something selected
        #click select
        #drag select, logial intersec
        #right click for menu

        pass


    def makeTask(self, function):
        x,z = base.mouseWatcherNode.getMouse()
        setattr(self, function, 

    def getMouseDisplacement(self):

    def getMouseStart(self):

    def panTask(self, task):
        pass
    def zoomTask(self, task):
        pass
    def rotateTask(self, task):
        pass

    #if we are in camera mode
    def pitch(self, task):
        pass
    def yaw(self, task):
        pass
    def roll(self, task):
        pass



def main()
    from direct.showbase.ShowBase import ShowBase
    from test_objects import Grid3d
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    base.disableMouse()
    cc = CameraControl()
    grid = Grid3d()
    run()


