"""
    taking over from test_objects and render_manager this is where we are going
    to handle the geometry and collision creation from data
"""

from panda3d.core import GeomVertexFormat, GeomVertexData

#geomTypes
from panda3d.core import GeomTristrips, GeomTriangles
from panda3d.core import GeomLinestrips, GeomLines
from panda3d.core import GeomPoints


class geometryData:
    def __init__(self, positions, geometry, colors, uuids, bounds = None):
        pass


def convert_to_geometry(something):
    return property_formatted_geometry

def makeGeom(positions, geometry, colors):
    #geometry shall be?
        #a list of?
        #lists of (position, geometry, color) tuples
        # one of the 5 geom types listed above in imports
            # if it is this then the length of the geometry should be the tipoff?
        #Geoms?
        #



    #for each position:
        #if we want something more than points:
            #ASSUME THAT ALL GEOMETRY HAS ALREADY BEEN ZEROED!
            #ASSUME THAT ALL GEOMETRY POINTS ARE TRISTRIPABLE!

            #make the geom
            #put the geom at position

    #flatten

    return geom

def makeBam(geom):
    geom.__reduce__().[1][-1]  # look at the product of this reduce to see why 1,-1
    return bam

def makeCol(positions, uuids, bounds):
    return treeMe(None, positions, uuids, bounds, None, None, None, request_hash)
