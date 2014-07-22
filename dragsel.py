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

class BoxSel(HasSelectables,DirectObject,object): ##python2 sucks
    def __init__(self, visualize = False):
        super(BoxSel, self).__init__()
        self.visualize = visualize

        self.uiRoot = render.find('uiRoot')
        self.projRoot = render2d.attachNewNode('projRoot')
        self.selRoot = render.attachNewNode('selRoot')

        if self.visualize:
            print("trying to show the collision bits")
            collRoot = render.find('collideRoot')
            print(collRoot)
            for child in collRoot.getChildren():
                child.show()


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
        #self.accept("escape", sys.exit)  #no, exit_cleanup does this

        self.curSelShown = []

        #taskMgr.add(self.clickTask, 'clickTask')

    def clearSelection(self):  # TODO enable saving selections to registers etc
        while 1:
            try:
                obj = self.curSelShown.pop()
                obj.detachNode()
                #obj.remove()
            except IndexError: #FIXME slow?
                return None

    def processTarget(self,target):  # FIXME this is wrong, it needs to accomodate more child nodes
        #TODO shouldn't we let nodes set their own "callback" on click? so that there is a type per instead of shoving it all here?
            #well we also need to keep track of the previously selected set of nodes so we can turn them back off
        #note: target is a CollisionEntry
        #embed()
        #self.loadData(uid)
        #self.doRenderStuff() #this is the hard part...

        if taskMgr.hasTaskNamed('boxTask'):  # FIXME this seems a nasty way to control this...
            #text = target.getPythonTag('text')
            #uuid = target.getPythonTag('uuid')
            intoNode = target
            clear = False
        else:
            clear = True
            intoNode = target.getIntoNode()
            #text = intoNode.getPythonTag('text')

        uuid = intoNode.getPythonTag('uuid')  # FIXME it would see that this are not actually uuids...
        self.selText.setText("%s"%uuid)

        if self.__shift__:  # FIXME OH NO! we need a dict ;_; shift should toggle selection
            pass
        elif self.curSelShown:
            if clear:
                self.clearSelection()

        textNode = self.uiRoot.find("%s_text"%uuid)
        if not textNode:
            textNode = self.uiRoot.attachNewNode(TextNode("%s_text"%uuid))
            textNode.setPos(*intoNode.getBounds().getApproxCenter())
            textNode.node().setText("%s"%uuid)
            textNode.node().setEffect(BillboardEffect.makePointEye())
            self.curSelShown.append(textNode)

        #textNode.node().setCardDecal(True)


        #if not text.node().getText():
            #text.node().setText("%s"%uuid)
        #text.show()

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
            #if abs(self.__baseBox__.getScale()[0]) > .005:
            if abs(self.__baseBox__.getScale()[0]) > .0001:
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
        #cfx, cfz = base.camLens.getFilmSize()  # FIXME need this for a bunch of corrections
        cfx = 1
        cfz = base.camLens.getAspectRatio()
        cx,cy,cz = self.__baseBox__.getPos()
        sx,sy,sz = self.__baseBox__.getScale()  # gives us L/W of the box
        collRoot = render.find('collideRoot')
        self.projRoot.removeChildren()
        self.selRoot.removeChildren()

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

        def calcRC(major,minor):
            if not minor:
                return 0, [0]
            ratio = int(abs(major // minor))
            if ratio > 5:  # prevent combinatorial nightmares TODO tune me!
                ratio = 5
            split = major / ratio
            radius = ((split * .5)**2 + (minor * .5)**2)**.5
            majCents = [(split * .5) + i*(split) for i in range(ratio)]
            return radius, majCents

        if abs(sx) > abs(sz):
            boxRadius,majCents = calcRC(sx,sz)
            centers = [Point3(cx + c, 0, cz + (sz * .5)) for c in majCents]
        elif abs(sz) >= abs(sx):
            boxRadius,majCents = calcRC(sz,sx)
            centers = [Point3(cx + (sx * .5), 0, cz + c) for c in majCents]

        lensFL = base.camLens.getFocalLength()
        fov = max(base.camLens.getFov()) * (pi/180)
        #print("focal length",lensFL)
        print("fov", base.camLens.getFov())

        points = []
        def projectNode(node):
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)
            p2 = Point2()

            if not base.camLens.project(p3,p2):
                return False

            pX = p2[0]
            pZ = p2[1]
            if lX <= pX and pX <= uX: 
                if lZ <= pZ and pZ <= uZ: 
                    points.append([pX, 0, pZ])
                    self.processTarget(node)
                    #self.projRoot.attachNewNode(makePoint(Point3(p2[0], 0, p2[1])))

        l2points = []
        utilityNode = render.attachNewNode('utilityNode')
        def projectL2(node):  # FIXME so it turns out that if our aspect ratio is perfectly square everything works
            """ projec only the centers of l2 spehres, figure out how to get their radii """
            point3d = node.getBounds().getApproxCenter()
            p3 = base.cam.getRelativePoint(render, point3d)
            p2 = Point2()

            base.camLens.project(p3,p2)

            p2p = Point3(p2[0],0,p2[1])

            r3 = node.getBounds().getRadius()
            utilityNode.setPos(point3d)  # FIXME I'm sure this is slower than just subtract and norm... but who knows
            d1 = camera.getDistance(utilityNode)  # FIXME make sure we get the correct camera

            if not d1:
                d1 = 1E-9

            #fovMaxCorr = fov**2 * .5 #tan(fov * .5) #fov**2 * .25 #(fov*.9 - 1)
            #fovCorr = p2p.length() * fovMaxCorr - p2p.length() + 1  # FIXME this fails hard at high fov derp and for low fov
            fovCorr = 1
            projNodeRadius = r3 * ((lensFL*1.7)/d1) * fovCorr  # FIXME for some reason 1.7 seems about right

            # testing stuff to view the (desired) projection of l2 nodes
            #rads = [Point3(p2[0]+sin(theta)*projNodeRadius*cfx, 0, p2[1]+cos(theta)*projNodeRadius*cfz) for theta in arange(0,pi*2.126,pi/16)]
            #rads = [p2p+fixAsp(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius)) for theta in arange(0,pi*2.126,pi/32)]
            #self.projRoot.attachNewNode(makeSimpleGeom(rads,[0,0,1,1],GeomLinestrips))
            if self.visualize:
                radU = [p2p+(Point3(cos(theta)*projNodeRadius, 0, sin(theta)*projNodeRadius*cfz)) for theta in arange(0,pi*2.126,pi/32)]
                self.projRoot.attachNewNode(makeSimpleGeom(radU,[0,0,1,1],GeomLinestrips))

            #print("cfz",cfz)

            for boxCenter in centers:
                diff = p2p - boxCenter  # FIXME aspect 2d??
                distance = diff.length()

                dx = (boxCenter[0] - p2[0])
                dz = (boxCenter[2] - p2[1]) / cfz  # division here maps the 2d aspected theta to the (more or less) orthogonal theta needed to map collision spheres
                theta = arctan2(dz, dx) # + pi/2  # FIXME this is what is broken I'm sure
                #print(theta/pi,"pi radians")

                x = cos(theta) * projNodeRadius
                z = sin(theta) * projNodeRadius * cfz # multiplication here givs the actual distance the 3d projection covers in 2d
                rescaled = (x**2 + z**2)**.5  # the actual distance give the rescaling to render2d 

                #visualize
                if self.visualize:
                    #radU = [boxCenter+(Point3(cos(theta)*distance, 0, sin(theta)*distance)) for theta in arange(0,pi*2.126,pi/32)]
                    #self.projRoot.attachNewNode(makeSimpleGeom(radU,[1,1,1,1],GeomLinestrips))

                    #radRads = [ p2p + (Point3( cos(theta)*rescaled, 0.0, sin(theta)*rescaled )) for theta in arange(0,pi*2.126,pi/32) ]
                    #rr = self.projRoot.attachNewNode(makeSimpleGeom(radRads,[1,1,0,1],GeomLinestrips))

                    asdf = self.projRoot.attachNewNode(makeSimpleGeom([p2p+Point3(x,0,z)],[0,1,0,1]))
                    asdf.setRenderModeThickness(4)

                    boxRadU = [ boxCenter + (Point3( cos(theta)*boxRadius, 0.0, sin(theta)*boxRadius )) for theta in arange(0,pi*2.126,pi/16) ]
                    self.projRoot.attachNewNode(makeSimpleGeom(boxRadU,[1,0,1,1],GeomLinestrips))
                    line = [p2p,boxCenter]

                if distance < boxRadius + rescaled:
                    #l2points.append(p2p)
                    if self.visualize:
                        self.projRoot.attachNewNode(makeSimpleGeom(line,[0,1,0,1],GeomLinestrips))
                    l2points.append(point3d)
                    for j in range(node.getNumChildren()):
                        projectNode(node.getChild(j))
                    return None  # return as soon as any one of the centers gets a hit
                elif self.visualize:
                    self.projRoot.attachNewNode(makeSimpleGeom(line,[1,0,0,1],GeomLinestrips))

                


        for i in range(collRoot.getNumChildren()):  # FIXME linear search SUCKS :/ we have the oct tree :/
            projectL2(collRoot.getChild(i))
            #for j in range(l2.getNumChildren()):
                #projectNode(l2.getChild(j))

        print(len(self.curSelShown))
        #someday we thread this ;_;
        l2s = makeSimpleGeom(l2points,[1,0,0,1])
        l2n = self.selRoot.attachNewNode(l2s)
        l2n.setRenderModeThickness(8)

        pts = makeSimpleGeom(points,[1,1,1,1])
        self.projRoot.attachNewNode(pts)
        #self.projRoot.flattenStrong()  # this makes the colors go away ;_;


    def _getEnclosedNodes(self):
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
                    if node.getCollideMask() == BitMask32.bit(BITMASK_COLL_CLICK): #FIXME we can massively improve performance on l2 nodes wholely contained in box
                    #if node.getPythonTag('text'):
                        self.processTarget(node)
                        return True
                    else:
                        output = []
                        out = None
                        #print("NumChildren",node.getNumChildren())
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
        #print(output)

        #just add the scale and everything will be ok
        #start with the l2 nodes since there are fewer ie collision mask = BITMASK_COLL_MOUSE

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
