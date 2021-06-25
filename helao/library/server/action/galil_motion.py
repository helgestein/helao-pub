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
from typing import Optional

from helao.core.model import move_modes, transformation_mode
from helao.core.server import Action, makeActServ


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
    async def setmotionref(action_dict: Optional[dict] = None):
        """Set the reference position for xyz by 
        (1) homing xyz, 
        (2) set abs zero, 
        (3) moving by center counts back, 
        (4) set abs zero"""
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "setmotionref"
        active = await app.base.contain_action(A)
        await active.enqueue_data({"setref": await app.driver.setaxisref()})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    # parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(platexy).tolist())}
    @app.post(f"/{servKey}/toMotorXY")
    async def transform_platexy_to_motorxy(
        platexy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Converts plate to motor xy"""
        if action_dict:
            A = Action(action_dict)
            platexy = A.action_params["platexy"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "toMotorXY"
            A.action_params["platexy"] = platexy
        active = await app.base.contain_action(A)
        motorxy = app.driver.transform.transform_platexy_to_motorxy(json.loads(platexy))
        await active.enqueue_data({"motorxy": json.dumps(motorxy.tolist())})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    # parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(motorxy).tolist())}
    @app.post(f"/{servKey}/toPlateXY")
    async def transform_motorxy_to_platexy(
        motorxy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Converts motor to plate xy"""
        if action_dict:
            A = Action(action_dict)
            platexy = A.action_params["motorxy"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "toMotorXY"
            A.action_params["motorxy"] = motorxy
        active = await app.base.contain_action(A)
        platexy = app.driver.transform.transform_motorxy_to_platexy(json.loads(motorxy))
        await active.enqueue_data({"platexy": json.dumps(platexy.tolist())})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/MxytoMPlate")
    async def MxytoMPlate(
        Mxy: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """removes Minstr from Msystem to obtain Mplate for alignment"""
        if action_dict:
            A = Action(action_dict)
            Mxy = A.action_params["Mxy"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "MxytoMPlate"
            A.action_params["Mxy"] = Mxy
        active = await app.base.contain_action(A)
        Mplate = app.driver.transform.get_Mplate_Msystem(json.loads(Mxy))
        await active.enqueue_data({"Mplate": json.dumps(Mplate.tolist())})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/download_alignmentmatrix")
    async def download_alignmentmatrix(
        newxyTransfermatrix: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        """Get current in use Alignment from motion server"""
        if action_dict:
            A = Action(action_dict)
            newxyTransfermatrix = A.action_params["newxyTransfermatrix"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "download_alignmentmatrix"
            A.action_params["newxyTransfermatrix"] = newxyTransfermatrix
        active = await app.base.contain_action(A)
        app.driver.transform.update_Mplatexy(json.loads(newxyTransfermatrix))
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/upload_alignmentmatrix")
    async def upload_alignmentmatrix(action_dict: Optional[dict] = None):
        """Send new Alignment to motion server"""
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "download_alignmentmatrix"
        active = await app.base.contain_action(A)
        alignmentmatrix = json.dumps(app.driver.transform.get_Mplatexy.tolist())
        await active.enqueue_data({"alignmentmatrix": alignmentmatrix})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/move")
    async def move(
        d_mm: Optional[str] = None,
        axis: Optional[str] = None,
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
        if action_dict:
            A = Action(action_dict)
            d_mm = A.action_params["d_mm"]
            axis = A.action_params["axis"]
            speed = A.action_params["speed"]
            mode = A.action_params["mode"]
            transformation = A.action_params["transformation"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "move"
            A.action_params["d_mm"] = d_mm
            A.action_params["axis"] = axis
            A.action_params["speed"] = speed
            A.action_params["mode"] = mode
            A.action_params["transformation"] = transformation
        active = await app.base.contain_action(A)

        # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x
        stopping = False
        # TODO: no same axis in sequence

        # for multi axis movement, we need to split d_mm and axis into lists
        # (1) find separator and split it, else assume single axis move
        sepvals = [" ", ",", "\t", ";", "::", ":"]
        new_axis = None
        new_d_mm = None

        for sep in sepvals:
            if not (d_mm.find(sep) == -1) and not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                new_d_mm = [float(item) for item in d_mm.split(sep)]
                break

        # single axis
        if new_d_mm == None:
            new_axis = axis
            new_d_mm = float(d_mm)

        # convert single axis move to list
        if type(new_d_mm) is not list:
            new_axis = [new_axis]
            new_d_mm = [new_d_mm]

        # need to get absolute motor position first
        tmpmotorpos = await app.driver.query_axis_position(
            await app.driver.get_all_axis()
        )
        print(" ... current absolute motor positions:", tmpmotorpos)
        # don't use dicts as we do math on these vectors
        current_positionvec = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # x, y, z, Rx, Ry, Rz
        # map the request to this
        #    req_positionvec = [0.0,0.0,0.0,0.0,0.0,0.0] # x, y, z, Rx, Ry, Rz
        req_positionvec = [None, None, None, None, None, None]  # x, y, z, Rx, Ry, Rz

        reqdict = dict(zip(new_axis, new_d_mm))
        print(" ... requested position (", mode, "): ", reqdict)

        for idx, ax in enumerate(["x", "y", "z", "Rx", "Ry", "Rz"]):
            if ax in tmpmotorpos["ax"]:
                # for current_positionvec
                current_positionvec[idx] = tmpmotorpos["position"][
                    tmpmotorpos["ax"].index(ax)
                ]
                # for req_positionvec
                if ax in reqdict:
                    req_positionvec[idx] = reqdict[ax]

        print(" ... motor position vector:", current_positionvec[0:3])
        print(" ... requested position vector (", mode, ")", req_positionvec)

        if transformation == transformation_mode.motorxy:
            # nothing to do
            print("motion: got motorxy (", mode, "), no transformation necessary")
        elif transformation == transformation_mode.platexy:
            print("motion: got platexy (", mode, "), converting to motorxy")
            motorxy = [0, 0, 1]
            motorxy[0] = current_positionvec[0]
            motorxy[1] = current_positionvec[1]
            current_platexy = app.driver.transform.transform_motorxy_to_platexy(motorxy)
            # transform.transform_motorxyz_to_instrxyz(current_positionvec[0:3])
            print(" ... current plate position (calc from motor):", current_platexy)
            if mode == move_modes.relative:
                new_platexy = [0, 0, 1]

                if req_positionvec[0] is not None:
                    new_platexy[0] = current_platexy[0] + req_positionvec[0]
                else:
                    new_platexy[0] = current_platexy[0]

                if req_positionvec[1] is not None:
                    new_platexy[1] = current_platexy[1] + req_positionvec[1]
                else:
                    new_platexy[1] = current_platexy[1]

                print(" ... new platexy (abs)", new_platexy)
                new_motorxy = app.driver.transform.transform_platexy_to_motorxy(
                    new_platexy
                )
                print(" ... new motorxy (abs):", new_motorxy)
                new_axis = ["x", "y"]
                new_d_mm = [d for d in new_motorxy[0:2]]
                mode = move_modes.absolute
            elif mode == move_modes.absolute:
                new_platexy = [0, 0, 1]

                if req_positionvec[0] is not None:
                    new_platexy[0] = req_positionvec[0]
                else:
                    new_platexy[0] = current_platexy[0]

                if req_positionvec[1] is not None:
                    new_platexy[1] = req_positionvec[1]
                else:
                    new_platexy[1] = current_platexy[1]

                print(" ... new platexy (abs)", new_platexy)
                new_motorxy = app.driver.transform.transform_platexy_to_motorxy(
                    new_platexy
                )
                print(" ... new motorxy (abs):", new_motorxy)
                new_axis = ["x", "y"]
                new_d_mm = [d for d in new_motorxy[0:2]]

            elif mode == move_modes.homing:
                # not coordinate conversoion needed as these are not used (but length is still checked)
                pass

            xyvec = [0, 0, 1]
            for i, ax in enumerate(new_axis):
                if ax == "x":
                    xyvec[0] = new_d_mm[0]
                if ax == "y":
                    xyvec[1] = new_d_mm[1]
        elif transformation == transformation_mode.instrxy:
            print(" ................mode", mode)
            print("motion: got instrxyz (", mode, "), converting to motorxy")
            current_instrxyz = app.driver.transform.transform_motorxyz_to_instrxyz(
                current_positionvec[0:3]
            )
            print(
                " ... current instrument position (calc from motor):", current_instrxyz
            )
            if mode == move_modes.relative:
                new_instrxyz = current_instrxyz
                for i in range(3):
                    if req_positionvec[i] is not None:
                        new_instrxyz[i] = new_instrxyz[i] + req_positionvec[i]
                    else:
                        new_instrxyz[i] = new_instrxyz[i]
                print(" ... new instrument position (abs):", new_instrxyz)
                # transform from instrxyz to motorxyz
                new_motorxyz = app.driver.transform.transform_instrxyz_to_motorxyz(
                    new_instrxyz[0:3]
                )
                print(" ... new motor position (abs):", new_motorxyz)
                new_axis = ["x", "y", "z"]
                new_d_mm = [d for d in new_motorxyz[0:3]]
                mode = move_modes.absolute
            elif mode == move_modes.absolute:
                new_instrxyz = current_instrxyz
                for i in range(3):
                    if req_positionvec[i] is not None:
                        new_instrxyz[i] = req_positionvec[i]
                    else:
                        new_instrxyz[i] = new_instrxyz[i]
                print(" ... new instrument position (abs):", new_instrxyz)
                new_motorxyz = app.driver.transform.transform_instrxyz_to_motorxyz(
                    new_instrxyz[0:3]
                )
                print(" ... new motor position (abs):", new_motorxyz)
                new_axis = ["x", "y", "z"]
                new_d_mm = [d for d in new_motorxyz[0:3]]
            elif mode == move_modes.homing:
                # not coordinate conversoion needed as these are not used (but length is still checked)
                pass

        print(" ... final axis requested:", new_axis)
        print(" ... final d (", mode, ") requested:", new_d_mm)

        move_response = await app.driver.motor_move(new_d_mm, new_axis, speed, mode)
        await active.enqueue_data({"move": move_response})
        if move_response["err_code"]:
            await active.set_error()
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/disconnect")
    async def disconnect(action_dict: Optional[dict] = None):
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "disconnect"
        active = await app.base.contain_action(A)
        await active.enqueue_data({"disconnect": await app.driver.motor_disconnect()})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/query_positions")
    async def query_positions(action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/query/positions
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "query_positions"
        active = await app.base.contain_action(A)
        await active.enqueue_data(
            {
                "positions": await app.driver.query_axis_position(
                    await app.driver.get_all_axis()
                )
            }
        )
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/query_position")
    async def query_position(
        axis: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        # http://127.0.0.1:8001/motor/query/position?axis=x
        if action_dict:
            A = Action(action_dict)
            axis = A.action_params["axis"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "query_position"
            A.action_params["axis"] = axis
        active = await app.base.contain_action(A)
        sepvals = [" ", ",", "\t", ";", "::", ":"]
        new_axis = None
        for sep in sepvals:
            if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break
        # single axis
        if new_axis == None:
            new_axis = axis
        await active.enqueue_data(
            {"position": await app.driver.query_axis_position(new_axis)}
        )
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/query_moving")
    async def query_moving(
        axis: Optional[str] = None, action_dict: Optional[dict] = None
    ):
        # http://127.0.0.1:8001/motor/query/moving?axis=x
        if action_dict:
            A = Action(action_dict)
            axis = A.action_params["axis"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "query_moving"
            A.action_params["axis"] = axis
        active = await app.base.contain_action(A)
        sepvals = [" ", ",", "\t", ";", "::", ":"]
        new_axis = None
        for sep in sepvals:
            if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break
        # single axis
        if new_axis == None:
            new_axis = axis
        await active.enqueue_data(
            {"moving": await app.driver.query_axis_moving(new_axis)}
        )
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/off")
    async def axis_off(axis: Optional[str] = None, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/off?axis=x
        if action_dict:
            A = Action(action_dict)
            axis = A.action_params["axis"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "off"
            A.action_params["axis"] = axis
        active = await app.base.contain_action(A)
        sepvals = [" ", ",", "\t", ";", "::", ":"]
        new_axis = None
        for sep in sepvals:
            if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break
        # single axis
        if new_axis == None:
            new_axis = axis
        await active.enqueue_data({"off": await app.driver.motor_off(new_axis)})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/on")
    async def axis_on(axis: Optional[str] = None, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/on?axis=x
        if action_dict:
            A = Action(action_dict)
            axis = A.action_params["axis"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "on"
            A.action_params["axis"] = axis
        active = await app.base.contain_action(A)
        sepvals = [" ", ",", "\t", ";", "::", ":"]
        new_axis = None
        for sep in sepvals:
            if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break
        # single axis
        if new_axis == None:
            new_axis = axis
        await active.enqueue_data({"on": await app.driver.motor_on(new_axis)})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/stop")
    async def stop(action_dict: Optional[dict] = None):
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "stop"
        active = await app.base.contain_action(A)
        await active.enqueue_data(
            {"stop": await app.driver.motor_off(await app.driver.get_all_axis())}
        )
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/reset")
    async def reset(action_dict: Optional[dict] = None):
        """resets galil device. only for emergency use!"""
        if action_dict:
            A = Action(action_dict)
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "reset"
        active = await app.base.contain_action(A)
        await active.enqueue_data(
            {"reset": await app.driver.motor_off(await app.driver.reset())}
        )
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

    @app.post(f"/{servKey}/estop")
    async def estop(switch: Optional[bool] = True, action_dict: Optional[dict] = None):
        # http://127.0.0.1:8001/motor/set/stop
        if action_dict:
            A = Action(action_dict)
            switch = A.action_params["switch"]
        else:
            A = Action()
            A.action_server = servKey
            A.action_name = "estop"
            A.action_params["switch"]
        active = await app.base.contain_action(A)
        await active.enqueue_data({"estop": await app.driver.estop_axis(switch)})
        finished_act = await active.finish()
        finished_dict = finished_act.as_dict()
        del finished_act
        return finished_dict

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
