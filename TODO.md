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

caching hierarchy
=================
currently visible -> attached to the scene graph but hidden ->
detached from scene graph -> still in bam file form in local cache ->
in server cache -> in server persistent store -> has not been computed yet

the cache really needs to hold the gzed bam geometry and the associated serialized
collision data and UI data, we *might* want to break up the UI data if possible and
just setPythonTag (and increase the priority if empty) of that node when we get a chance
(this is only really and issue if we are working with MASSIVE numbers of nodes)


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
 6. multipe camera views/ windows, get multiple perspectives on a problem at the same time... well, each diferent arragment will require its own model... but it will be nice to have them side by side at least
 8. http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/ << counter things irritating :/
 9. make it possible to view a 'slice' through a 3d structure specifically by hiding all points/geom along an axis
    support for arbitrary axes *should* be possible though their meaning outside say a raw data pixel volume is nebulous
 10. Write a function to convert selected objects, and the relevant set of properties to a set of points!
 11. Relative scaling of the base grid for different objects can be handled locally using the scale property on geoms?
     but will need to sync with the collision surfaces somehow :/
 12. random thought, if we get a token uuid here, fine, great awesome, we can switch back to know view from data view and just move the camera that was in know view so that the size and location of the token object doesnt change!
 13. marks, store tuples of camera positions and scene node visibility so we can just set those particular nodes back to visible

 14. SUPER CRITICIAL: we do need to deal with the fact that what the user wants may change between the time they request it and they time
     they receive it, so we need to keep track of what should be rendered locally even if we end up sending all of it. Basically we need
     one additional layer of separation cache=True/False is not sufficient

 15. cache invalidation happens on the server, we might need a special opcode to tell the client, thoughts for another day
 16. need a switch that prevents the server from caching when we run a local session, send it all to the client immediately and bypass cache
 17. need to handle timeouts and lost connections
 18. if we dont creat the connection immediately, create a coro to retry
 19. apparently trying to spawn lots of requests can segfault!?
