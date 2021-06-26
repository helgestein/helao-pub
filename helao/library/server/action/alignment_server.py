# Instrument Alignment server
# talks with specified motor server and provides input to separate user interface server

# TODO: add checks against align.aligning

from typing import Optional
from importlib import import_module

from helao.core.server import Action, makeActServ
from helao.library.driver.alignment_driver import aligner
from helao.library.driver.galil_driver import move_modes


def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config
    C = config["servers"]
    S = C[servKey]

    app = makeActServ(
        config,
        servKey,
        servKey,
        "Instrument alignment server",
        version=2.0,
        driver_class=aligner,
    )

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_get_position")
    async def private_align_get_position():
        """Return the current motor position"""
        # gets position of all axis, but use only axis defined in aligner server params
        # can also easily be 3d axis (but not implemented yet so only 2d for now)
        retc = return_class(
            measurement_type="alignment_command",
            parameters={},
            data=await app.driver.get_position(),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_move")
    async def private_align_move(
        d_mm: str, axis: str, speed: int = None, mode: move_modes = "relative"
    ):
        stopping = False
        retc = return_class(
            measurement_type="alignment_command",
            parameters={
                "command": "move",
                #            "motor":"def"},
                "d_mm": d_mm,
                "axis": axis,
                "speed": speed,
                "mode": mode,
                "stopping": stopping,
            },
            data=await app.driver.move(d_mm, axis, speed, mode),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/MxytoMPlate")
    async def private_MxytoMPlate(Mxy):
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "MxytoMPlate",},
            data=await app.driver.MxytoMPlate(Mxy),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toPlateXY")
    async def private_toPlateXY(motorxy):
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "toPlateXY", "plateid": app.driver.plateid,},
            data=await app.driver.motor_to_platexy(motorxy),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toMotorXY")
    async def private_toMotorXY(platexy):
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "toMotorXY", "plateid": app.driver.plateid,},
            data=await app.driver.plate_to_motorxy(platexy),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_get_PM")
    async def private_align_get_PM():
        """Returns the PM for the alignment Visualizer"""
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "get_PM", "plateid": app.driver.plateid,},
            data=await app.driver.get_PM(),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/ismoving")
    async def private_align_ismoving(axis: str = "xy"):
        """check if motor is moving"""
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "align_ismoving", "axis": axis},
            data=await app.driver.ismoving(axis),
        )
        return retc

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/send_alignment")
    async def private_align_send_alignment(
        Transfermatrix: str, oldTransfermatrix: str, errorcode: str
    ):
        """the bokeh server will send its Transfermatrix back with this"""
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "private_align_send_alignment",},
            data={
                "err_code": errorcode,
                "Transfermatrix": Transfermatrix,
                "init_Transfermatrix": oldTransfermatrix,
            },
        )
        # saving params from bokehserver so we can send them back
        app.driver.newTransfermatrix = Transfermatrix
        app.driver.errorcode = errorcode
        # signal to other function that we are done
        app.driver.aligning = False
        print("received new alignment")
        return retc  # should not need that but we simply send the same data back to signal success

    # TODO: alignment FastAPI and bokeh server are linked
    # should motor server and data server be parameters?
    # TODO: add mode to get Transfermatrix from Database?
    @app.post(f"/{servKey}/get_alignment")
    async def get_alignment(
        plateid: str,
        motor: str = "motor",  # align.config_dict['motor_server'], # default motor server in config
        #                        visualizer: str=align.config_dict['vis_server'], # default visualizer in config
        data: str = "data",  # align.config_dict['data_server'] # default data server in config
        action_params="",
    ):
        """Starts alignment process and returns TransferMatrix"""
        print("Getting alignment for:", plateid)

        retc = return_class(
            measurement_type="alignment_command",
            parameters={
                "command": "get_alignment",
                "plateid": plateid,
                "motor": motor,
                "data": data,
                #                    "visualizer":visualizer
            },
            data={
                "TransferMatrix": await app.driver.get_alignment(plateid, motor, data)
            },
        )
        return retc

    # gets status and Transfermatrix
    # for new Matrix, a new alignment process needs to be started via
    # get_alignment
    # when align_status is then true the Matrix is valid, else it will return the initial one
    @app.post(f"/{servKey}/align_status")
    async def align_status(action_params=""):
        """Return status of current alignment"""
        # True: alignment is running, False: no alignment running
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "get_PM",},
            data={
                "aligning": await app.driver.is_aligning(),  # true when in progress, false otherwise
                "Transfermatrix": app.driver.newTransfermatrix,
                "plateid": app.driver.plateid,
                "err_code": app.driver.errorcode,
                "motor_server": app.driver.motorserv,
                "data_server": app.driver.dataserv,
            },
        )
        return retc

    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
