#check out stuff from glsl volume rendering google search
#also panda documentation
#to do 4d stuff we just set up a bunch of 3d textures and swap them and keep the same shader
from panda3d.core import Shader
from panda3d.core import Texture, TextureStage, TexGenAttrib
from panda3d.core import PNMImage
from panda3d.core import GeomNode
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans

from panda3d.core import Geom, GeomVertexWriter, GeomVertexFormat, GeomVertexData
#from panda3d.core import loader

import numpy as np

from .util.ipython import embed

def make_cube(x, y, z):  # FIXME make prism
    """ make x, y, z sized cube (ints pls) """
    colors = [[1,1,1,0] for i in range(8)]
    #colors[0] = np.array((1,1,1,1))
    #colors[1] = np.array((1,0,0,0))
    #colors[2] = np.array((0,1,0,0))
    #colors[5] = np.array((0,0,1,0))
    points = (
        (0,0,0),
        (0,0,z),
        (0,y,0),
        (0,y,z),
        (x,0,0),
        (x,0,z),
        (x,y,0),
        (x,y,z),
    )
    order = [0, 5, 1, 7, 3, 2, 1, 0, 5, 4, 7, 6, 2, 4, 0]  # perfect for clockwise
    #order = [2, 6, 3, 7, 5, 6, 4, 2, 0, 3, 1, 4, 0, 4]
    #order.reverse()
    #order = [4, 3, 7, 8, 5, 3, 1, 4, 2, 7, 6, 5, 2, 1]


    fmt = GeomVertexFormat.getV3c4()
    vertexData = GeomVertexData('points', fmt, Geom.UHStatic)
    verts = GeomVertexWriter(vertexData, 'vertex')
    color = GeomVertexWriter(vertexData, 'color')

    for p,c in zip(points,colors):
        verts.addData3f(*p)
        color.addData4f(*c)

    targetTris = GeomTristrips(Geom.UHStatic)
    targetTris.addConsecutiveVertices(0,8)
    for i in order:
        targetTris.addVertex(i)#-1)
    targetTris.closePrimitive()

    target = Geom(vertexData)
    target.addPrimitive(targetTris)
    return target
# apparently the sizes need to be powers of 2??? but maybe we can just map the relevant coords 1:1

# TODO for volume rendering we will hopefully use the alpha value?
# not clear exactly how to load in a full 3d matrix...

def make_texture3d(array):
    """ assumes x y z ordering for slicing """
    tex = Texture()
    xl,yl,zl = array.shape

    tex.setup3dTexture(xl, yl, zl, Texture.TUnsignedByte, Texture.FLuminanceAlphamask)  #all ints
    tex.setQualityLevel(3)
    mv = memoryview(tex.modifyRamImage())
    asdf = np.asarray(mv)
    
    # so it turns out that panda uses fortran style indexing for arrays (apparently)???
    # empeically using reshape(x,y,z,'A') to map  works??? figure this out!
    # to map indexes directly to x, y, z values
    values = asdf[::2].reshape(*array.shape, order='A')
    values[::] = array  # TODO transform between writing and cartesian coordinate systems

    tex.setMagfilter(Texture.FTNearest)
    tex.setMinfilter(Texture.FTNearest)

    return tex, None


###
#   Tests
###

def main():
    from direct.showbase.ShowBase import ShowBase
    from .util.util import startup_data, exit_cleanup, ui_text, console, frame_rate
    from .ui import CameraControl, Axis3d, Grid3d
    from keys import AcceptKeys, callbacks

    base = ShowBase()
    base.disableMouse()
    base.setBackgroundColor(0,0,0)
    startup_data()
    frame_rate()
    uit = ui_text()
    con = console()
    ec = exit_cleanup()
    cc = CameraControl()
    ax = Axis3d()
    gd = Grid3d()
    ac = AcceptKeys()


    ###
    # XXX REAL CODE HERE
    ###

    size = 256

    shift = .001  # .001 works with scale .499 and size 2
    scale = 1/size  - (1/ (size * 100))
    #scale = 1
    #shift = -size * .125

    array = np.random.randint(0,255,(size,size,size))

    #array = np.linspace(0,255,size**3).reshape(size,size,size)

    tex, memarray = make_texture3d(array)
    tex2 = Texture()
    tex2.setup2dTexture()


    # TODO how to read the matrix in?!

    geomNode = GeomNode('shader_test')
    geomNode.addGeom(make_cube(size,size,size))
    nodePath = render.attachNewNode(geomNode)
    #embed()
    nodePath.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
    nodePath.setTexProjector(TextureStage.getDefault(), render, nodePath)
    nodePath.setTexPos(TextureStage.getDefault(), shift, shift, shift)
    nodePath.setTexScale(TextureStage.getDefault(), scale)

    nodePath.setTexture(tex)
    #embed()
    #nodePath.setTexGen(TextureStage.getDefault(), 0, 0, 0)  #bug?

    #"""
    myShader = Shader.load(Shader.SL_GLSL, "my_vert.glsl", "my_frag.glsl")#, "my_geom.glsl")

    # wow, this actually... turns the box black or something, probably shound't attach the texture to the nodepath if we do it this way
    nodePath.set_shader(myShader)
    #nodePath.set_shader_input("my_param",(1,1,1))
    nodePath.set_shader_input("tex",tex2)
    nodePath.set_shader_input("volume_tex",tex)
    nodePath.set_shader_input("stepsize",.5)
    #"""

    run()

if __name__ == '__main__':
    main()
