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

from numpy import sign

import sys
from threading import Thread
from IPython import embed

keybinds = {
    'view': {
        #'':'mouse1',
        #'':'mouse2',
        #'':'mouse3',
        #'pan':'mouse3',
        #'zoom':'mouse2', #this should allow L->R to zoom out etc up down is too awkward
        #'rotate':'mouse1',
        'pitch':'mouse3',
        'yaw':'mouse1',
        'roll':'mouse2',
        #'zoom in':'wheel_up',
        #'zoom out':'wheel_down',
    },
    'zmode': {
        'pitch':'', #not needed the mouse does this
        'yaw':'', #the mouse does this
        'roll':'mouse2',
    }
}


class CameraControl(DirectObject):
    """ adds controls to a given camera, usually base.camera"""
    def __init__(self,camera=None):
        self.camera = camera
        if self.camera == None:
            self.camera = base.camera
        for function,key in keybinds['view'].items():
            #self.accept(key,taskMgr.add,(getattr(self,function),function+'Task'))
            self.accept(key, self.makeTask, [function,])
            if key in {'mouse1','mouse2','mouse3'}:
                self.accept(key+'-up', self.endTask, [function,])

        self.XGAIN = 1
        self.YGAIN = 1

        self.accept("escape", sys.exit)
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

        self.__ch__=None
        self.__cp__=None
        self.__cr__=None

        pass

    def getWindowSize(self):
        return base.win.getX

    def makeTask(self, function):
        x,y = base.mouseWatcherNode.getMouse()
        #setattr(self, '__%sTask_sx__'%function, x)
        #setattr(self, '__%sTask_sy__'%function, y)
        setattr(self, '__%sTask_s__'%function, (x,y)) #this should be faster
        taskMgr.add(getattr(self,function), function+'Task')

    def endTask(self, function):
        taskMgr.remove(function+'Task')
        #setattr(self, '__%sTask_sx__'%function, None)
        #setattr(self, '__%sTask_sy__'%function, None)
        setattr(self, '__%sTask_s__'%function, None) #this should be faster
        self.__ch__=None
        self.__cp__=None
        self.__cr__=None

    def getMouseDdDt(self, name): #XXX deprecated
        """ use gain to adjust pixels per degree
            this should probably be normalized to screen size actually?
            or no... but to what?
        """
        x,z = base.mouseWatcherNode.getMouse()
        sx,sz = getattr(self,'__%s_start__'%name)
        print(x,sx)
        print(z,sz)
        if z != sz or x != sx: #watch out for aliasing here...
            norm = (((x - sx) * self.XGAIN)**2 + ((z - sz) * self.YGAIN)**2)**.5
            #norm =  ((x - sx) * self.X_GAIN), ((z - sz) * self.Y_GAIN)
            setattr(self, '__%s_start__'%name, (x,z))
            return norm
        else: #mouse has not moved
            return 0

    def getMouseDdDf(self,name):
        x,y = base.mouseWatcherNode.getMouse()
        sx,sy = getattr(self,'__%s_s__'%(name))
        #if i != si:
            #setattr(self, '__%s_s%s__'%(name,dim), i)
        dx = (x - sx) * self.XGAIN
        dy = (y - sy) * self.YGAIN
        return dx, dy

    #if we are in camera mode
    def pitch(self, task):
        dx,dy = self.getMouseDdDf(task.getName())
        if self.__cp__ == None:
            self.__cp__ = self.camera.getP()
        self.camera.setP(self.__cp__ - dy)
        print('got pitch',dy)
        return task.cont

    def yaw(self, task): #AKA heading in hpr
        dx,dy = self.getMouseDdDf(task.getName())
        if self.__ch__ == None:
            self.__ch__ = self.camera.getH()
        self.camera.setH(self.__ch__ - dx)
        print('got yaw',dx)
        return task.cont

    def roll(self, task):
        dx,dy = self.getMouseDdDf(task.getName())
        if self.__cr__ == None:
            self.__cr__ = self.camera.getR()
        #ccw vs cw, determined in the ++ quadrant of r2
        #ul = ccw, dr = cw
        #norm + sign
        #assume ccw = -, cw = +
        r=sign(dx)*-sign(dy)*(dx**2 + dy**2)**.5

        self.camera.setR(self.__cr__ - r)
        print('got roll',r)
        return task.cont



def main():
    from direct.showbase.ShowBase import ShowBase
    from test_objects import Grid3d
    from util import Utils
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    ut = Utils()
    cc = CameraControl()
    grid = Grid3d()
    base.disableMouse()
    run()

if __name__ == '__main__':
    main()

