import sys

from collections import defaultdict

from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath, GeomNode
from panda3d.core import Geom, GeomVertexWriter, GeomVertexFormat, GeomVertexData
from panda3d.core import GeomTristrips, GeomLinestrips

from IPython import embed

from monitor import getMaxPixelsPerMM

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

        for function_name, key in keybinds['view'].items():
            #self.accept(key,taskMgr.add,(getattr(self,function),function+'Task'))
            self.accept(key, self.makeTask, [function_name])  # TODO split out functions that don't require tasks
            keytest=key.split('-')[-1]
            #print(keytest)
            if keytest in {'mouse1','mouse2','mouse3'}:
                self.addEndTask(keytest,function_name)
                self.accept(keytest+'-up', self.endTask, [keytest,function_name])

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

    def makeTask(self, function_name):
        """ ye old task spawner """
        if hasattr(self, function_name):
            if base.mouseWatcherNode.hasMouse():
                x,y = base.mouseWatcherNode.getMouse()
                setattr(self, '__%sTask_s__'%function_name, (x,y)) #this should be faster
                taskMgr.add(getattr(self,function_name), function_name+'Task')
        else:
            raise KeyError('Check your keybinds, there is no function by that name here!')

    def addEndTask(self,key,function_name):
        self.__ends__[key].append(function_name)

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
#   Menus and frames
###

from direct.gui.DirectGui import DirectButton, DirectFrame, DGG, OnscreenText
from panda3d.core import TextNode, LineSegs, Point3, Point2

class GuiType(DirectObject):
    #DEFAULTS
    POSITION = (0, 0)
    color = (.5, .5, .5, 1)
    color_hover = (.5, .5, .5, 1)
    color_press = (.5, .5, .5, 1)
    def __init__(self, parent = None, position = None, color = None):
        if parent is None:
            self.parent = self
        else:
            self.parent = parent

        if position is None:
            self.position = self.POSITION
        else:
            self.position = position

        if color is None:
            self.color = self.parent.color
        else:
            self.color = color


class GuiLineType(GuiType):
    #DEFAULTS
    THICKNESS = 1
    def __init__(self, parent = None, position = None, color = None, thickness = None):
        super().__init__(parent, position, color)
        if thickness is None:
            self.thickness = THICKNESS
        else:
            self.thickness = thickness


class GuiLine(GuiLineType):
    #DEFAULTS
    LENGTH = 1
    def __init__(self, parent = None, position = None, color = None, thickness = None, length = None,):
        super().__init__(parent, position, color, thickness)
        self.length = length


class GuiAreaType(GuiType):
    #DEFAULTS
    WIDTH = 1
    HEIGHT = 1
    def __init__(parent = None, position = None, color = None, width = None, height = None):
        super().__init__(self, parent, position, color)
        self.width = width
        self.height = height


class GuiBorder(GuiLineType, GuiAreaType):
    def __init__(self, parent = None, position = None, color = None, thickness = None, width = None, height = None):
        super(GuiLineType, self).__init__(parent, position, color, thickness)
        super(GuiAreaType, self).__init__(parent, position, color, width, height)





class GuiFrame(DirectObject):
    #should be able to show/hide, do conditional show hide
    #position where you want
    #parent to other frames
    #there should be a -list- tree of frames
    def __init__(self, title,
                 shortcut = None,
                 x = 0,
                 y = .5,
                 width = .25,
                 height = .25,
                 #scale = .05,  # there is some black magic here :/
                 bdr_thickness = 2,
                 bdr_color = (.1, .1, .1, 1),
                 bg_color = (.7, .7, .7, .5),
                 text_color = (0, 0, 0, 1),
                 text_font = TextNode.getDefaultFont(),
                 text_height_mm = 3,
                 items = ((None,None,(None,)),),
                ):
    #item_w_pad = 1
    #item_h_pad = 1

        self.title = title
        self.do_xywh(x, y, width, height)
        #self.scale = scale
        self.bdr_thickness = bdr_thickness  # FIXME ??
        self.bdr_color = bdr_color
        self.bg_color = bg_color
        self.text_color = text_color
        self.text_font = text_font
        text_h = .25
        self.text_h = text_h
        self.text_s = text_h * 1.6666667
        #self.text_sx = self.text_sy

        #self.BT = buttonThrower if buttonThrower else base.buttonThrowers[0].node()
        self.BT = base.buttonThrowers[0].node()

        # get our aspect ratio, and pixels per mm
        self.getWindowData()
        self.accept('window-event', self.getWindowData)
        self.ppmm = getMaxPixelsPerMM()  # FIXME this does not need to be called every time...

        # get the root for all frames in the scene
        frameRoot = aspect2d.find('frameRoot')
        if not frameRoot:
            frameRoot = aspect2d.attachNewNode('frameRoot')

        # create the parent node for this frame
        self.frame = frameRoot.attachNewNode('frame-%s-%s'%(title, id(self)))

        # background
        l,r,b,t = 0, self.width, 0, self.height
        self.frame_bg = DirectFrame(parent=self.frame,
                                    frameColor=self.bg_color,
                                    pos=(self.x, 0, self.y),
                                    frameSize=(l,r,b,t),
                                    state=DGG.NORMAL,  # FIXME framesize is >_<
                                    suppressMouse=1)

        # border
        self.__make_border__(self.frame_bg, self.bdr_thickness, self.bdr_color, l, r, b, t)

        # setup for items
        self.itemsParent = self.frame_bg.attachNewNode('frame items')
        self.num_items = 0

        # title
        self.title_button = self.__add_item__(title, self.title_toggle_vis)
        
        # add any items that we got
        for item in items:
            self.__add_item__(*item)

        # dragging
        self.frame_bg.bind(DGG.B1PRESS, self.__startDrag)
        self.frame_bg.bind(DGG.B1RELEASE, self.__stopDrag)

        # toggle vis
        if shortcut:
            self.accept(shortcut, self.toggle_vis)

    def do_xywh(self, x, y, w, h):
        """ makes negative wneg xidths and heights work
            as well as negative x and y (bottom right is 0)
        """
        if x < 0:
            x = 1 + x
        if y < 0:
            y = 1 + y
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h

        self.x = self.fix_x(x)  # for top left
        self.y = self.fix_y(y)  # for top left
        self.width = self.fix_w(w)
        self.height = self.fix_h(h)

    def getWindowData(self, event=None):
        self.__ar__ = base.camLens.getAspectRatio()  # this gives the width / height ratio
        self.__winx__ = base.win.getXSize()
        self.__winy__ = base.win.getYSize()
        self.frame_adjust()

    def frame_adjust(self):
        #we are using aspect2d...
        pass
        
    def getWindowSize(self, event=None):  # TODO see if we really need this
        self.__winx__ = base.win.getXSize()
        self.__winy__ = base.win.getYSize()
        m = max(self.__winx__, self.__winy__)
        self.__xscale__ = self.__winx__ / m
        self.__yscale__ = self.__winy__ / m


    # put origin in top left and positive down and right
    @staticmethod
    def fix_x(x):
        return (x - .5) * 2
    @staticmethod
    def fix_y(y):
        return (y - .5) * -2
    @staticmethod
    def fix_w(n):
        return n * 2
    @staticmethod
    def fix_h(n):
        return -n * 2

    def __add_item__(self, text, command = None, args = (None,)): 
        self.num_items += 1
        b = DirectButton(
            parent=self.itemsParent,
            frameColor=(1,1,1,.5),
            frameSize=(0, self.width, 0, self.text_h),
            text=text,
            text_font=self.text_font,
            text_fg=self.text_color,
            text_scale=self.text_s, #, self.text_s),
            text_pos=(0, self.text_h - .8 * self.text_s),
            #text_pos=(0, -self.text_sy*self.num_items),
            #pos=(self.x, 0, self.y),
            command=command,
            extraArgs=args,
            relief=DGG.FLAT,
            #text_align=TextNode.ABoxedLeft,
            text_align=TextNode.ALeft,
        )
        #fr = b.node().getFrame()
        #height = fr[2]-fr[3]  # this is bottom - top so the value is already flipped
        #width = fr[1]-fr[0]  # right - left always positive
        b.setPos(0, 0, -self.text_h * self.num_items)
        return b

    def __del_item__(self):
        """ I have no idea how this is going to work """
        self.num_items -= 1

    @staticmethod
    def __make_border__(parent, thickness, color, l, r , b, t):
        moveto_drawto = (
           ((l,0,t), (l,0,b)),
           ((r,0,t), (r,0,b)),
           ((l,0,b), (r,0,b)),
           ((l,0,t), (r,0,t)),
        )
        for moveto, drawto in moveto_drawto:
            Border = LineSegs()
            Border.setThickness(thickness)
            Border.setColor(*color)
            Border.moveTo(*moveto)
            Border.drawTo(*drawto)
            parent.attachNewNode(Border.create())

    def toggle_vis(self):
        if self.frame_bg.isHidden():
            self.frame_bg.show()
        else:
            self.frame_bg.hide()


    def title_toggle_vis(self, wat = None):
        self.toggle_vis()
        if self.frame_bg.isHidden():
            self.title_button.wrtReparentTo(self.frame)
            self.title_button.show()
        else:
            self.title_button.wrtReparentTo(self.frame_bg)



    def __startDrag(self,crap):
        self._ox, self._oy = base.mouseWatcherNode.getMouse()
        taskMgr.add(self.__drag,'dragging %s'%self.title)
        self.origBTprefix=self.BT.getPrefix()
        self.BT.setPrefix('dragging frame')

    def __drag(self, task):
        if base.mouseWatcherNode.hasMouse():
            x, y = base.mouseWatcherNode.getMouse()
            if x != self._ox or y != self._oy:
                m_old = aspect2d.getRelativePoint(render2d, Point3(self._ox, self._oy, 0))
                m_new = aspect2d.getRelativePoint(render2d, Point3(x, y, 0))
                dx, dy, _ = m_new - m_old
                self.setPos(self.x + dx, self.y + dy)
                self._ox = x
                self._oy = y
        return task.cont

    def __stopDrag(self,crap):
        taskMgr.remove('dragging %s'%self.title)
        self.BT.setPrefix(self.origBTprefix)

    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.frame_bg.setPos(x, 0, y)


    def __enter__(self):
        #load the position
        #load other saved state
        pass

    def __exit__(self):
        #save the position!
        #save other state
        pass



# lits of frames
# selected objects
# selected object properties
# selected object types
# selected object relations

# relation types to view
# filters


class SelectProperties(GuiFrame):
    pass



###
#   Tests
###

def main():
    from direct.showbase.ShowBase import ShowBase
    from util import exit_cleanup, ui_text, console
    base = ShowBase()
    base.disableMouse()
    base.setBackgroundColor(0,0,0)
    ec = exit_cleanup()
    uit = ui_text()
    con = console()
    cc = CameraControl()
    ax = Axis3d()
    gd = Grid3d()

    items = [('testing',) for _ in range(10)]
    frames = [
        GuiFrame('MegaTyj', x=-.5, y=.5, height=.25, width=-.25),
        GuiFrame('MegaTyj', x=-.5, y=.5, height=.25, width=-.25),
        #GuiFrame('testing', x=0, y=0, height=.25, width=.25, items = items),
        #GuiFrame('cookies', x=1, y=1, height=-.25, width=-.25, items = items),
        #GuiFrame('neg x', x=-.25, y=0, height=.1, width=-.25, items = items),
        #GuiFrame('text', x=.5, y=.5, height=.25, width=-.25, items = items),
        #GuiFrame('text', x=.5, y=.5, height=-.25, width=-.25, items = items),
        #GuiFrame('text', x=.5, y=.25, height=.25, width=.25, items = items),
    ]
    # FIXME calling __add_item__ after this causes weird behvaior

    run()

if __name__ == '__main__':
    main()

