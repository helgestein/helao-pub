# shell: uvicorn motion_server:app --reload
""" A FastAPI service definition for a motion/IO server, e.g. Galil.

The motion/IO service defines RESTful methods for sending commmands and retrieving data
from a motion controller driver class such as 'galil_driver' or 'galil_simulate' using
FastAPI. The methods provided by this service are not device-specific. Appropriate code
must be written in the driver class to ensure that the service methods are generic, i.e.
calls to 'motion.*' are not device-specific. Currently inherits configuration from
driver code, and hard-coded to use 'galil' class (see "__main__").
"""

from typing import Optional, Union, List
from importlib import import_module
from fastapi import Request
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
        print("Galil I/O simulator loaded.")
        from helao.library.driver.galil_simulate import galil
    else:
        from helao.library.driver.galil_driver import galil

    app = makeActServ(
        config, servKey, servKey, "Galil IO server", version=2.0, driver_class=galil
    )

    @app.post(f"/{servKey}/query_analog_in")
    async def read_analog_in(
        request: Request, multi_port: Optional[Union[List[int], int]] = None, action_dict: Optional[dict] = None
    ):
        # http://127.0.0.1:8001/io/query/analog_in?port=0
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.read_analog_in(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/query_digital_in")
    async def read_digital_in(
        request: Request, multi_port: Optional[Union[List[int], int]] = None, action_dict: Optional[dict] = None
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.read_digital_in(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/query_digital_out")
    async def read_digital_out(
        request: Request, multi_port: Optional[Union[List[int], int]] = None, action_dict: Optional[dict] = None
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.read_digital_out(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/digital_out_on")
    async def set_digital_out_on(
        request: Request, multi_port: Optional[Union[List[int], int]] = None, action_dict: Optional[dict] = None
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.digital_out_on(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/digital_out_off")
    async def set_digital_out_off(
        request: Request, multi_port: Optional[Union[List[int], int]] = None, action_dict: Optional[dict] = None
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.digital_out_off(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/set_triggered_cycles")
    async def set_triggered_cycles(
        request: Request,
        trigger_port: Optional[int] = None,
        out_port: Optional[int] = None,
        t_cycle: Optional[int] = None,
        action_dict: Optional[dict] = None,
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.set_digital_cycle(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/analog_out")
    async def set_analog_out(
        request: Request,
        multi_port: Optional[Union[List[int], int]] = None,
        multi_value: Optional[Union[List[float], float]] = None,
        action_dict: Optional[dict] = None,
    ):
        # async def set_analog_out(handle: int, module: int, bitnum: int, value: float):
        # TODO
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.set_analog_out(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/inf_digi_cycles")
    async def inf_cycles(
        request: Request,
        time_on: Optional[float] = None,
        time_off: Optional[float] = None,
        port: Optional[int] = None,
        init_time: Optional[float] = None,
        action_dict: Optional[dict] = None,
    ):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.infinite_digital_cycles(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/break_inf_digi_cycles")
    async def break_inf_cycles(request: Request, action_dict: Optional[dict] = None):
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.break_infinite_digital_cycles())
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/reset")
    async def reset(request: Request, action_dict: Optional[dict] = None):
        """resets galil device. only for emergency use!"""
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.reset())
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post(f"/{servKey}/estop")
    async def estop(request: Request, switch: Optional[bool] = True, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/stop
        A = setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.estop_io(switch))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post("/shutdown")
    def post_shutdown():
        pass

    #    shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        app.driver.shutdown_event()

    return app
