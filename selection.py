from __future__ import print_function
#import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import TextNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Point2,Vec3,Vec4,BitMask32
from panda3d.core import BillboardEffect

from panda3d.core import LPoint2f, LPoint3f, LVector3f

from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay,CollisionLine

from numpy import pi, arange, argmin, sin, cos, tan, arctan2 #, arccos, arcsin, arctan2, arccos2, arcsin2

import sys
from threading import Thread
from .util.ipython import embed

from .defaults import *
from .util.util import genLabelText
from .test_objects import makeSimpleGeom
from .keys import event_callback, HasKeybinds
from .prof import profile_me

import inspect

RADIANS_PER_DEGREE = pi/180


def fixAsp(point):  # FIXME broken
    return render2d.getRelativePoint(aspect2d,point)
    #return aspect2d.getRelativePoint(render2d,point)  # no...

def norm(x, y):
    return (x**2 + y**2)**.5

def rescale(p2p, corner, radius, cfz):
    """ aspect ratio fix for radii >_< """
    dx = (corner[0] - p2p[0])
    dz = (corner[2] - p2p[2]) / cfz
    theta = arctan2(dz, dx)

    x = cos(theta) * radius
    z = sin(theta) * radius * cfz # multiplication here givs the actual distance the 3d projection covers in 2d
    return (x**2 + z**2)**.5  #


class HasSelectables(HasKeybinds): #mixin see chessboard example
    def __init__(self):
        #selection detection
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        #self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask()) #TODO WOW geometry collision is SUPER slow...
        self.pickerNode.setFromCollideMask(BitMask32.bit(BITMASK_COLL_CLICK))
        #render.find('**selectable').node().setIntoCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        #self.picker.showCollisions(render)

        #box selection detection HINT: start with drawing the 2d thing yo!

        self.__shift__ = False
        self.accept("shift", self.shiftOn)
        self.accept("shift-up", self.shiftOff)

        self.__ctrl__ = False
        self.accept("control", self.ctrlOn)
        self.accept("control-up", self.ctrlOff)

        #mouse handling
        self.accept("mouse1", self.clickHandler)
        self.accept("shift-mouse1", self.clickHandler)
        self.accept("mouse1-up", self.releaseHandler)

        #dragging
        self.dragTask = taskMgr.add(self.dragTask, 'dragTask')

    def getClickTarget(self,rootSelNode=None):
        """ traverse from the root of the selectable tree """
        #print('getting target....')
        if rootSelNode == None:
            rootSelNode = render

        if base.mouseWatcherNode.hasMouse():
            self.pickerRay.setFromLens(base.camNode, *base.mouseWatcherNode.getMouse())

            self.picker.traverse(rootSelNode)
            if self.pq.getNumEntries() > 0: #if we got something sort it
                self.pq.sortEntries()
                return self.pq.getEntry(0)



        #nearPoint = render.getRelativePoint(camera, self.pickerRay.getOrigin())
        #nearVec = render.getRelativeVector(camera, self.pickerRay.getDirection())
        #thingToDrag.obj.setPos(PointAtZ(.5, nearPoint, nearVec)) #not sure how this works

    def ctrlOn(self):
        self.__ctrl__ = True

    def ctrlOff(self):
        self.__ctrl__ = False

    def shiftOn(self):
        self.__shift__ = True

    def shiftOff(self):
        self.__shift__ = False

    @event_callback
    def clickHandler(self):
        pass

    @event_callback
    def releaseHandler(self):
        pass

    def dragTask(self, task):
        pass

    def clickSelectObject(self): #shif to multiselect... ?? to unselect invidiual??
        pass

    def dragSelectObjects(self): #always drag in the plane of the camera
        pass

def makeSelectRect():
    ctup = (1,1,1,1)
    fmt = GeomVertexFormat.getV3c4()
    vertexData = GeomVertexData('points', fmt, Geom.UHDynamic)

    points = ( #makes nice for Tristrips
        (0,0,0),
        (0,0,1),
        (1,0,0),
        (1,0,1),
    )

    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for point in points:
        verts.addData3f(*point)
        color.addData4f(*ctup)

    boxLines = GeomLinestrips(Geom.UHDynamic)
    boxLines.addVertices(0,1,3,2)
    boxLines.addVertex(0)
    boxLines.closePrimitive()

    boxTris = GeomTristrips(Geom.UHDynamic)
    boxTris.addConsecutiveVertices(0,3)
    boxTris.closePrimitive()

    box = Geom(vertexData)
    box.addPrimitive(boxLines)
    #box.addPrimitive(boxTris)

    return box
    
#use render 2d?

class BoxSel(HasSelectables,DirectObject):
    #visualization levels
    VIS_OFF = 0
    VIS_POINTS = 1
    VIS_CENTERS = 2
    VIS_ALL = 3
    VIS_DEBUG = 4
    def __init__(self, frames = None, visualize = VIS_POINTS):
        super().__init__()
        self.visualize = visualize

        self.uiRoot = render.find('uiRoot')
        self.projRoot = render2d.attachNewNode('projRoot')
        self.selRoot = render.attachNewNode('selRoot')
        self.collRoot = render.find('collideRoot')
        if not self.collRoot:
            raise ValueError('No collideRoot found, you need to initilizate the render manager first.')

        self.utilityNode = render.attachNewNode('utilityNode')

        self.bitmask_click = BitMask32.bit(BITMASK_COLL_CLICK)

        self.frames = frames
        if self.frames is None:
            self.frames = {}
            class f:
                items = {}
                def del_all(self):
                    pass
                def add_item(self, *args, **kwargs):
                    pass
                def getMaxItems(self):
                    pass
            self.frames['data'] = f()


        #setup the selection box
        boxNode = GeomNode('selectBox')
        boxNode.addGeom(makeSelectRect())
        self.__baseBox__ = render2d.attachNewNode(boxNode)
        self.__baseBox__.hide()

        self.selText = genLabelText('uuid',3)
        self.selText.reparentTo(base.a2dTopLeft)

        self.accept('mouse1',self.gotClick)  # TODO keybinds
        self.accept('shift-mouse1',self.gotClick)
        self.accept('mouse1-up',self.gotRelease)
        #self.accept('v', self.toggle_vis)
        #self.accept("escape", sys.exit)  #no, exit_cleanup does this

        self.curSelShown = []
        self.curSelPoints = []

    @event_callback('v')
    def toggle_vis(self):
        def do_show(node):
            #if node.getName().count('leaf'):  # apparently ALL parents must be visible?!
            node.show()
            for child in node.getChildren():
                if child.getNumChildren():
                    do_show(child)

        def do_hide(node):
            #if node.getName().count('leaf'):
            node.hide()
            for child in node.getChildren():
                if child.getNumChildren():
                    do_hide(child)


        self.visualize = (self.visualize + 1) % 5  # rotate through 5 levels
        if self.visualize == self.VIS_DEBUG:
            if self.collRoot.getNumDescendants() < 100000:
                #self.collRoot.showAllDescendants()
                do_show(self.collRoot)
        elif not self.visualize:
            if self.collRoot.getNumDescendants() < 100000:
                #self.collRoot.hideAllDescendants()
                do_hide(self.collRoot)

    def clearSelection(self):  # TODO enable saving selections to registers etc
        #taskMgr.remove('show_task')
        if self.curSelShown:
            self.curSelShown = []
            self.frames['data'].del_all()  # FIXME!
        self.clearHighlight()
        
    def clearHighlight(self):
        if self.curSelPoints:
            for point in self.curSelPoints:
                point.removeNode()
            self.curSelPoints = []
            #self.curSelNode.detachNode()
        #while 1:
            #try:
                #uuid = self.curSelShown.pop()
                #self.frames['data'].del_item(uuid)
                #obj = self.curSelNodes.pop()
                #obj.detachNode()
                #obj.reparentTo(self.invisRoot)
                #obj.remove()
            #except IndexError: #FIXME slow?
                #return None

    def processTarget(self, target):  # FIXME this is wrong, it needs to accomodate more child nodes
        #TODO shouldn't we let nodes set their own "callback" on click? so that there is a type per instead of shoving it all here?
            #well we also need to keep track of the previously selected set of nodes so we can turn them back off
        #note: target is a CollisionEntry
        #self.loadData(uid)
        #self.doRenderStuff() #this is the hard part...

        if taskMgr.hasTaskNamed('boxTask'):  # FIXME this seems a nasty way to control this...
            intoNode = target
            uuid = intoNode.getTag('uuid')  # FIXME it would see that this are not actually uuids...
        else:
            if not self.__shift__ and self.curSelShown:
                self.clearSelection()
            intoNode = target.getIntoNode()
            uuid = intoNode.getTag('uuid')
            self.frames['data'].add_item(uuid, command=self.highlight, args=(uuid, intoNode, True) )
            self.highlight(uuid, intoNode, False)

        #self.selText.setText("%s"%uuid)

        self.curSelShown.append(intoNode)

        return None

    @event_callback
    def gotClick(self):  # TODO rename this to inherit from HasSelectables
        target = self.getClickTarget()
        if target:
            self.processTarget(target)
            try:
                print([n for n in target.getIntoNodePath().getAncestors() if n.getName().count('ObjectRoot')])
                root = [n for n in target.getIntoNodePath().getAncestors() if n.getName().count('ObjectRoot')][-1]  # FIXME global naming please
                cbs = root.getPythonTag('selection_callbacks')
                if cbs:
                    [f() for f in cbs]
                print(root, 'got a hit')
            except IndexError:
                print('anger')
            # switch that to selection for object level manipulation
        else:
            if not self.__shift__:
                self.clearSelection()

            if base.mouseWatcherNode.hasMouse():
                x,y = base.mouseWatcherNode.getMouse()
                self.__baseBox__.setPos(x,0,y)
                self.__baseBox__.setScale(0) #setSx setSy
                self.__baseBox__.show()
                taskMgr.add(self.boxTask, 'boxTask')

    def getClickTarget(self):
        """ See if we were clicking ON an object """
        #this will use the ray tracing hit detection
        #so no need for x and y

        #TODO the magic here will be that we will move the individual geom
        #by creating a new node that copies it for the drag and then reinsert at the new position
        #when we release
        
        #this may take a bit more finagling ie: we may need to create a collision sphere around every vertex
        return super(BoxSel,self).getClickTarget() #TODO damn it python 2

    @event_callback
    def gotRelease(self):
        #self.__mouseDown__ = False
        if taskMgr.hasTaskNamed('boxTask'):
            if self.visualize <= self.VIS_POINTS:
                self.__baseBox__.hide()
            #if abs(self.__baseBox__.getScale()[0]) > .005:
            if abs(self.__baseBox__.getScale()[0]) > .0001:
                #if self.visualize > 1:
                    #self.getEnclosedNodes_viz()
                #else:
                self.getEnclosedNodes()
            taskMgr.remove('boxTask')

    def boxTask(self, task): #this will only be active if mouse down and not click
        x,y = base.mouseWatcherNode.getMouse()
        cx,cy,cz = self.__baseBox__.getPos()
        self.__baseBox__.setSx(x-cx)
        #self.__baseBox__.setSy(y-cy)
        self.__baseBox__.setSz(y-cz) #so it turns out that 'z' is what we want???
        #embed()
        return task.cont

    #@profile_me
    def getEnclosedNodes(self):  # FIXME, get a list of every object behind a pixel...
        cfx = 1
        cfz = base.camLens.getAspectRatio()
        cx, _, cz = self.__baseBox__.getPos()
        sx, _, sz = self.__baseBox__.getScale()  # gives us L/W of the box
        self.selRoot.removeChildren()
        self.projRoot.removeChildren()

        x2 = cx + sx
        if cx > x2:
            uX = cx
            lX = x2
        else:
            uX = x2
            lX = cx

        z2 = cz + sz
        if cz > z2:
            uZ = cz
            lZ = z2
        else:
            uZ = z2
            lZ = cz

        lensFL = base.camLens.getFocalLength()
        fov = max(base.camLens.getFov()) * RADIANS_PER_DEGREE

        if self.visualize:
            points3 = []
            if self.visualize >= self.VIS_CENTERS:
                points = []


        p2 = Point2()  # allocating this once saves us about 110ms
        white = (1,1,1,1)
        def projectNode(node):  # FIXME this is where some serious time cost exists
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)

            if not base.camLens.project(p3,p2):
                return False

            pX = p2[0]
            pZ = p2[1]
            # check if the points are inside the box
            if lX <= pX and pX <= uX:
                if lZ <= pZ and pZ <= uZ: 
                    self.processTarget(node)
                    # TODO it would be faster to change the color of all the vertexes of
                    # the selected nodes when we're working with a single points geom
                    # but that requires a function to do the mapping from nodes -> verts
                    # TODO we need a way to tell the ObjectRoot collNode a child actually got a hit
                    if self.visualize:
                        points3.append(point3d)
                        if self.visualize >= self.VIS_CENTERS:
                            points.append([pX, 0, pZ])
                    return True

        if self.visualize >= self.VIS_CENTERS:
            l2points = []
            l2all = []

        # things we don't need to do every bloody time
        #utilityNode = render.attachNewNode('utilityNode')
        track = camera.find('track')
        track_pos = render.getRelativePoint(track, track.getPos())
        cam_pos = render.getRelativePoint(camera, camera.getPos())
        camVec = track_pos - cam_pos
        radius_correction = 2  #no idea if this is correct...
        #p2 = Point2()  # already allocated above
        def projectL2(node, contained = False):  # FIXME so it turns out that if our aspect ratio is perfectly square everything works
            """ projec only the centers of l2 spehres, figure out how to get their radii """

            if contained:
                test = True
            else:
                point3d = node.getBounds().getApproxCenter()
                p3 = camera.getRelativePoint(render, point3d)
                base.camLens.project(p3,p2)
                point2projection = Point3(p2[0],0,p2[1])

                r3 = node.getBounds().getRadius()  # this seems to be correct despite node.show() looking wrong in some cases
                self.utilityNode.setPos(point3d)  # FIXME I'm sure this is slower than just subtract and norm... but who knows
                # this also works correctly with no apparent issues
                d1 = camera.getDistance(self.utilityNode)  # FIXME make sure we get the correct camera
                if not d1:
                    d1 = 1E-9

                pointVect = point3d - cam_pos

                pos_theta = abs(camVec.relativeAngleRad(pointVect))

                #naieve approach with similar triangles, only seems to give the correct distance when d1 is very close to zero (wat)
                eccen_corr = pos_theta
                eccen_corr = 1
                # XXX the magic happens here
                projNodeRadius = (r3 * lensFL) / d1 * radius_correction * eccen_corr # % fov)  # need to compensate for distance effect on theta


                test = tests(d1, r3, projNodeRadius, point2projection, lX, uX, lZ, uZ, cfz)
                if test == -1:
                    contained = True


                if self.visualize >= self.VIS_CENTERS:
                    # centers of all l2 points
                    if test:
                        l2points.append(point3d)
                        color = [0,1,0,1]
                    else:
                        l2all.append(point3d)
                        color = [0,0,1,1]
                    # visualize the projected radius of l2 collision spheres
                    if self.visualize >= self.VIS_ALL:
                        radU = [point2projection+(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius*cfz)) for theta in arange(0,pi*2.126,pi/32)]
                        self.projRoot.attachNewNode(makeSimpleGeom(radU,color,GeomLinestrips))

            hit = None
            if test:
                for c in node.getChildren():
                    #if c.getNumChildren():
                    if c.getCollideMask() == self.bitmask_click:
                        if projectNode(c):
                            hit = True
                    else:
                        if projectL2(c, contained):  # next level and check hit
                            hit = True


                #if not contained:
                if 0:
                    if self.visualize >= self.VIS_CENTERS:
                        l2points.append(point3d)
                        if self.visualize >= self.VIS_ALL:
                            radU = [point2projection+(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius*cfz)) for theta in arange(0,pi*2.126,pi/32)]
                            n = self.projRoot.attachNewNode(makeSimpleGeom(radU,[0,1,0,1],GeomLinestrips))
                            n.setBin('unsorted',0)
            return hit

        def tests(d1, r3, radius, p2p, lX, uX, lZ, uZ, cfz):
            """ see if boxes and circles overlap """
            if d1 < r3:
                #print('Inside the sphere')
                return True

            pX, _, pZ = p2p

            if lX <= pX - radius and pX + radius <= uX and lZ <= pZ - radius and pZ + radius <= uZ:
                #print("circle in box")
                return -1

            Xin = lX <= pX and pX <= uX
            Zin = lZ <= pZ and pZ <= uZ

            if Xin and Zin:
                #print("Xin and Zin")
                return True

            #if Xin:
                #print('Xin')
            #elif Zin:
                #print('Zin')

            corners = (
                Point3(lX, 0, lZ),
                Point3(lX, 0, uZ),
                Point3(uX, 0, lZ),
                Point3(uX, 0, uZ),
            )

            for c in corners:
                if (c - p2p).length() < rescale(p2p, c, radius, cfz):
                    if self.visualize >= self.VIS_ALL:
                        line = (c, (pX, 0, pZ))
                        self.projRoot.attachNewNode(makeSimpleGeom(line,[0,1,0,1],GeomLinestrips))
                    #print("min of norms")
                    return True

            dxl = pX - lX
            dxu = pX - uX
            dzl = pZ - lZ
            dzu = pZ - uZ
            min_dxs = min(abs(dxl), abs(dxu))
            min_dzs = min(abs(dzl), abs(dzu))

            #if min_dxs <= radius:
                #print('min dxs passed')
            #if min_dzs <= radius * cfz:
                #print('min dzs passed')

            if min_dxs <= radius and Zin:
                #print('dx < r and Zin')
                return True
            elif min_dzs <= radius * cfz and Xin:
                #print('dz < r and Xin')
                return True
            else:
                #print('fail')
                return False

        # actually do the projection
        for c in self.collRoot.getChildren():  # FIXME this is linear doesnt use the pseudo oct tree
            if c.getName().count('ObjectRoot for'):
                print('yes we normal')
                if projectL2(c):  # check if we got a hit
                    cbs = c.getPythonTag('selection_callbacks')
                    if cbs:
                        [f() for f in cbs]

            elif c.getName().count('ObjectRoot'): # FIXME starts with
                for c_ in c.getChildren():
                    if projectL2(c_):  # check if we got a hit
                        print('yes we here')
                        print(c_)
                        cbs = c_.getPythonTag('selection_callbacks')
                        if cbs:
                            [f() for f in cbs]
            else:
                print(c.getName())


        print(len(self.curSelShown))
        #someday we thread this ;_;
        if self.visualize:
            pts3 = makeSimpleGeom(points3, [1,1,1,1])
            p3n = self.selRoot.attachNewNode(pts3)
            p3n.setRenderModeThickness(3)  # render order >_<

            if self.visualize >= self.VIS_CENTERS:
                l2s = makeSimpleGeom(l2points,[0,1,0,1])
                l2n = self.selRoot.attachNewNode(l2s)
                l2n.setRenderModeThickness(8)

                l2as = makeSimpleGeom(l2all,[1,0,0,1])
                l2an = self.selRoot.attachNewNode(l2as)
                l2an.setRenderModeThickness(8)

                if self.visualize >= self.VIS_DEBUG:
                    pts = makeSimpleGeom(points,[1,1,1,1])
                    self.projRoot.attachNewNode(pts)


        # set up the task to add entries to the data frame TODO own function?
        stop = len(self.frames['data'].items) - 1
        for into in self.curSelShown[:stop]:
            uuid = into.getTag('uuid')
            self.frames['data'].add_item(uuid, command=self.highlight, args=(uuid, into, True) )
        #self.show_stop = len(self.curSelShown[:stop])
        #self.show_count = 0
        #if self.show_stop:
            #taskMgr.add(self.show_task, 'show_task')

    def show_task(self, task):
        if self.show_count >= self.show_stop:
            taskMgr.remove(task.getName())
        else:  # adding buttons is pretty slow :/ TODO try to make these in the background?
            into = self.curSelShown[self.show_count]
            uuid = into.getTag('uuid')
            self.frames['data'].add_item(uuid, command=self.highlight, args=(uuid, into, True) )
            self.show_count += 1
        return task.cont
    
    def highlight(self, uuid, intoNode, clear, *args):
        if clear:
            self.clearHighlight()
        pos = intoNode.getBounds().getApproxCenter()

        point = makePoint(pos)
        p = self.uiRoot.attachNewNode(point)
        p.setRenderModeThickness(3)
        self.curSelPoints.append(p)

        textNode = p.attachNewNode(TextNode("%s_text"%uuid))
        textNode.setPos(*pos)
        textNode.node().setText("%s"%uuid)
        textNode.node().setEffect(BillboardEffect.makePointEye())


def makePoint(point=(0,0,0)):
    clr4 = [1,1,1,1]
    fmt = GeomVertexFormat.getV3c4() #3 component vertex, w/ 4 comp color
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)
    verts = GeomVertexWriter(vertexData, 'vertex')
    verts.addData3f(*point)
    color = GeomVertexWriter(vertexData, 'color')
    color.addData4f(*clr4)
    pointCloud = GeomPoints(Geom.UHStatic)
    pointCloud.addVertex(0)
    pointCloud.closePrimitive()
    cloud = Geom(vertexData)
    cloud.addPrimitive(pointCloud)
    cloudNode = GeomNode('point')
    cloudNode.addGeom(cloud)
    return cloudNode



def main():
    import pickle
    from .util.util import ui_text, console, exit_cleanup, frame_rate, startup_data
    from .keys import AcceptKeys
    from .render_manager import renderManager
    from .ui import CameraControl, Axis3d, Grid3d
    base = ShowBase()
    base.setBackgroundColor(0,0,0)
    base.disableMouse()
    startup_data()
    console()
    exit_cleanup()
    frame_rate()
    CameraControl()
    Axis3d()
    Grid3d()

    r = renderManager()

    from .test_objects import makeSimpleGeom
    import numpy as np
    from .trees import treeMe
    from uuid import uuid4
    from panda3d.core import GeomLinestrips
    n = 1000
    #positions = np.array([i for i in zip(np.linspace(-1000,1000,n),np.linspace(-1000,1000,n),np.linspace(-1000,1000,n))]) # wat 1
    #positions = np.array([i for i in zip(np.linspace(-1000,1000,n),np.linspace(-1000,1000,n),np.zeros(n))]) # wat 2
    positions = np.array([i for i in zip(np.linspace(-1000,1000,n),np.zeros(n),np.zeros(n))])
    #positions = np.random.randint(-1000,1000,(n,3))
    # so it turns out that the collision nodes don't render properly on this, the tree constructed with math is correct, the rendering is not
    r.geomRoot.attachNewNode(makeSimpleGeom(positions,(1,1,1,1)))
    uuids = np.array(['%s'%uuid4() for _ in range(n)])
    bounds = np.ones(n) * .5
    treeMe(r.collRoot, positions, uuids, bounds)

    base.camLens.setFov(90)

    n = 1E4  # apparently 1e8 is a bit too big and 1e7 is slowwww... definitely need downsampling
    positions = np.array([i for i in zip(10*np.sin(np.arange(0,n)),np.arange(0,n),10*np.cos(np.arange(0,n)))]) # fukken saved
    r.geomRoot.attachNewNode(makeSimpleGeom(positions,(1,1,1,1), geomType=GeomLinestrips))

    #with open('edge_case_data_tuple.pickle','rb') as f:
        #data_tuple = pickle.load(f)
    #r.cache['edgecase'] = False
    #r.set_nodes('edgecase',data_tuple)

    sgn = GeomNode('srct')
    sgn.addGeom(makeSelectRect())
    sn = render.attachNewNode(sgn)
    sn.setSx(10)
    sn.setSy(10)
    sn.setColor(.5,.5,.5,.5)

    ut = ui_text()
    dt = BoxSel(visualize = BoxSel.VIS_ALL)
    ac = AcceptKeys()
    base.run()

if __name__ == '__main__':
    main()
