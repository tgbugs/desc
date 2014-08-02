from __future__ import print_function
#import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import PandaNode,NodePath
from panda3d.core import TextNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Point2,Vec3,Vec4,BitMask32
from panda3d.core import BillboardEffect

#from panda3d.core import AmbientLight

from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay,CollisionLine

from numpy import pi, arange, sin, cos, tan, arctan2 #, arccos, arcsin, arctan2, arccos2, arcsin2

import sys
from math import copysign
from threading import Thread
from IPython import embed

from defaults import *
from util import genLabelText
from test_objects import makeSimpleGeom


RADIANS_PER_DEGREE = pi/180

def fixAsp(point):  # FIXME broken
    return render2d.getRelativePoint(aspect2d,point)
    #return aspect2d.getRelativePoint(render2d,point)  # no...

class HasSelectables: #mixin see chessboard example
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

    def clickHandler(self):
        pass

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
    VIS_L2 = 2
    VIS_ALL = 3
    VIS_DEBUG = 4
    VIS_DEBUG_LINES = 5
    def __init__(self, frames = None, visualize = VIS_POINTS):
        super().__init__()
        self.visualize = visualize

        self.uiRoot = render.find('uiRoot')
        self.projRoot = render2d.attachNewNode('projRoot')
        self.selRoot = render.attachNewNode('selRoot')
        self.collRoot = render.find('collideRoot')

        self.frames = frames
        if self.frames is None:
            self.frames = {}
            class f:
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
        self.accept('v', self.toggle_vis)
        #self.accept("escape", sys.exit)  #no, exit_cleanup does this

        self.curSelShown = []
        self.curSelPoints = []

    def toggle_vis(self):
        self.visualize = (self.visualize + 1) % 6  # rotate through 4 levels
        if self.visualize == self.VIS_DEBUG:
            for child in self.collRoot.getChildren():
                child.show()
        elif not self.visualize:
            for child in self.collRoot.getChildren():
                child.hide()



    def clearSelection(self):  # TODO enable saving selections to registers etc
        taskMgr.remove('show_task')
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
            uuid = intoNode.getPythonTag('uuid')  # FIXME it would see that this are not actually uuids...
        else:
            if not self.__shift__ and self.curSelPoints:
                self.clearSelection()
            intoNode = target.getIntoNode()
            uuid = intoNode.getPythonTag('uuid')
            self.frames['data'].add_item(uuid, command=self.highlight, args=(uuid, intoNode, True) )
            self.highlight(uuid, intoNode, False)

        #self.selText.setText("%s"%uuid)

        self.curSelShown.append(intoNode)

        return None

    def gotClick(self):  # TODO rename this to inherit from HasSelectables
        target = self.getClickTarget()
        if target:
            self.processTarget(target)
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

    def gotRelease(self):
        #self.__mouseDown__ = False
        if taskMgr.hasTaskNamed('boxTask'):
            if self.visualize <= self.VIS_POINTS:
                self.__baseBox__.hide()
            #if abs(self.__baseBox__.getScale()[0]) > .005:
            if abs(self.__baseBox__.getScale()[0]) > .0001:
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

    def getEnclosedNodes(self):
        #cfx, cfz = base.camLens.getFilmSize()  # FIXME need this for a bunch of corrections
        cfx = 1
        cfz = base.camLens.getAspectRatio()
        cx,cy,cz = self.__baseBox__.getPos()
        sx,sy,sz = self.__baseBox__.getScale()  # gives us L/W of the box
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

        #boxRadius = ( (sx * .5)**2 + (sz * .5)**2 ) ** .5  # TODO we could make it so that every 2x change in raidus used 2 circles instead of 1 to prevent overshoot we can't just divide the radius by 2 though :/
        #boxCenter = Point3(cx + (sx * .5), 0, cz + (sz * .5))  # profile vs just using the points we get out

        def calcSelectionBoxRC(major, minor):
            if not minor:
                return 0, [0]
            ratio = abs(major / minor)
            if ratio > 5:  # prevent combinatorial nightmares TODO tune me!
                ratio = 5
            elif ratio < 1.5:
                ratio = 1
            else:
                ratio = int(ratio)

            split = major / ratio
            radius = ((split * .5)**2 + (minor * .5)**2)**.5
            majCents = [(split * .5) + i*(split) for i in range(ratio)]
            return radius, majCents

        if abs(sx) > abs(sz):
            boxRadius, majCents = calcSelectionBoxRC(sx, sz)
            centers = [Point3(cx + c, 0, cz + (sz * .5)) for c in majCents]
        else:
        #elif asz >= asx:
            boxRadius, majCents = calcSelectionBoxRC(sz, sx)
            centers = [Point3(cx + (sx * .5), 0, cz + c) for c in majCents]

        lensFL = base.camLens.getFocalLength()
        fov = max(base.camLens.getFov()) * RADIANS_PER_DEGREE
        #print("focal length",lensFL)
        #print("fov", base.camLens.getFov())

        if self.visualize:
            points3 = []
            if self.visualize >= self.VIS_ALL:
                points = []
        def projectNode(node):
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)
            p2 = Point2()

            if not base.camLens.project(p3,p2):
                return False

            pX = p2[0]
            pZ = p2[1]
            # check if the points are inside the box
            if lX <= pX and pX <= uX:
                if lZ <= pZ and pZ <= uZ: 
                    self.processTarget(node)
                    if self.visualize:
                        points3.append(point3d)
                        if self.visualize >= self.VIS_ALL:
                            points.append([pX, 0, pZ])

        if self.visualize >= self.VIS_L2:
            l2points = []
            if self.visualize >= self.VIS_ALL:
                l2all = []
        utilityNode = render.attachNewNode('utilityNode')
        def projectL2(node):  # FIXME so it turns out that if our aspect ratio is perfectly square everything works
            """ projec only the centers of l2 spehres, figure out how to get their radii """
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)
            p2 = Point2()

            base.camLens.project(p3,p2)

            point2projection = Point3(p2[0],0,p2[1])

            r3 = node.getBounds().getRadius()  # this seems to be correct despite node.show() looking wrong in some cases
            utilityNode.setPos(point3d)  # FIXME I'm sure this is slower than just subtract and norm... but who knows
            # this also works correctly with no apparent issues
            d1 = camera.getDistance(utilityNode)  # FIXME make sure we get the correct camera
            if not d1:
                d1 = 1E-9
            #fovMaxCorr = fov**2 * .5 #tan(fov * .5) #fov**2 * .25 #(fov*.9 - 1)
            #fovCorr = point2projection.length() * fovMaxCorr - point2projection.length() + 1  # FIXME this fails hard at high fov derp and for low fov
            fovCorr = 1
            
            # XXX the magic happens here
            #projNodeRadius = r3 * ((lensFL*1.7)/d1) * fovCorr  # FIXME for some reason 1.7 seems about right
            #projNodeRadius = r3 * ((lensFL*2)/d1) * fovCorr

            #naieve approach with similar triangles, only seems to give the correct distance when d1 is very close to zero (wat)
            radius_correction = 2  #no idea if this is correct...
            projNodeRadius = (r3 * lensFL) / d1 * radius_correction

            if self.visualize >= self.VIS_ALL:
                # centers of all l2 points
                l2all.append(point3d)

                # visualize the projected radius of l2 collision spheres
                radU = [point2projection+(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius*cfz)) for theta in arange(0,pi*2.126,pi/32)]
                self.projRoot.attachNewNode(makeSimpleGeom(radU,[0,0,1,1],GeomLinestrips))

                # smaller radisu radU...?
                #rads = [point2projection+fixAsp(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius)) for theta in arange(0,pi*2.126,pi/32)]
                #self.projRoot.attachNewNode(makeSimpleGeom(rads,[0,1,1,1],GeomLinestrips))

                # lower rez radU (same radisu)
                #rads = [Point3(p2[0]+sin(theta)*projNodeRadius*cfx, 0, p2[1]+cos(theta)*projNodeRadius*cfz) for theta in arange(0,pi*2.126,pi/16)]  
                #self.projRoot.attachNewNode(makeSimpleGeom(rads,[1,0,1,1],GeomLinestrips))

            #print("cfz",cfz)

            for boxCenter in centers:  # TODO there is a tradeoff here between number of box centers and mistargeting other nodes due to having a larger radius
                diff = point2projection - boxCenter  # FIXME aspect 2d??
                distance = diff.length()

                dx = (boxCenter[0] - p2[0])
                dz = (boxCenter[2] - p2[1]) / cfz  # division here maps the 2d aspected theta to the (more or less) orthogonal theta needed to map collision spheres
                theta = arctan2(dz, dx)
                #print(theta/pi,"pi radians")

                x = cos(theta) * projNodeRadius
                z = sin(theta) * projNodeRadius * cfz # multiplication here givs the actual distance the 3d projection covers in 2d
                rescaled = (x**2 + z**2)**.5  # the actual distance give the rescaling to render2d 

                if self.visualize >= self.VIS_ALL:
                    # circle with a radius of distance centered at the middle of each selection box circle
                    #bcDist = [boxCenter+(Point3(cos(theta)*distance, 0, sin(theta)*distance)) for theta in arange(0,pi*2.126,pi/32)]
                    #self.projRoot.attachNewNode(makeSimpleGeom(bcDist,[1,1,1,1],GeomLinestrips))

                    # circle with the radius for the corrected angle
                    #radRads = [ point2projection + (Point3( cos(theta)*rescaled, 0.0, sin(theta)*rescaled )) for theta in arange(0,pi*2.126,pi/32) ]
                    #rr = self.projRoot.attachNewNode(makeSimpleGeom(radRads,[1,1,0,1],GeomLinestrips))

                    # the point at which the lines from the center of the box circles to the centers of l2 nodes intersect
                    circleIntersect = self.projRoot.attachNewNode(makeSimpleGeom([point2projection+Point3(x,0,z)],[0,1,0,1]))
                    circleIntersect.setRenderModeThickness(4)

                    # a circle of the box radius
                    boxRadU = [ boxCenter + (Point3( cos(theta)*boxRadius, 0.0, sin(theta)*boxRadius )) for theta in arange(0,pi*2.126,pi/16) ]
                    self.projRoot.attachNewNode(makeSimpleGeom(boxRadU,[1,0,1,1],GeomLinestrips))

                    if self.visualize >= self.VIS_DEBUG_LINES:
                        line = [point2projection, boxCenter]


                if distance < boxRadius + rescaled:
                    for c in node.getChildren():
                        projectNode(c)
                    if self.visualize >= self.VIS_L2:
                        l2points.append(point3d)
                        if self.visualize >= self.VIS_DEBUG_LINES:
                            self.projRoot.attachNewNode(makeSimpleGeom(line,[0,1,0,1],GeomLinestrips))
                    return None  # return as soon as any one of the centers gets a hit

                elif self.visualize >= self.VIS_DEBUG_LINES:
                    self.projRoot.attachNewNode(makeSimpleGeom(line,[1,0,0,1],GeomLinestrips))

        # actually do the projection
        for c in self.collRoot.getChildren():  # FIXME this is linear and doesnt use the pseudo oct tree
            projectL2(c)

        print(len(self.curSelShown))
        #someday we thread this ;_;
        if self.visualize:
            pts3 = makeSimpleGeom(points3, [1,1,1,1])
            p3n = self.selRoot.attachNewNode(pts3)
            p3n.setRenderModeThickness(3)  # render order >_<

            if self.visualize >= self.VIS_L2:
                l2s = makeSimpleGeom(l2points,[0,1,0,1])
                l2n = self.selRoot.attachNewNode(l2s)
                l2n.setRenderModeThickness(8)

                if self.visualize >= self.VIS_ALL:
                    l2as = makeSimpleGeom(l2all,[1,0,0,1])
                    l2an = self.selRoot.attachNewNode(l2as)
                    l2an.setRenderModeThickness(8)

                    pts = makeSimpleGeom(points,[1,1,1,1])
                    self.projRoot.attachNewNode(pts)


        # set up the task to add entries to the data frame TODO own function?
        stop = self.frames['data'].getMaxItems()
        self.show_stop = len(self.curSelShown[:stop])
        self.show_count = 0
        if self.show_stop:
            taskMgr.add(self.show_task, 'show_task')

    def show_task(self, task):
        if self.show_count >= self.show_stop:
            taskMgr.remove(task.getName())
        else:  # adding buttons is pretty slow :/ TODO try to make these in the background?
            into = self.curSelShown[self.show_count]
            uuid = into.getPythonTag('uuid')
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


def makePoint(point=[0,0,0]):
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
    from util import ui_text, console, exit_cleanup, frame_rate, startup_data
    from render_manager import renderManager
    from ui import CameraControl, Axis3d, Grid3d
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

    from test_objects import makeSimpleGeom
    import numpy as np
    from dataIO import treeMe
    from uuid import uuid4
    n = 10000
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

    #with open('edge_case_data_tuple.pickle','rb') as f:
        #data_tuple = pickle.load(f)
    #r.cache['edgecase'] = False
    #r.set_nodes('edgecase',data_tuple)

    ut = ui_text()
    dt = BoxSel(visualize = BoxSel.VIS_ALL)
    run()

if __name__ == '__main__':
    main()
