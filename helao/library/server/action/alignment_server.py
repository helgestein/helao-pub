# Instrument Alignment server
# talks with specified motor server and provides input to separate user interface server

# TODO: add checks against align.aligning

from typing import Optional, List, Union
from importlib import import_module
from fastapi import Request
from helao.core.server import makeActServ, setupAct
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
    async def private_align_get_position(request: Request, action_dict: Optional[dict] = None):
        """Return the current motor position"""
        # gets position of all axis, but use only axis defined in aligner server params
        # can also easily be 3d axis (but not implemented yet so only 2d for now)
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_position())
        finished_act = await active.finish()
        return finished_act.as_dict()

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_move")
    async def private_align_move(
        request: Request,
        multi_d_mm: Optional[Union[List[float], float]] = None,
        multi_axis: Optional[Union[List[str], str]] = None,
        speed: Optional[int] = None,
        mode: Optional[move_modes] = "relative",
        action_dict: Optional[dict] = None
    ):
        A = await setupAct(action_dict, request, locals())
        # A.action_params['stopping'] = False
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.move(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()
        

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/MxytoMPlate")
    async def private_MxytoMPlate(request: Request, Mxy: Optional[List[List[float]]], action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.MxytoMPlate(Mxy))
        finished_act = await active.finish()
        return finished_act.as_dict()
        

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toPlateXY")
    async def private_toPlateXY(request: Request, motorxy: Optional[List[List[float]]], action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.motor_to_platexy(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toMotorXY")
    async def private_toMotorXY(request: Request, platexy: Optional[List[List[float]]], action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.plate_to_motorxy(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_get_PM")
    async def private_align_get_PM(request: Request, action_dict: Optional[dict]=None):
        """Returns the PM for the alignment Visualizer"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_PM())
        finished_act = await active.finish()
        return finished_act.as_dict()

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/ismoving")
    async def private_align_ismoving(request: Request, axis: str="xy", action_dict: Optional[dict]=None):
        """check if motor is moving"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.ismoving(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/send_alignment")
    async def private_align_send_alignment(
        request: Request, Transfermatrix: Optional[List[List[int]]]=None, errorcode: Optional[str]=None, action_dict: Optional[dict]=None, 
    ):
        """the bokeh server will send its Transfermatrix back with this"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        # saving params from bokehserver so we can send them back
        app.driver.newTransfermatrix = Transfermatrix
        app.driver.errorcode = errorcode
        # signal to other function that we are done
        app.driver.aligning = False
        print("received new alignment")
        await active.enqueue_data("received new alignment")
        finished_act = await active.finish()
        return finished_act.as_dict()

    # TODO: alignment FastAPI and bokeh server are linked
    # should motor server and data server be parameters?
    # TODO: add mode to get Transfermatrix from Database?
    @app.post(f"/{servKey}/get_alignment")
    async def get_alignment(
        request: Request,
        plateid: Optional[str],
        motor: Optional[str] = "motor",  # align.config_dict['motor_server'], # default motor server in config
        data: Optional[str] = "data",  # align.config_dict['data_server'] # default data server in config
        action_dict: Optional[dict]=None,
    ):
        """Starts alignment process and returns TransferMatrix"""
        print("Getting alignment for:", plateid)
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_alignment(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    # gets status and Transfermatrix
    # for new Matrix, a new alignment process needs to be started via
    # get_alignment
    # when align_status is then true the Matrix is valid, else it will return the initial one
    @app.post(f"/{servKey}/align_status")
    async def align_status(request: Request, action_dict: Optional[dict]=None):
        """Return status of current alignment"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        align_status={
            "aligning": await app.driver.is_aligning(),  # true when in progress, false otherwise
            "Transfermatrix": app.driver.newTransfermatrix,
            "plateid": app.driver.plateid,
            "err_code": app.driver.errorcode,
            "motor_server": app.driver.motorserv,
            "data_server": app.driver.dataserv,
        }
        await active.enqueue_data(align_status)
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
