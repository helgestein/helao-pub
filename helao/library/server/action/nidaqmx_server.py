# NIdaqmx server
# https://nidaqmx-python.readthedocs.io/en/latest/task.html
# http://127.0.0.1:8006/docs#/default
# https://readthedocs.org/projects/nidaqmx-python/downloads/pdf/stable/


# TODO:
# done - add wsdata with buffering for visualizers
# - add wsstatus
# - test what happens if NImax broswer has nothing configured and only lists the device
# done - Current and voltage stream with interrut handler?
# - create tasks for action library
# - handshake as stream with interrupt

from importlib import import_module

from helao.core.server import Action, makeActServ
from helao.library.driver.nidaqmx_driver import cNIMAX


def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config
    C = config["servers"]
    S = C[servKey]

    app = makeActServ(
        config, servKey, servKey, "NIdaqmx server", version=2.0, driver_class=cNIMAX
    )


    @app.post(f"/{servKey}/run_task_GasFlowValves")
    async def run_task_GasFlowValves(valves: str, on: bool = True, action_params = ''):
        """Provide list of Valves (number) separated by ,"""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_GasFlowValves",
                        "parameters": {
                            "valves": valves,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_GasFlowValves(valves, on),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_Master_Cell_Select")
    async def run_task_Master_Cell_Select(cells: str, on: bool = True, action_params = ''):
        """Provide list of Cells separated by ,"""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_Master_Cell_Select",
                        "parameters": {
                            "cells": cells,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_Master_Cell_Select(cells, on),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_Active_Cells_Selection")
    async def run_task_Active_Cells_Selection(cells: str, on: bool = True, action_params = ''):
        """Provide list of Cells (number) separated by ,"""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_Active_Cells_Selection",
                        "parameters": {
                            "cells": cells,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_Active_Cells_Selection(cells, on),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_Pumps")
    async def run_task_Pumps(pumps: pumpitems = 'PeriPump', on: bool = True, action_params = ''):
        """Provide list of Pumps separated by ,"""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_Pumps",
                        "parameters": {
                            "pumps": pumps,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_Pumps(pumps, on),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_FSWBCD")
    async def run_task_FSWBCD(BCDs: str, on: bool = True, action_params = ''):
        """Provide list of Pumps separated by ,"""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_FSWBCD",
                        "parameters": {
                            "BCD": BCDs,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_FSWBCD(BCDs, on),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_FSW_error")
    async def run_task_FSW_error(action_params = ''):
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_FSW_error",
                        "parameters": {
                            },
                        },
            data=await app.driver.run_task_getFSW('Error'),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/run_task_FSW_done")
    async def run_task_FSW_done(action_params = ''):
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_FSW_done",
                        "parameters": {
                            },
                        },
            data=await app.driver.run_task_getFSW('Done'),
        )
        await stat.set_idle()
        return retc


    # @app.post(f"/{servKey}/run_task_RSH_TTL_handshake")
    # async def run_task_RSH_TTL_handshake(action_params = ''):
    #     await stat.set_run()
    #     retc = return_class(
    #         measurement_type="NImax_command",
    #         parameters={
    #                     "command": "run_RSH_TTL_handshake",
    #                     "parameters": {
    #                         },
    #                     },
    #         data=await app.driver.run_task_RSH_TTL_handshake(),
    #     )
    #     await stat.set_idle()
    #     return retc


    @app.post(f"/{servKey}/run_task_Cell_IV")
    async def run_task_Cell_IV(on: bool = True,tstep: float = 1.0, action_params = ''):
        """Get the current/voltage measurement for each cell.
        Only active cells are plotted in visualizer."""
        await stat.set_run()
        retc = return_class(
            measurement_type="NImax_command",
            parameters={
                        "command": "run_task_Cell_IV",
                        "parameters": {
                            "tstep": tstep,
                            "ON": on
                            },
                        },
            data=await app.driver.run_task_Cell_IV(on, tstep),
        )
        await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/stop")
    async def stop(action_params = ''):
        """Stops measurement in a controlled way."""
        await stat.set_run()
        retc = return_class(
            measurement_type="gamry_command",
            parameters={"command": "stop"},
            data = await app.driver.stop(),
        )
        # will be set within the driver
        #await stat.set_idle()
        return retc


    @app.post(f"/{servKey}/estop")
    async def estop(switch: bool = True, action_params = ''):
        """Same as stop, but also sets estop flag."""
        await stat.set_run()
        retc = return_class(
            measurement_type="gamry_command",
            parameters={"command": "estop"},
            data = await app.driver.estop(switch),
        )
        # will be set within the driver
        #await stat.set_estop()
        return retc


    @app.websocket(f"/{servKey}/ws_data_settings")
    async def websocket_data_setings(websocket: WebSocket):
        await wsdatasettings.send(websocket, app.driver.qsettings, 'NImax_data_settings')


    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()


    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app