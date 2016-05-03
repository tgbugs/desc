# desc
Network transparent 3d visualization system for scientific data
based on the [panda3d](https://github.com/panda3d/panda3d) graphics engine.

# about
This is experimental work using a 3d engine for interactive data visualization in python.
There is a weird mismash of tools used to implement some features (panda3d in some places,
asyncio in others). Some points of (dis)interest. There is an really bad wireprotocol
written from communicating between the visualization client and server in request.py.
There is also an implementation of an octree (in trees.py) for doing fast collision
detection to enable selection of large numbers of data points at the same time. There
is also some work for interconverting between numpy arrays and 3d textures that
could be useful for volume rendering in shaders.py (comment out the shader init code).
Finally, there are some useful fixes [util/](util/) for IPython embed in a threaded
environment and a fix to ProcessPoolExecutor that prevents KeyboardInterrupt from propagating.

# requirements
 1. Linux, tested on Debian and Gentoo. (may work on Windows)
 2. python3.4
 3. panda3d compiled for python3 (documentation is in panda.py, but that may be out of date).
 	Alternately, run [install.sh](install.sh).

# running
Parts of desc can be used as a module for visualization in other projects,
but if you want to run it directly you need to use the -m option to run the
module like this `python -m desc.client`. You will need to have the parent
folder where this repository was cloned in your `PYTHONPATH`. 

# quickstart
Navigate with right mouse, right mouse + shift, and mousewheel. Select with left mouse.
The `n` and `r` keys generate data to display, the `i` key opens an interactive
(nonblocking) ipython shell in the original terminal emulator, the `c` key opens an
iteractive (blocking) shell. The `v` key cycles through selection visualization options.
To exit, hit the `esc` key.

# configuration
Keybinds are found in [ui.py](ui.py) or in the defintion of the `@event_callback`
decorator for a given method (eg in [render_manager.py](render_manager.py)).
Any method decorated with `@event_callback` can be referenced by name in
the keybinds dictionary in [ui.py](ui.py). To pull out all potential names
use `grep -ri event_callback -A1` (maybe this will be automated someday).

