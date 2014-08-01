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
from threading import Thread
from IPython import embed

from defaults import *
from util import genLabelText
from test_objects import makeSimpleGeom


RADIANS_PER_DEGREE = 0.017453292519943295

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
    def __init__(self, frames = None, visualize = False):
        super().__init__()
        self.visualize = visualize

        self.uiRoot = render.find('uiRoot')
        self.projRoot = render2d.attachNewNode('projRoot')
        self.selRoot = render.attachNewNode('selRoot')

        self.frames = frames

        if self.visualize:
            print("trying to show the collision bits")
            self.collRoot = render.find('collideRoot')
            print(self.collRoot)
            for child in self.collRoot.getChildren():
                child.show()

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
        #self.accept("escape", sys.exit)  #no, exit_cleanup does this

        self.curSelShown = []
        self.curSelNodes = []

    def clearSelection(self):  # TODO enable saving selections to registers etc
        taskMgr.remove('show_task')
        if self.curSelShown:
            self.curSelShown = []
            self.frames['data'].del_all()  # FIXME!
        self.clearHighlight()
        
    def clearHighlight(self):
        if self.curSelNodes:
            for node in self.curSelNodes:
                node.removeNode()
            self.curSelNode = []
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
            if not self.__shift__ and self.curSelNodes:
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
            if not self.visualize:
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

        def calcRC(major, minor):
            if not minor:
                return 0, [0]
            ratio = major / minor
            if ratio > 5:  # prevent combinatorial nightmares TODO tune me!
                ratio = 5
            else:
                ratio = int(ratio)
            split = major / ratio
            radius = ((split * .5)**2 + (minor * .5)**2)**.5
            majCents = [(split * .5) + i*(split) for i in range(ratio)]
            return radius, majCents

        asx, asz = abs(sx), abs(sz)
        if asx > asz:
            boxRadius, majCents = calcRC(asx, asz)
            centers = [Point3(cx + c, 0, cz + (sz * .5)) for c in majCents]
        else:
        #elif asz >= asx:
            boxRadius, majCents = calcRC(asz, asx)
            centers = [Point3(cx + (sx * .5), 0, cz + c) for c in majCents]

        lensFL = base.camLens.getFocalLength()
        fov = max(base.camLens.getFov()) * RADIANS_PER_DEGREE
        #print("focal length",lensFL)
        #print("fov", base.camLens.getFov())

        points = []
        points3 = []
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
                    points.append([pX, 0, pZ])
                    self.processTarget(node)
                    points3.append(point3)
                    #self.projRoot.attachNewNode(makePoint(Point3(p2[0], 0, p2[1])))

        l2points = []
        utilityNode = render.attachNewNode('utilityNode')
        def projectL2(node):  # FIXME so it turns out that if our aspect ratio is perfectly square everything works
            """ projec only the centers of l2 spehres, figure out how to get their radii """
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)
            p2 = Point2()

            base.camLens.project(p3,p2)

            point2projection = Point3(p2[0],0,p2[1])

            r3 = node.getBounds().getRadius()
            utilityNode.setPos(point3d)  # FIXME I'm sure this is slower than just subtract and norm... but who knows
            d1 = camera.getDistance(utilityNode)  # FIXME make sure we get the correct camera
            if not d1:
                d1 = 1E-9
            #fovMaxCorr = fov**2 * .5 #tan(fov * .5) #fov**2 * .25 #(fov*.9 - 1)
            #fovCorr = point2projection.length() * fovMaxCorr - point2projection.length() + 1  # FIXME this fails hard at high fov derp and for low fov
            fovCorr = 1
            projNodeRadius = r3 * ((lensFL*1.7)/d1) * fovCorr  # FIXME for some reason 1.7 seems about right

            # testing stuff to view the (desired) projection of l2 nodes
            #rads = [Point3(p2[0]+sin(theta)*projNodeRadius*cfx, 0, p2[1]+cos(theta)*projNodeRadius*cfz) for theta in arange(0,pi*2.126,pi/16)]
            #rads = [point2projection+fixAsp(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius)) for theta in arange(0,pi*2.126,pi/32)]
            #self.projRoot.attachNewNode(makeSimpleGeom(rads,[0,0,1,1],GeomLinestrips))
            if self.visualize:
                radU = [point2projection+(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius*cfz)) for theta in arange(0,pi*2.126,pi/32)]
                self.projRoot.attachNewNode(makeSimpleGeom(radU,[0,0,1,1],GeomLinestrips))

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

                if self.visualize:
                    #radU = [boxCenter+(Point3(cos(theta)*distance, 0, sin(theta)*distance)) for theta in arange(0,pi*2.126,pi/32)]
                    #self.projRoot.attachNewNode(makeSimpleGeom(radU,[1,1,1,1],GeomLinestrips))

                    #radRads = [ point2projection + (Point3( cos(theta)*rescaled, 0.0, sin(theta)*rescaled )) for theta in arange(0,pi*2.126,pi/32) ]
                    #rr = self.projRoot.attachNewNode(makeSimpleGeom(radRads,[1,1,0,1],GeomLinestrips))

                    asdf = self.projRoot.attachNewNode(makeSimpleGeom([point2projection+Point3(x,0,z)],[0,1,0,1]))
                    asdf.setRenderModeThickness(4)

                    boxRadU = [ boxCenter + (Point3( cos(theta)*boxRadius, 0.0, sin(theta)*boxRadius )) for theta in arange(0,pi*2.126,pi/16) ]
                    self.projRoot.attachNewNode(makeSimpleGeom(boxRadU,[1,0,1,1],GeomLinestrips))
                    line = [point2projection, boxCenter]

                if distance < boxRadius + rescaled:
                    l2points.append(point3d)
                    for c in node.getChildren():
                        projectNode(c)
                    if self.visualize:
                        self.projRoot.attachNewNode(makeSimpleGeom(line,[0,1,0,1],GeomLinestrips))
                    #for j in range(node.getNumChildren()):
                        #projectNode(node.getChild(j))
                    return None  # return as soon as any one of the centers gets a hit

                elif self.visualize:
                    self.projRoot.attachNewNode(makeSimpleGeom(line,[1,0,0,1],GeomLinestrips))

        # actually do the projection
        for c in self.collRoot.getChildren():  # FIXME this is linear and doesnt use the pseudo oct tree
            projectL2(c)
        #for i in range(self.collRoot.getNumChildren()):  # FIXME linear search SUCKS :/ we have the oct tree :/
            #projectL2(self.collRoot.getChild(i))
            #for j in range(l2.getNumChildren()):
                #projectNode(l2.getChild(j))

        print(len(self.curSelShown))
        #someday we thread this ;_;
        if self.visualize:

            l2s = makeSimpleGeom(l2points,[1,0,0,1])
            self.selRoot.removeChildren()
            l2n = self.selRoot.attachNewNode(l2s)
            l2n.setRenderModeThickness(8)

            pts3 = makeSimpleGeom(points3, [1,1,1,1])
            self.selRoot.attachNewNode(pts3)

            pts = makeSimpleGeom(points,[1,1,1,1])
            self.projRoot.removeChildren()
            self.projRoot.attachNewNode(pts)
            #self.projRoot.flattenStrong()  # this makes the colors go away ;_;

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
        textNode = self.uiRoot.attachNewNode(TextNode("%s_text"%uuid))
        textNode.setPos(*intoNode.getBounds().getApproxCenter())
        textNode.node().setText("%s"%uuid)
        textNode.node().setEffect(BillboardEffect.makePointEye())
        self.curSelNodes.append(textNode)

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
    from util import ui_text
    base = ShowBase()
    base.disableMouse()
    ut = ui_text()
    dt = BoxSel()
    embed()
    run()

if __name__ == '__main__':
    main()
