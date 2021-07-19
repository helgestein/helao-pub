from importlib import import_module

from helao.core.server import Action, makeActServ, setupAct
from helao.library.driver.PAL_driver import cPAL
from helao.library.driver.PAL_driver import PALmethods
from helao.library.driver.PAL_driver import Spacingmethod
from helao.library.driver.PAL_driver import PALtools


from fastapi import Request
from typing import Optional

def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config

    app = makeActServ(
        config,
        servKey,
        servKey,
        "PAL Autosampler Server",
        version=2.0,
        driver_class=cPAL,
    )

    @app.post(f"/{servKey}/reset_PAL_system_vial_table")
    async def reset_PAL_system_vial_table(
        request: Request, 
        action_dict: Optional[dict] = None
    ):
        """Resets app.driver vial table. But will make a full dump to CSV first."""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"reset":  await app.driver.reset_PAL_system_vial_table(A, active)})
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/update_PAL_system_vial_table")
    async def update_PAL_system_vial_table(
        request: Request, 
        vial: Optional[int] = None,
        vol_mL: Optional[float] = None,
        liquid_sample_no: Optional[int] = None,
        tray: Optional[int] = None,
        slot: Optional[int] = None,
        action_dict: Optional[dict] = None
    ):
        """Updates app.driver vial Table. If sucessful (vial-slot was empty) returns True, else it returns False."""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"update": await app.driver.update_PAL_system_vial_table(**A.action_params)})
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_vial_holder_table")
    async def get_vial_holder_table(
        request: Request, 
        tray: Optional[int] = 2, 
        slot: Optional[int] = 1, 
        action_dict: Optional[dict] = None
    ):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"vial_table": await app.driver.get_vial_holder_table(A, active)})
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/write_vial_holder_table_CSV")
    async def write_vial_holder_table_CSV(
        request: Request, 
        tray: Optional[int] = None,
        slot: Optional[int] = None,
        action_dict: Optional[dict] = None
    ):
        csv = True # signal subroutine to create a csv
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"vial_table": await app.driver.get_vial_holder_table(A, active)})
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_new_vial_position")
    async def get_new_vial_position(
        request: Request, 
        req_vol: Optional[float] = None,
        action_dict: Optional[dict] = None
    ):
        """Returns an empty vial position for given max volume.\n
        For mixed vial sizes the req_vol helps to choose the proper vial for sample volume.\n
        It will select the first empty vial which has the smallest volume that still can hold req_vol"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data({"vial_position": await app.driver.get_new_vial_position(**A.action_params)})
        finished_act = await active.finish()
        return finished_act.as_dict()


    # relay_actuation_test2.cam
    # lcfc_archive.cam
    # lcfc_fill.cam
    # lcfc_fill_hardcodedvolume.cam
    @app.post(f"/{servKey}/run_method")
    async def run_method(
        request: Request, 
        liquid_sample_no: Optional[int],
        method: Optional[PALmethods] = PALmethods.fillfixed,  # lcfc_fill_hardcodedvolume.cam',
        tool: Optional[PALtools] = PALtools.LS3,
        source: Optional[str] = "elec_res1",
        volume_uL: Optional[int] = 500,  # uL
        totalvials: Optional[int] = 1,
        sampleperiod: Optional[float] = 0.0,
        spacingmethod: Optional[Spacingmethod] = Spacingmethod.linear,
        spacingfactor: Optional[float] = 1.0,
        action_dict: Optional[dict] = None
    ):

        dest_tray=None  # dest_tray, # will be filled via call to vial warehouse table
        dest_slot=None  # dest_slot, # will be filled via call to vial warehouse table
        dest_vial=None  # dest_vial, # will be filled via call to vial warehouse table


        A = await setupAct(action_dict, request, locals())
        A.save_data = True
        active_dict = await app.driver.initcommand(A)
        return active_dict


        Vfinal = A.action_params["Vfinal"]



        # runparams = action_runparams(
        #     uid=getuid(servKey), name="run_method", action_params=action_params
        # )
        # retc = return_class(
        #     measurement_type="PAL_command",
        #     parameters={
        #         "command": "sendcommand",
        #         "parameters": {
        #             "liquid_sample_no": liquid_sample_no,
        #             "PAL_method": method.name,
        #             "PAL_tool": tool,
        #             "PAL_source": source,
        #             "PAL_volume_uL": volume_uL,
        #             # 'PAL_dest_tray': dest_tray, # will be filled via call to vial warehouse table
        #             # 'PAL_dest_slot': dest_slot, # will be filled via call to vial warehouse table
        #             # 'PAL_dest_vial': dest_vial, # will be filled via call to vial warehouse table
        #             #'logfile': logfile,
        #             "totalvials": totalvials,
        #             "sampleperiod": sampleperiod,
        #             "spacingmethod": spacingmethod,
        #             "spacingfactor": spacingfactor,
        #         },
        #     },
        #     data=await app.driver.initcommand(
        #         cPALparams(
        #             liquid_sample_no=liquid_sample_no,
        #             method=method,
        #             tool=tool,
        #             source=source,
        #             volume_uL=volume_uL,
        #             dest_tray=None,  # dest_tray, # will be filled via call to vial warehouse table
        #             dest_slot=None,  # dest_slot, # will be filled via call to vial warehouse table
        #             dest_vial=None,  # dest_vial, # will be filled via call to vial warehouse table
        #             # logfile,
        #             totalvials=totalvials,
        #             sampleperiod=sampleperiod,
        #             spacingmethod=spacingmethod,
        #             spacingfactor=spacingfactor,
        #         ),
        #         runparams,
        #     ),
        # )
        # # will be set within the driver
        # return retc

    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()

    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
