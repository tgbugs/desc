from __future__ import print_function
#import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
#from panda3d.core import PandaNode,NodePath
from panda3d.core import TextNode, PandaNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomVertexWriter
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips #useful for nodes
from panda3d.core import GeomPoints
from panda3d.core import Texture, GeomNode
from panda3d.core import Point3,Point2,Vec3,Vec4,BitMask32

from panda3d.core import AmbientLight

from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay,CollisionLine


import sys
from threading import Thread
from IPython import embed

from defaults import *
from util import genLabelText


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
        print('getting target....')
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

class BoxSel(HasSelectables,DirectObject,object): ##python2 sucks
    def __init__(self):
        super(BoxSel, self).__init__()

        #corner selection detection #XXX this turns out to be slower, only traverse all the l2 nodes once faster
        self.cornerPicker = CollisionTraverser()
        self.cpq = CollisionHandlerQueue()  # FIXME we might only need one of these?
        self.cornerPickerNode = CollisionNode('cornerRay')
        self.cornerPickerNP = camera.attachNewNode(self.cornerPickerNode)
        self.cornerPickerNode.setFromCollideMask(BitMask32.bit(BITMASK_COLL_MOUSE))
        self.cornerPickerRay = CollisionLine()
        self.cornerPickerNode.addSolid(self.cornerPickerRay)
        self.cornerPicker.addCollider(self.cornerPickerNP, self.cpq)
        self.cornerPicker.showCollisions(render)


        #self.__mouseDown__ = False

        #setup the selection box
        #self.__startNode__ = render2d.attachNewNode(PandaNode()) #empty node
        boxNode = GeomNode('selectBox')
        boxNode.addGeom(makeSelectRect())
        self.__baseBox__ = render2d.attachNewNode(boxNode)
        self.__baseBox__.hide()

        self.selText = genLabelText('uuid',3)
        self.selText.reparentTo(base.a2dTopLeft)

        self.accept('mouse1',self.gotClick)
        self.accept('shift-mouse1',self.gotClick)
        self.accept('mouse1-up',self.gotRelease)
        self.accept("escape", sys.exit)

        self.curSelShown = []

        #taskMgr.add(self.clickTask, 'clickTask')

    def clearSelection(self):  # TODO enable saving selections to registers etc
        while 1:
            try:
                obj = self.curSelShown.pop()
                obj.hide()
            except IndexError: #FIXME slow?
                return None

        
    def processTarget(self,target):
        #TODO shouldn't we let nodes set their own "callback" on click? so that there is a type per instead of shoving it all here?
            #well we also need to keep track of the previously selected set of nodes so we can turn them back off
        #note: target is a CollisionEntry
        #embed()
        #self.loadData(uid)
        #self.doRenderStuff() #this is the hard part...

        text = None

        if taskMgr.hasTaskNamed('boxTask'):  # FIXME this seems a nasty way to control this...
            text = target.getPythonTag('text')
            intoNode = None
        else:
            intoNode = target.getIntoNode()
            text = intoNode.getPythonTag('text')
            uuid = intoNode.getPythonTag('uuid')
            self.selText.setText("%s"%uuid)

        text.show()

        if self.__shift__:  # FIXME OH NO! we need a dict ;_; shift should toggle selection
            pass
        elif self.curSelShown:
            if intoNode != None:
                self.clearSelection()

        self.curSelShown.append(text)

            #add stuff, nasty race conditions if someone releases shift and the mouse at the same time
            #and subtract from selection too while keeping the rest selected
        #elif self.__ctrl__:  # may not need
            #pass
        #elif not taskMgr.hasTaskNamed('boxTask'):  # FIXME this seems a nasty way to control this...

        return None

    def gotClick(self):  # TODO rename this to inherit from HasSelectables
        #if not self.__mouseDown__: #this case never happens unless the univers explodes?
        #self.__mouseDown__ = True
        target = self.getClickTarget()  #this isnt an RTS so we want click/drag
        #TODO in theory this should not normally take this long???
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
            self.__baseBox__.hide()
            self.getEnclosedNodes()
            taskMgr.remove('boxTask')

    #def clickTask(self, task): #this will probably need to handle many possible click targets
        #if type(self.__mouseDown__) is tuple:
            #self.__mouseStart__ = self.__mouseDown__
        #elif self.__mouseDown__:
            #pass #dragging?
        #return task.cont

    def boxTask(self, task): #this will only be active if mouse down and not click
        x,y = base.mouseWatcherNode.getMouse()
        cx,cy,cz = self.__baseBox__.getPos()
        self.__baseBox__.setSx(x-cx)
        #self.__baseBox__.setSy(y-cy)
        self.__baseBox__.setSz(y-cz) #so it turns out that 'z' is what we want???
        #embed()
        return task.cont

    def getEnclosedNodes(self):
        cx,cy,cz = self.__baseBox__.getPos()
        sx,sy,sz = self.__baseBox__.getScale()  # gives us L/W of the box
        
        collRoot = render.find('collideRoot')

        
        corners = [
            #[cx + sx , cz + sz],
            #[cx + sx , cz - sz],
            #[cx - sx , cz + sz],
            #[cx - sx , cz - sz],
            [cx + sx , cz + sz],
            [cx , cz + sz],
            [cx + sx , cz],
            [cx, cz],
            #[cx + sx * .5, cz + sz * .5],
        ]
        #use 1 picker ray on the corners of the box to pick against MOUSE


        rootSelNode = collRoot

        nodes = set() 
        #for c in corners:
            #self.cornerPickerRay.setFromLens(base.camNode, *c)

            #self.cornerPicker.traverse(rootSelNode)
            #ents = [e for e in self.cpq.getEntries()]
            #nodes.update(ents)

            #print("entries",ents)
            #print("nodes",nodes)

            #if self.pq.getNumEntries() > 0: #if we got something sort it
                #self.pq.sortEntries()
                #return self.pq.getEntry(0)

        #if not nodes:
            #return False
       

        #nearPoint = render.getRelativePoint(camera, self.pickerRay.getOrigin())
        #nearVec = render.getRelativeVector(camera, self.pickerRay.getDirection())
        #thingToDrag.obj.setPos(PointAtZ(.5, nearPoint, nearVec)) #not sure how this works

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

        #print("running enclosed node task")

        #boxCentX = cx + sx * .5
        #boxCentZ = cz + sz * .5
        #subtract each center from the center of the coll circle
        #make sure that that difference plus the radius is < scale * .5
       
        def checkNode(node):
            #print(node)
            #embed()  # FIXME lol oops, forgot that all the collision nodes are centered at zero and that their solids are positioned!
            #point3d = node.getPos() #FIXME this wont work... we'll miss cases where center is outside
            point3d = node.getBounds().getApproxCenter()  # FIXME this might work better if we position nodes instead of geoms?
            radius = node.getBounds().getRadius()
            #we need to move this point toward the center of the box...
            p3 = base.cam.getRelativePoint(render, point3d)  # FIXME probably not render?
            p2 = Point2()

            rproj = Point2()
            base.camLens.project(Point3(p3[0]+radius,p3[1],p3[2]), rproj)

            dist = p2 - rproj
            dist = dist.length()
            #print(dist)
            dist = 0  # XXX until we can figure out what is wrong

            if not base.camLens.project(p3,p2):
                #displacement = (p2[0]**2 + p2[1]**2) ** .5
                #if displacement - dist < 1.414213:
                #check if we are w/in the radius?
                #print(p2)
                return False

            #r2d = Point3(p2[0], 0, p2[1])
            #a2d = aspect2d.getRelativePoint(render2d, r2d)  # apparently we don't actually need this?
            #render2d.attachNewNode(makePoint(r2d))
            pX = p2[0] #r2d.getX()
            pZ = p2[1] #r2d.getZ()

            #if abs(pX - boxCentX) + radius < sx * .5 and abs(pZ - boxCentZ) + radius < sy * .5:
                #for i in range(node.getNumChildren()):
                    #proccessTarget(node.getChild(i))
                #return True
            if lX-dist <= pX and pX <= uX+dist: 
                if lZ-dist <= pZ and pZ <= uZ+dist: 
                    #print(node.getCollideMask())
                    #print(BitMask32.bit(BITMASK_COLL_CLICK))
                    #if node.getCollideMask() == BitMask32.bit(BITMASK_COLL_CLICK): #FIXME we can massively improve performance on l2 nodes wholely contained in box
                    if node.getPythonTag('text'):
                        self.processTarget(node)
                        return True
                    else:
                        output = []
                        out = None
                        print("NumChildren",node.getNumChildren())
                        for i in range(node.getNumChildren()):
                            out = checkNode(node.getChild(i))
                        output.append(out)
                        return output

        output = []
        out = None
        for i in range(collRoot.getNumChildren()):  # It is faster to just iterate over all the l2 nodes
            l2 = collRoot.getChild(i)
            out = checkNode(collRoot.getChild(i))
        #for node in nodes:
            #collNode = node.getIntoNode()
            #for i in range(collNode.getNumChildren()):
                #out = checkNode(collNode.getChild(i))
            #for j in range(l2.getNumChildren()):
                #out = checkNode(l2.getChild(j))
            output.append(out)
        print(output)

        #just add the scale and everything will be ok
        #start with the l2 nodes since there are fewer ie collision mask = BITMASK_COLL_MOUSE

def makePoint(point):
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
    from util import Utils
    base = ShowBase()
    base.disableMouse()
    ut = Utils()
    dt = BoxSel()
    run()

if __name__ == '__main__':
    main()
