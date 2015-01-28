#check out stuff from glsl volume rendering google search
#also panda documentation
#to do 4d stuff we just set up a bunch of 3d textures and swap them and keep the same shader
from panda3d.core import Shader

from panda3d.core import Texture

from panda3d.core import loader


tex = Texture.setup3dTexture(sx, sy, sz, component_type, format_)  #all ints
# TODO how to read the matrix in?!

nodePath.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
nodePath.setTexGen(TextureStage.getDefault(), 0, 0, 0)
nodePath.setTexture(tex)

myShader = Shader.load(Shader.SL_GLSL, "my_vert.glsl", "my_frag.glsl", "my_geom.glsl")

nodePath.set_shader(myShader)
nodePath.set_shader_input("my_param",(1,1,1))

# apparently the sizes need to be powers of 2??? but maybe we can just map the relevant coords 1:1

# TODO for volume rendering we will hopefully use the alpha value?
# not clear exactly how to load in a full 3d matrix...
