THIS SHALL BE A MODAL PROGRAM ALA VIM
we need modes so that we can handle the complexity

ideas:
 1. modes can also be selected/indicated visually to let people click
 2. in theory we might be able to use encodeToBamStream

modes:
 1. camera
 2. visual (select/explore/control what can be seen)
 3. insert (add a note or something?) implement last

accessible from everywhere except insert mode:
 1. search
 2. command line

notes:
 1. yes, high node counts are a problem, but apparently not in and of themselves?
    solutions are: RigidBodyCombiner or NodePath.flattenStrong() (Light or Medium)
    as long as selection still works this should not be an issue and we can alwasy
    manipulate the geometry directly...
 2. read rdbs blog posts... threading-model Cull/Draw, also buffer protocols for direct manip seems good for quite a bit of stuff
    holy crap that massively degrades performance!!!! multiplies the cull and draw times by a factor of 4!!!!!
 3. sweet spot for nodes is around 3000 on my hardware, guys in the thread say 300-500
 4. also, turns out it might be possible to do collision on individual nodes and keep that index by itself and thus not have to worry about the
    impact on rendering

 bugs:
  1. turn on threading-mode Cull/Draw, do mouse collision with showCollisions(render) on the CollisionTraverser will segfault

things
======
 7. we could use getPythonTag to make it really easy to link collision nodes to vertecies...
 6. collision nodes need to be able to quickly reference the geometry atom
    they are bound to, this means the index of a specific vertex in a geom or
    a geom itself to manipulate either the pixel shader or the texture, hrm
    we might be able to use a vertex shader to change color of selected vertices
 1. separate out the proceduarl object definitions into their own file
 2. keybinds config file: mapping from config names to functions
 3. CONCLUSION: do not use the scene graph for most things, it is simply too slow allow selection on sub components, or figure out how to thread this
 4. 4d grid plus the ability to zip through any 1 2 or 3 of the dimensions with a slider... 
 5. simple way to represent relations as lines with colors to mark their type
 8. http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/ << counter things irritating :/
