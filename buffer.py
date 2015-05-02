#!/usr/bin/env python3.4
""" Example for how to load vertex data from numpy directly
"""

import numpy as np
from panda3d.core import Geom, GeomVertexFormat, GeomVertexData

from .util.ipython import embed

size = 1000
data = np.random.randint(0,1000,(size,3))
#color = np.random.randint(0,255,(size,4))
color = np.repeat(np.random.randint(0,255,(1,4)), size, 0)
#full = np.hstack((data,color))
full = [tuple(d) for d in np.hstack((data,color))]
#full = [tuple(*d,*color) for d in data]


geom = GeomVertexData('points', GeomVertexFormat.getV3c4(), Geom.UHDynamic)
geom.setNumRows(len(full))
array = geom.modifyArray(0)  # need a writeable version
handle = array.modifyHandle()

#options are then the following:

view = memoryview(array)
arr = np.asarray(view)
arr[:] = full

embed()
#OR
#handle.copyDataFrom('some other handle to a GVDA')
#handle.copySubataFrom(to_start, to_size, buffer, from_start, from_size)
