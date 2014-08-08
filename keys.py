#from functools import wraps
#from collections import defaultdict

callbacks = {}


# TODO bindings for different modes

def ui_callback(func):  # TODO default binds and collisions?
    """ wrapper the collects all possible keyboard/mouse callbacks """
    if func.__name__ in callbacks:
        raise ValueError('Namespace collision. There is already a function with that name in the callback list!')
    callbacks[func.__name__] = func  # FIXME namespace collisions
    return func
    #@wraps(func)
    #def wrapper(*args, **kwargs):
        #pass

# panda3d event names
rel = '-up'  # release

key_events = [
]

mouse_events = [
    'mouse1',
    'mouse2',  # middle mouse
    'mouse3',
    'mouse4',
    'mouse5',
    'wheel_up',
    'wheel_down',
]

key_modifiers = [
    'alt-',
    'shift-',
    'control-',
]

