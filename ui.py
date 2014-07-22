import sys

from collections import defaultdict

from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath, GeomNode
from panda3d.core import Geom, GeomVertexWriter, GeomVertexFormat, GeomVertexData
from panda3d.core import GeomTristrips, GeomLinestrips

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

###
#   Geometry creation
###

def makeGrid(rng = 1000, spacing = 10): #FIXME make this scale based on zoom???
    ctup = (.3,.3,.3,1)
    xs = range(-rng,rng+1,spacing)
    ys = xs

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    #fmt = GeomVertexFormat.getV3() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')


    for i,d in enumerate(xs):
        switch1 = (-1) ** i * rng
        switch2 = (-1) ** i * -rng
        #print(d,switch1,0)
        verts.addData3f(d, switch1, 0)
        verts.addData3f(d, switch2, 0)
        color.addData4f(*ctup)
        color.addData4f(*ctup)

    for i,d in enumerate(ys):
        switch1 = (-1) ** i * rng
        switch2 = (-1) ** i * -rng
        verts.addData3f(switch1, d, 0)
        verts.addData3f(switch2, d, 0)
        color.addData4f(*ctup)
        color.addData4f(*ctup)

    gridLines = GeomLinestrips(Geom.UHStatic)
    gridLines.addConsecutiveVertices(0, vertexData.getNumRows())
    gridLines.closePrimitive()

    grid = Geom(vertexData)
    grid.addPrimitive(gridLines)
    return grid

def makeAxis(): #FIXME make this scale based on zoom???
    colors = (
        (1,0,0,1),
        (0,1,0,1),
        (0,0,1,1),

        (1,0,0,1),
        (0,1,0,1),
        (0,0,1,1),
    )
    points = (
        (0,0,0),
        (0,0,0),
        (0,0,0),
        (1,0,0),
        (0,1,0),
        (0,0,1),
    )

    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    #fmt = GeomVertexFormat.getV3() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')


    for p,c in zip(points,colors):
        verts.addData3f(*p)
        color.addData4f(*c)

    axisX = GeomLinestrips(Geom.UHStatic)
    axisX.addVertices(0,3)
    axisX.closePrimitive()

    axisY = GeomLinestrips(Geom.UHStatic)
    axisY.addVertices(1,4)
    axisY.closePrimitive()

    axisZ = GeomLinestrips(Geom.UHStatic)
    axisZ.addVertices(2,5)
    axisZ.closePrimitive()

    axis = Geom(vertexData)
    axis.addPrimitive(axisX)
    axis.addPrimitive(axisY)
    axis.addPrimitive(axisZ)
    return axis


def makeCameraTarget():
    colors = (
        (0,0,1,1),
        (1,0,0,1),
        (0,1,0,1),
        (0,0,1,1),
        (1,0,0,1),
        (0,1,0,1),
    )
    points = (
        (0,0,1),
        (-1,0,0),
        (0,-1,0),
        (0,0,-1),
        (1,0,0),
        (0,1,0),
        (0,0,1),
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
    targetTris.addConsecutiveVertices(0,6)
    targetTris.addVertex(0)
    targetTris.addVertex(1)
    targetTris.addVertex(3)
    targetTris.addVertex(5)
    targetTris.addVertex(2)
    targetTris.addVertex(4)
    targetTris.addVertex(0)
    targetTris.closePrimitive()

    target = Geom(vertexData)
    target.addPrimitive(targetTris)
    return target

###
#   DirectObjects
###

class HasKeybinds:
    def __init__(self,keybinds):
        self.keybinds = keybinds

class Grid3d(DirectObject):
    def __init__(self):
        gridNode = GeomNode('grid')
        gridGeom = makeGrid()
        gridNode.addGeom(gridGeom)
        grid = render.attachNewNode(gridNode)

class Axis3d(DirectObject): #FIXME not the best way to do this, making all these new direct objects if they need to be controlled
    def __init__(self, scale=10):
        axisNode = GeomNode('axis')
        axisGeom = makeAxis()
        axisNode.addGeom(axisGeom)
        axis = render.attachNewNode(axisNode)
        axis.setScale(scale,scale,scale)
        axis.setRenderModeThickness(2)

class CameraControl(DirectObject):
    """ adds controls to a given camera, usually base.camera"""
    def __init__(self,camera=None):
        #camera setup
        self.camera = camera
        if self.camera == None:
            self.camera = base.camera

        #XXX note, when moving cam target we need to make sure the camera doesnt move too...
        cameraBase = GeomNode('cameraBase') #utility node for pan
        targetGeom = makeCameraTarget()
        cameraBase.addGeom(targetGeom)
        self.cameraBase = render.attachNewNode(cameraBase)
        #self.cameraBase.setTwoSided(True) #backface culling issue with my tristrip fail

        self.cameraTarget = NodePath('cameraTarget') #utility node for rot, zoom, reattach
        self.cameraTarget.reparentTo(self.cameraBase)
        #self.cameraTarget.reparentTo(render)
        self.camera.reparentTo(self.cameraTarget)

        #keybind setup
        self.__ends__=defaultdict(list)

        #self.accept("escape", sys.exit)  #no, exit_cleanup will handle this...

        for function,key in keybinds['view'].items():
            #self.accept(key,taskMgr.add,(getattr(self,function),function+'Task'))
            self.accept(key, self.makeTask, [function])
            keytest=key.split('-')[-1]
            #print(keytest)
            if keytest in {'mouse1','mouse2','mouse3'}:
                self.addEndTask(keytest,function)
                self.accept(keytest+'-up', self.endTask, [keytest,function])

        #gains #TODO tweak me!
        self.XGAIN = .01
        self.YGAIN = .01

        #window setup
        self.getWindowSize()
        self.accept('window-event', self.getWindowSize)
        


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
        self.__cth__=None
        self.__ctp__=None

        pass

    def getWindowSize(self,wat=None):
        self.__winx__ = base.win.getXSize()
        self.__winy__ = base.win.getYSize()
        #print(self.__winx__,self.__winy__)

    def makeTask(self, function):
        """ ye old task spawner """
        if base.mouseWatcherNode.hasMouse():
            x,y = base.mouseWatcherNode.getMouse()
            setattr(self, '__%sTask_s__'%function, (x,y)) #this should be faster
            taskMgr.add(getattr(self,function), function+'Task')

    def addEndTask(self,key,function):
        self.__ends__[key].append(function)

    def endTask(self, key, function):
        for func in self.__ends__[key]:
            taskMgr.remove(func+'Task')
            setattr(self, '__%sTask_s__'%func, None) #this should be faster
        self.__ch__=None #FIXME this seems hackish
        self.__cp__=None
        self.__cr__=None
        self.__cth__=None
        self.__ctp__=None

    def getMouseDdDt(self, name): #XXX deprecated
        """ use gain to adjust pixels per degree
            this should probably be normalized to screen size actually?
            or no... but to what?
        """
        if base.mouseWatcherNode.hasMouse():
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
        if base.mouseWatcherNode.hasMouse():
            x,y = base.mouseWatcherNode.getMouse()
            sx,sy = getattr(self,'__%s_s__'%(name))
            dx = (x - sx) * self.XGAIN * self.__winx__
            dy = (y - sy) * self.YGAIN * self.__winy__
            return dx, dy

    def getMouseCross(self,name): #FIXME may need to do this incrementally as we started with...
        if base.mouseWatcherNode.hasMouse():
            x,y = base.mouseWatcherNode.getMouse()
            sx,sy = getattr(self,'__%s_s__'%(name))

            dx = (x - sx) * self.XGAIN * self.__winx__
            dy = (y - sy) * self.YGAIN * self.__winy__
            norm = (dx**2 + dy**2)**.5
            cross = x * sy - y * sx

            return cross * norm

    def home(self, task):
        self.camera.lookAt(self.cameraBase)
        taskMgr.remove(task.getName())
        return task.cont

    def pan(self, task):
        """ I don't like it, it's weird! """
        if base.mouseWatcherNode.hasMouse():
            x,y = base.mouseWatcherNode.getMouse()
            sx,sy = getattr(self,'__%s_s__'%(task.getName()))
            dx = (x - sx) * self.XGAIN * self.__winx__ * 15
            dy = (y - sy) * self.YGAIN * self.__winy__ * 15
            #cx,cy,cz = self.camera.getPos()
            self.camera.setPos(self.camera,dx,0,dy)
            setattr(self, '__%s_s__'%task.getName(), (x,y)) #reset each frame to compensate for moving from own position
            #nx,ny,nz = self.camera.getPos()
            #dx2, dy2, dz2 = nx-cx, ny-cy, nz-cz
            #self.camera.setPos(cx,cz,cy)
            #self.cameraBase.setPos(self.cameraBase,dx2,dy2,dz2) #a hack to move cameraBase as if it were the camera
            #self.cameraTarget.setPos(self.cameraBase,dx2,dy2,dz2) #a hack to move cameraBase as if it were the camera
        return task.cont

    def zoom_in_slow(self, task, speed = 10):
        return self.zoom_in(task, speed) #hehe this will work because it just passes the task :)

    def zoom_out_slow(self, task, speed = 10):
        return self.zoom_out(task, speed)

    def zoom_in_fast(self, task, speed = 1000):
        return self.zoom_in(task, speed) #hehe this will work because it just passes the task :)

    def zoom_out_fast(self, task, speed = 1000):
        return self.zoom_out(task, speed)


    def zoom_in(self, task, speed = 100): #FIXME zoom_in and zoom_out still get custom xys even thought they don't use them!
        self.camera.setPos(self.camera,0,speed,0)
        taskMgr.remove(task.getName())
        return task.cont

    def zoom_out(self, task, speed = 100):
        self.camera.setPos(self.camera,0,-speed,0)
        taskMgr.remove(task.getName()) #we do it this way instead of addOnce because we want to add all the tasks in one go
        return task.cont

    def rotate(self, task): #FIXME disregard orientation acqurie proper mouse movements!
        dx,dy = self.getMouseDdDf(task.getName())
        if self.__cth__ == None:
            self.__cth__ = self.cameraTarget.getH()
        if self.__ctp__ == None:
            self.__ctp__ = self.cameraTarget.getP()
        self.cameraTarget.setH(self.__cth__ - dx * 10)
        self.cameraTarget.setP(self.__ctp__ + dy * 10)
        return task.cont

    #if we are in camera mode
    def pitch(self, task):
        dx,dy = self.getMouseDdDf(task.getName())
        print('got pitch',dy)
        return task.cont

    def look(self, task): #AKA heading in hpr
        dx,dy = self.getMouseDdDf(task.getName())
        if self.__ch__ == None:
            self.__ch__ = self.camera.getH()
        if self.__cp__ == None:
            self.__cp__ = self.camera.getP()
        self.camera.setH(self.__ch__ - dx)
        self.camera.setP(self.__cp__ + dy) #FIXME when we're clicking this might should be inverted?
        return task.cont

    def roll(self, task):
        """ ALWAYS roll with respect to axis of rotation"""
        if self.__cr__ == None:
            self.__cr__ = self.cameraTarget.getR()
        #cross product idiot
        cross = self.getMouseCross(task.getName())

        self.cameraTarget.setR(self.__cr__ - cross * 10 )
        return task.cont

###
#   Tests
###

def main():
    from direct.showbase.ShowBase import ShowBase
    base = ShowBase()
    base.disableMouse()
    base.setBackgroundColor(0,0,0)
    cc = CameraControl()
    ax = Axis3d()
    gd = Grid3d()
    run()

if __name__ == '__main__':
    main()

