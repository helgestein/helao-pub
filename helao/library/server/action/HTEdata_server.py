# data management server for HTE
from typing import Optional
from importlib import import_module
from fastapi import Request
from helao.core.server import makeActServ, setupAct


def makeApp(confPrefix, servKey):

    config = import_module(f"helao.config.{confPrefix}").config
    C = config["servers"]
    S = C[servKey]

    # check if 'mode' setting is present
    if not 'mode' in S.keys():
        print('"mode" not defined, switching to legacy mode.')
        S['mode']= "legacy"


    if S['mode'] == "legacy":
        print("Legacy data managament mode")
        from helao.library.driver.HTEdata_legacy import HTEdata
    elif S['mode'] == "modelyst":
        print("Modelyst data managament mode")
    #    from HTEdata_modelyst import HTEdata
    else:
        print("Unknown data mode")
    #    from HTEdata_dummy import HTEdata


    app = makeActServ(
        config, servKey, servKey, "HTE data management server", version=2.0, driver_class=HTEdata
    )

    @app.post(f"/{servKey}/get_elements_plateid")
    async def get_elements_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """Gets the elements from the screening print in the info file"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.get_elements_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_platemap_plateid")
    async def get_platemap_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """gets platemap"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.get_platemap_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_platexycalibration")
    async def get_platexycalibration(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """gets saved plate alignment matrix"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(None)
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/save_platexycalibration")
    async def save_platexycalibration(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """saves alignment matrix"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(None)
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/check_plateid")
    async def check_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """checks that the plate_id (info file) exists"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.check_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/check_printrecord_plateid")
    async def check_printrecord_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """checks that a print record exist in the info file"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.check_printrecord_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/check_annealrecord_plateid")
    async def check_annealrecord_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        """checks that a anneal record exist in the info file"""
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.check_annealrecord_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_info_plateid")
    async def get_info_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.get_info_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_rcp_plateid")
    async def get_rcp_plateid(request: Request, plateid: Optional[str]=None, action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(app.driver.get_rcp_plateid(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/create_new_liquid_sample_no")
    async def create_new_liquid_sample_no(request: Request, 
                            source: Optional[str] = None,
                            sourcevol_mL: Optional[str] = None,
                            volume_mL: Optional[float] = 0.0,
                            action_time: Optional[str] = None,
                            chemical: Optional[str] = None,
                            mass: Optional[str] = None,
                            supplier: Optional[str] = None,
                            lot_number: Optional[str] = None,
                            servkey: Optional[str] = servKey,
                            action_dict: Optional[dict] = None
                            ):
        '''use CAS for chemical if available. Written on bottles of chemicals with all other necessary information.\n
        For empty DUID and AUID the UID will automatically created. For manual entry leave DUID, AUID, action_time, and action_params empty and servkey on "data".\n
        If its the very first liquid (no source in database exists) leave source and source_mL empty.'''
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.create_new_liquid_sample_no(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_last_liquid_sample_no")
    async def get_last_liquid_sample_no(request: Request, action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_last_liquid_sample_no())
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_liquid_sample_no")
    async def get_liquid_sample_no(request: Request, liquid_sample_no: Optional[int]=None, action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_liquid_sample_no(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()


    @app.post(f"/{servKey}/get_liquid_sample_no_json")
    async def get_liquid_sample_no_json(request: Request, liquid_sample_no: Optional[int]=None, action_dict: Optional[dict]=None):
        A = await setupAct(action_dict, request, locals())
        active = await app.base.contain_action(A)
        await active.enqueue_data(await app.driver.get_liquid_sample_no_json(**A.action_params))
        finished_act = await active.finish()
        return finished_act.as_dict()

    @app.post("/shutdown")
    def post_shutdown():
        shutdown_event()


    @app.on_event("shutdown")
    def shutdown_event():
        return ""

    return app
        