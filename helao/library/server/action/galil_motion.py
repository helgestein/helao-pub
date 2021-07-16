# shell: uvicorn motion_server:app --reload
""" A FastAPI service definition for a motion/IO server, e.g. Galil.

The motion/IO service defines RESTful methods for sending commmands and retrieving data
from a motion controller driver class such as 'galil_driver' or 'galil_simulate' using
FastAPI. The methods provided by this service are not device-specific. Appropriate code
must be written in the driver class to ensure that the service methods are generic, i.e.
calls to 'motion.*' are not device-specific. Currently inherits configuration from
driver code, and hard-coded to use 'galil' class (see "__main__").
"""

import json
from importlib import import_module
from typing import Optional, List, Union
from fastapi import Request
from helao.library.driver.galil_driver import move_modes, transformation_mode
from helao.core.server import makeActServ, setupAct


def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config
    C = config["servers"]
    S = C[servKey]

    # check if 'simulate' settings is present
    if not "simulate" in S.keys():
        # default if no simulate is defined
        print('"simulate" not defined, switching to Galil Simulator.')
        S["simulate"] = False
    if S["simulate"]:
        print("Galil motion simulator loaded.")
        from helao.library.driver.galil_simulate import galil
    else:
        from helao.library.driver.galil_driver import galil

    app = makeActServ(
        config, servKey, servKey, "Galil motion server", version=2.0, driver_class=galil
    )

    @app.post(f"/{servKey}/setmotionref")
    async def setmotionref(request: Request, action_dict: Optional[dict] = None):
        """Set the reference position for xyz by 
        (1) homing xyz, 
        (2) set abs zero, 
        (3) moving by center counts back, 
        (4) set abs zero"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"setref": await app.driver.setaxisref()})
        finished_act = await active.finish()
        return finished_act.as_dict()

    # parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(platexy).tolist())}
    @app.post(f"/{servKey}/toMotorXY")
    async def transform_platexy_to_motorxy(request: Request, 
        platexy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Converts plate to motor xy"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        motorxy = app.driver.transform.transform_platexy_to_motorxy(**A.action_params)
        await active.enqueue_data(motorxy)
        finished_act = await active.finish()
        return finished_act.as_dict()

    # parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(motorxy).tolist())}
    @app.post(f"/{servKey}/toPlateXY")
    async def transform_motorxy_to_platexy(request: Request, 
        motorxy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Converts motor to plate xy"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        platexy = app.driver.transform.transform_motorxy_to_platexy(**A.action_params)
        await active.enqueue_data(platexy)
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/MxytoMPlate")
    async def MxytoMPlate(request: Request, 
        Mxy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """removes Minstr from Msystem to obtain Mplate for alignment"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        Mplate = app.driver.transform.get_Mplate_Msystem(**A.action_params)
        await active.enqueue_data(Mplate)
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/download_alignmentmatrix")
    async def download_alignmentmatrix(request: Request, 
        Mxy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Get current in use Alignment from motion server"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        updsys = app.driver.transform.update_Mplatexy(**A.action_params)
        await active.enqueue_data(updsys)
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/upload_alignmentmatrix")
    async def upload_alignmentmatrix(request: Request, action_dict: Optional[dict] = None):
        """Send new Alignment to motion server"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        alignmentmatrix = app.driver.transform.get_Mplatexy().tolist()
        await active.enqueue_data(alignmentmatrix)
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/move")
    async def move(request: Request, 
        multi_d_mm: Optional[Union[List[float], float]] = None,
        multi_axis: Optional[Union[List[str], str]] = None,
        speed: Optional[int] = None,
        mode: Optional[move_modes] = "relative",
        transformation: Optional[
            transformation_mode
        ] = "motorxy",  # default, nothing to do
        action_dict: Optional[dict] = None,
    ):
        """Move a apecified {axis} by {d_mm} distance at {speed} using {mode} i.e. relative.
        Use Rx, Ry, Rz and not in combination with x,y,z only in motorxy.
        No z, Rx, Ry, Rz when platexy selected."""
        A = await setupAct(action_dict, request, locals())
        if 'speed' not in A.action_params.keys():
            A.action_params['speed'] = app.base.server_cfg['params']['def_speed_count_sec']
        active = await app.base.contain_action(A)
        # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x
        stopping = False
        # TODO: no same axis in sequence

        move_response = await app.driver.motor_move(**A.action_params)
        await active.enqueue_data(move_response)
        if move_response["err_code"]:
            await active.set_error(f"{move_response['err_code']}")
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/disconnect")
    async def disconnect(request: Request, action_dict: Optional[dict] = None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.motor_disconnect())
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/query_positions")
    async def query_positions(request: Request, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/query/positions
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.query_axis_position(await app.driver.get_all_axis()))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/query_position")
    async def query_position(request: Request, 
        multi_axis: Optional[Union[List[str], str]] = None, action_dict: Optional[dict] = None
    ):
        # http://127.0.0.1:8001/motor/query/position?axis=x
        A = await setupAct(action_dict, request, locals())
        active = app.base.contain_action(A)
        await active.enqueue_data(await app.driver.query_axis_position(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/query_moving")
    async def query_moving(request: Request, 
        multi_axis: Optional[Union[List[str], str]] = None, action_dict: Optional[dict] = None
    ):
        # http://127.0.0.1:8001/motor/query/moving?axis=x
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.query_axis_moving(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/off")
    async def axis_off(request: Request, multi_axis: Optional[Union[List[str], str]] = None, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/off?axis=x
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.motor_off(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/on")
    async def axis_on(request: Request, multi_axis: Optional[Union[List[str], str]] = None, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/on?axis=x
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.motor_on(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/stop")
    async def stop(request: Request, action_dict: Optional[dict] = None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(
            await app.driver.motor_off(await app.driver.get_all_axis())
        )
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/reset")
    async def reset(request: Request, action_dict: Optional[dict] = None):
        """resets galil device. only for emergency use!"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(
            await app.driver.motor_off(await app.driver.reset())
        )
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/estop")
    async def estop(request: Request, switch: Optional[bool] = True, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/stop
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.estop_axis(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post("/shutdown")
    def post_shutdown():
        print(" ... motion shutdown ###")
        app.driver.shutdown_event()

    #    shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        global galil_motion_running
        galil_motion_running = False
        app.driver.shutdown_event()

    return app
