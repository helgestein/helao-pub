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
        config, servKey, servKey, "Instrument alignment server", version=2.0, driver_class=aligner
    )

    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_get_position")
    async def private_align_get_position():
        """Return the current motor position"""
        # gets position of all axis, but use only axis defined in aligner server params
        # can also easily be 3d axis (but not implemented yet so only 2d for now)
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_align_get_position")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={},
            data=await align.get_position(),
        )
        await stat.set_idle(uuid, "private_align_get_position")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_move")
    async def private_align_move(
        d_mm: str,
        axis: str,
        speed: int = None,
        mode: move_modes = "relative"
    ):
        stopping = False
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_align_move")
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
            data=await align.move(d_mm, axis, speed, mode),
        )
        await stat.set_idle(uuid, "private_align_move")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/MxytoMPlate")
    async def private_MxytoMPlate(Mxy):
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_MxytoMPlate")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "MxytoMPlate",
                        },
            data=await align.MxytoMPlate(Mxy),
        )
        await stat.set_idle(uuid, "private_MxytoMPlate")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toPlateXY")
    async def private_toPlateXY(motorxy):
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_toPlateXY")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "toPlateXY",
                        "plateid": align.plateid,
                        },
            data=await align.motor_to_platexy(motorxy),
        )
        await stat.set_idle(uuid, "private_toPlateXY")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/toMotorXY")
    async def private_toMotorXY(platexy):
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_toMotorXY")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "toMotorXY",
                        "plateid": align.plateid,
                        },
            data=await align.plate_to_motorxy(platexy),
        )
        await stat.set_idle(uuid, "private_toMotorXY")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/align_get_PM")
    async def private_align_get_PM():
        """Returns the PM for the alignment Visualizer"""
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_align_get_PM")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "get_PM",
                        "plateid": align.plateid,
                        },
            data=await align.get_PM(),
        )
        await stat.set_idle(uuid, "private_align_get_PM")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/ismoving")
    async def private_align_ismoving(axis: str = 'xy'):
        """check if motor is moving"""
        uuid = getuid(servKey)
        await stat.set_run(uuid, "private_ismoving")
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "align_ismoving",
                        "axis": axis
                        },
            data=await align.ismoving(axis),
        )
        await stat.set_idle(uuid, "private_ismoving")
        return retc


    # only for alignment bokeh server
    @app.post(f"/{servKey}/private/send_alignment")
    async def private_align_send_alignment(Transfermatrix: str, oldTransfermatrix: str, errorcode: str):
        """the bokeh server will send its Transfermatrix back with this"""
        await stat.set_run()
        retc = return_class(
            measurement_type="alignment_command",
            parameters={
                "command": "private_align_send_alignment",
            },
            data= {'err_code':errorcode,
                'Transfermatrix':Transfermatrix,
                'init_Transfermatrix':oldTransfermatrix
                },
        )
        # saving params from bokehserver so we can send them back
        align.newTransfermatrix = Transfermatrix
        align.errorcode = errorcode
        # signal to other function that we are done
        align.aligning = False
        print("received new alignment")
        await stat.set_idle()
        return retc # should not need that but we simply send the same data back to signal success


    @app.on_event("startup")
    def startup_event():
        global align
        align = aligner(S.params, C)
        global stat
        stat = StatusHandler()
        global wsstatus
        wsstatus = wsConnectionManager()


    @app.websocket(f"/{servKey}/ws_status")
    async def websocket_status(websocket: WebSocket):
        await wsstatus.send(websocket, stat.q, 'aligner_status')


    @app.post(f"/{servKey}/get_status")
    def status_wrapper():
        return stat.dict


    # TODO: alignment FastAPI and bokeh server are linked
    # should motor server and data server be parameters?
    # TODO: add mode to get Transfermatrix from Database?
    @app.post(f"/{servKey}/get_alignment")
    async def get_alignment(plateid: str,
                            motor: str="motor",#align.config_dict['motor_server'], # default motor server in config 
    #                        visualizer: str=align.config_dict['vis_server'], # default visualizer in config
                            data: str="data",#align.config_dict['data_server'] # default data server in config
                            action_params = ''
                            ):
        """Starts alignment process and returns TransferMatrix"""
        print('Getting alignment for:', plateid)
        
        await stat.set_run()
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "get_alignment",
                        "plateid": plateid,
                        "motor": motor,
                        "data": data,
    #                    "visualizer":visualizer
                        },
            data={"TransferMatrix":await align.get_alignment(plateid, motor, data)},
        )
        await stat.set_idle()
        return retc



    # gets status and Transfermatrix
    # for new Matrix, a new alignment process needs to be started via
    # get_alignment
    # when align_status is then true the Matrix is valid, else it will return the initial one
    @app.post(f"/{servKey}/align_status")
    async def align_status(action_params = ''):
        """Return status of current alignment"""
        # True: alignment is running, False: no alignment running
        await stat.set_run()
        retc = return_class(
            measurement_type="alignment_command",
            parameters={"command": "get_PM",
                        },
            data={"aligning": await align.is_aligning(), # true when in progress, false otherwise
                "Transfermatrix": align.newTransfermatrix,
                "plateid": align.plateid,
                "err_code": align.errorcode,
                "motor_server": align.motorserv,
                "data_server": align.dataserv
                },
        )
        await stat.set_idle()
        return retc


    @app.post('/endpoints')
    def get_all_urls():
        url_list = []
        for route in app.routes:
            routeD = {'path': route.path,
                    'name': route.name
                    }
            if 'dependant' in dir(route):
                flatParams = get_flat_params(route.dependant)
                paramD = {par.name: {
                    'outer_type': str(par.outer_type_).split("'")[1],
                    'type': str(par.type_).split("'")[1],
                    'required': par.required,
                    'shape': par.shape,
                    'default': par.default
                } for par in flatParams}
                routeD['params'] = paramD
            else:
                routeD['params'] = []
            url_list.append(routeD)
        return url_list


    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()


    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
