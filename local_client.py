#!/usr/bin/env python3.4

def main():
    from asyncio import get_event_loop
    from threading import Thread

    # server bits
    from server import tokenManager, requestCacheManager, responseMaker, make_shutdown
    from defaults import CONNECTION_PORT, DATA_PORT

    # render setup
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import loadPrcFileData
    from panda3d.core import PStatClient

    from render_manager import renderManager
    from selection import BoxSel
    from util import ui_text, console, exit_cleanup, frame_rate, startup_data
    from ui import CameraControl, Axis3d, Grid3d, GuiFrame

    from protocols import connectionServerProtocol, dataServerProtocol
    from protocols import dataClientProtocol
    from process_fixed import ProcessPoolExecutor_fixed as ProcessPoolExecutor

    # common
    event_loop = get_event_loop()
    ppe = ProcessPoolExecutor()

    # server
    tm = tokenManager()
    rcm = requestCacheManager(0)

    conServ = connectionServerProtocol(tm)
    datServ = dataServerProtocol(event_loop, responseMaker, rcm, tm, ppe)

    coro_conServer = event_loop.create_server(conServ, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl
    coro_dataServer = event_loop.create_server(datServ, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl and this can be another box
    serverCon = event_loop.run_until_complete(coro_conServer)
    serverData = event_loop.run_until_complete(coro_dataServer)



    # client
    PStatClient.connect() #run pstats in console
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()

    base.setBackgroundColor(0,0,0)
    base.disableMouse()
    # TODO init all these into a dict or summat?
    startup_data()
    frame_rate()
    ut = ui_text()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()

    frames = {
        'data':GuiFrame('Data view')
    }

    rendMan = renderManager(event_loop, ppe)
    bs = BoxSel(frames)

    datCli_base = dataClientProtocol(rendMan.set_nodes, rendMan.set_send_request, rendMan.cache, event_loop)
    datCli = datCli_base()
    datCli.connection_lost('START')

    eventThread = Thread(target=event_loop.run_forever)
    eventThread.start()

    con = console(locals(), True)
    shutdown = make_shutdown(event_loop, eventThread, serverCon, serverData, ppe)
    el = exit_cleanup(event_loop, ppe, datCli.transport, shutdown)

    run()


if __name__ == '__main__':
    main()
