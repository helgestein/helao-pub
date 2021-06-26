from importlib import import_module

from helao.core.server import Action, makeActServ
from helao.library.driver.PAL_driver import cPAL


def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config
    C = config["servers"]
    S = C[servKey]

    app = makeActServ(
        config,
        servKey,
        servKey,
        "PAL Autosampler Server",
        version=2.0,
        driver_class=cPAL,
    )

    @app.post(f"/{servKey}/reset_PAL_system_vial_table")
    async def reset_PAL_system_vial_table(action_params=""):
        """Resets app.driver vial table. But will make a full dump to CSV first."""
        retc = return_class(
            measurement_type="PAL_command",
            parameters={"command": "reset_PAL_system_vial_table"},
            data={"reset": await app.driver.reset_PAL_system_vial_table()},
        )
        return retc

    @app.post(f"/{servKey}/update_PAL_system_vial_table")
    async def update_PAL_system_vial_table(
        vial: int,
        vol_mL: float,
        liquid_sample_no: int,
        tray: int = 2,
        slot: int = 1,
        action_params="",
    ):
        """Updates app.driver vial Table. If sucessful (vial-slot was empty) returns True, else it returns False."""
        retc = return_class(
            measurement_type="PAL_command",
            parameters={"command": "update_PAL_system_vial_table"},
            data={
                "update": await app.driver.update_PAL_system_vial_table(
                    tray, slot, vial, vol_mL, liquid_sample_no
                )
            },
        )
        return retc

    @app.post(f"/{servKey}/get_vial_holder_table")
    async def get_vial_holder_table(tray: int = 2, slot: int = 1, action_params=""):
        retc = return_class(
            measurement_type="PAL_command",
            parameters={"command": "get_vial_holder_table"},
            data={"vial_table": await app.driver.get_vial_holder_table(tray, slot)},
        )
        return retc

    @app.post(f"/{servKey}/write_vial_holder_table_CSV")
    async def write_vial_holder_table_CSV(
        tray: int = 2, slot: int = 1, action_params=""
    ):
        retc = return_class(
            measurement_type="PAL_command",
            parameters={"command": "get_vial_holder_table"},
            data={
                "vial_table": await app.driver.get_vial_holder_table(
                    tray, slot, csv=True
                )
            },
        )
        return retc

    @app.post(f"/{servKey}/get_new_vial_position")
    async def get_new_vial_position(req_vol: float = 2.0, action_params=""):
        """Returns an empty vial position for given max volume.\n
        For mixed vial sizes the req_vol helps to choose the proper vial for sample volume.\n
        It will select the first empty vial which has the smallest volume that still can hold req_vol"""
        retc = return_class(
            measurement_type="PAL_command",
            parameters={"command": "get_new_vial_position"},
            data={"position": await app.driver.get_new_vial_position(req_vol)},
        )
        return retc

    # relay_actuation_test2.cam
    # lcfc_archive.cam
    # lcfc_fill.cam
    # lcfc_fill_hardcodedvolume.cam
    @app.post(f"/{servKey}/run_method")
    async def run_method(
        liquid_sample_no: int,
        method: app.drivermethods = app.drivermethods.fillfixed,  # lcfc_fill_hardcodedvolume.cam',
        tool: str = "LS3",
        source: str = "electrolyte_res",
        volume_uL: int = 500,  # uL
        #               dest_tray: int = 2, # will be filled via call to vial warehouse table
        #               dest_slot: int = 1, # will be filled via call to vial warehouse table
        #               dest_vial: int = 1, # will be filled via call to vial warehouse table
        # logfile: str = 'TestLogFile.txt',
        totalvials: int = 1,
        sampleperiod: float = 0.0,
        spacingmethod: Spacingmethod = "linear",
        spacingfactor: float = 1.0,
        action_params="",  # optional parameters
    ):

        runparams = action_runparams(
            uid=getuid(servKey), name="run_method", action_params=action_params
        )
        retc = return_class(
            measurement_type="PAL_command",
            parameters={
                "command": "sendcommand",
                "parameters": {
                    "liquid_sample_no": liquid_sample_no,
                    "PAL_method": method.name,
                    "PAL_tool": tool,
                    "PAL_source": source,
                    "PAL_volume_uL": volume_uL,
                    # 'PAL_dest_tray': dest_tray, # will be filled via call to vial warehouse table
                    # 'PAL_dest_slot': dest_slot, # will be filled via call to vial warehouse table
                    # 'PAL_dest_vial': dest_vial, # will be filled via call to vial warehouse table
                    #'logfile': logfile,
                    "totalvials": totalvials,
                    "sampleperiod": sampleperiod,
                    "spacingmethod": spacingmethod,
                    "spacingfactor": spacingfactor,
                },
            },
            data=await app.driver.initcommand(
                cPALparams(
                    liquid_sample_no=liquid_sample_no,
                    method=method,
                    tool=tool,
                    source=source,
                    volume_uL=volume_uL,
                    dest_tray=None,  # dest_tray, # will be filled via call to vial warehouse table
                    dest_slot=None,  # dest_slot, # will be filled via call to vial warehouse table
                    dest_vial=None,  # dest_vial, # will be filled via call to vial warehouse table
                    # logfile,
                    totalvials=totalvials,
                    sampleperiod=sampleperiod,
                    spacingmethod=spacingmethod,
                    spacingfactor=spacingfactor,
                ),
                runparams,
            ),
        )
        # will be set within the driver
        return retc

    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
