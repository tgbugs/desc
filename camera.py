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
        #'':'mouse1',
        #'':'mouse2',
        #'':'mouse3',
        #'pan':'mouse3',
        #'zoom':'mouse2', #this should allow L->R to zoom out etc up down is too awkward
        #'rotate':'mouse1',
        'pitch':'mouse3',
        'yaw':'mouse1',
        'roll':'mouse2',
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
    def __init__(self,camera=None):
        self.camera = camera
        if self.camera == None:
            self.camera = base.camera
        for function,key in keybinds['view'].items():
            #self.accept(key,taskMgr.add,(getattr(self,function),function+'Task'))
            self.accept(key, self.makeTask, [function,])
            if key in {'mouse1','mouse2','mouse3'}:
                self.accept(key+'-up', self.endTask, [function,])

        self.X_GAIN = 1 #XXX deprecated
        self.Y_GAIN = 1 #XXX deprecated
        self.GAIN={'x':1,'y':1} #degrees >_<

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

    def makeTask(self, function):
        x,y = base.mouseWatcherNode.getMouse()
        setattr(self, '__%sTask_sx__'%function, x)
        setattr(self, '__%sTask_sy__'%function, y)
        taskMgr.add(getattr(self,function), function+'Task')

    def endTask(self, function):
        taskMgr.remove(function+'Task')
        setattr(self, '__%sTask_sx__'%function, None)
        setattr(self, '__%sTask_sy__'%function, None)
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
            norm = (((x - sx) * self.X_GAIN)**2 + ((z - sz) * self.Y_GAIN)**2)**.5
            #norm =  ((x - sx) * self.X_GAIN), ((z - sz) * self.Y_GAIN)
            setattr(self, '__%s_start__'%name, (x,z))
            return norm
        else: #mouse has not moved
            return 0

    def getMouseDdDf(self,name,dim):
        i = base.mouseWatcherNode.getMouse()[{'x':0,'y':1}[dim]]
        si = getattr(self,'__%s_s%s__'%(name,dim))
        print(i,si)
        #if i != si:
            #setattr(self, '__%s_s%s__'%(name,dim), i)
        return (i-si) * self.GAIN[dim] * 15 #FIXME 15 works for some, but not for roll at all

    #if we are in camera mode
    def pitch(self, task):
        dd = self.getMouseDdDf(task.getName(),'y') 
        if self.__cp__ == None:
            self.__cp__ = self.camera.getP()
        self.camera.setP(self.__cp__ - dd)
        print('got pitch',dd)
        return task.cont
    def yaw(self, task): #AKA heading in hpr
        dd = self.getMouseDdDf(task.getName(),'x')
        if self.__ch__ == None:
            self.__ch__ = self.camera.getH()
        self.camera.setH(self.__ch__ - dd)
        print('got yaw',dd)
        return task.cont
    def roll(self, task):
        dd = self.getMouseDdDf(task.getName(),'x') #FIXME both?
        if self.__cr__ == None:
            self.__cr__ = self.camera.getR()
        self.camera.setR(self.__cr__ - dd)
        print('got roll',dd)
        return task.cont



def main():
    from direct.showbase.ShowBase import ShowBase
    from test_objects import Grid3d
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    cc = CameraControl()
    grid = Grid3d()
    base.disableMouse()
    run()

if __name__ == '__main__':
    main()

