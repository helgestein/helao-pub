# data management server for HTE

import os
import sys

from importlib import import_module
import uvicorn

from fastapi import WebSocket
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from typing import Optional
from prototyping import Action, HelaoFastAPI, Base


confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


# check if 'mode' setting is present
if not 'mode' in S:
    print('"mode" not defined, switching to legacy mode.')
    S['mode']= "legacy"


if S.mode == "legacy":
    print("Legacy data managament mode")
    from HTEdata_legacy import HTEdata
elif S.mode == "modelyst":
    print("Modelyst data managament mode")
#    from HTEdata_modelyst import HTEdata
else:
    print("Unknown data mode")
#    from HTEdata_dummy import HTEdata


app = HelaoFastAPI(config, servKey, title="HTE data management server",
    description="",
    version="1.0")


@app.on_event("startup")
def startup_event():
    global dataserv
    dataserv = HTEdata(S.params)
    global actserv
    actserv = Base(app)


@app.websocket(f"/ws_status")
async def websocket_status(websocket: WebSocket):
    """Broadcast status messages.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_status(websocket)


@app.websocket(f"/ws_data")
async def websocket_data(websocket: WebSocket):
    """Broadcast status dicts.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_data(websocket)
    

@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return actserv.status


@app.post(f"/{servKey}/get_elements_plateid")
async def get_elements_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """Gets the elements from the screening print in the info file"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_elements_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"elements": dataserv.get_elements_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_platemap_plateid")
async def get_platemap_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """gets platemap"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_platemap_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"map": dataserv.get_platemap_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_platexycalibration")
async def get_platexycalibration(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """gets saved plate alignment matrix"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_platexycalibration"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"matrix": None})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/save_platexycalibration")
async def save_platexycalibration(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """saves alignment matrix"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "save_platexycalibration"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"matrix": None})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/check_plateid")
async def check_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """checks that the plate_id (info file) exists"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "check_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"bool": dataserv.check_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/check_printrecord_plateid")
async def check_printrecord_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """checks that a print record exist in the info file"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "check_printrecord_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"bool": dataserv.check_printrecord_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/check_annealrecord_plateid")
async def check_annealrecord_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    """checks that a anneal record exist in the info file"""
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "check_annealrecord_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"bool": dataserv.check_annealrecord_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_info_plateid")
async def get_info_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_info_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"info": dataserv.get_info_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_rcp_plateid")
async def get_rcp_plateid(plateid: Optional[str]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        plateid = A.action_params['plateid']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_rcp_plateid"
        A.action_params['plateid'] = plateid
    active = await actserv.contain_action(A)
    await active.enqueue_data({"info": dataserv.get_rcp_plateidstr(plateid)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/create_new_liquid_sample_no")
async def create_new_liquid_sample_no(
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
    if action_dict:
        A = Action(action_dict) # actions originating from orchesterator will include decision attributes
        source = A.action_params['source']
        sourcevol_mL = A.action_params['sourcevol_mL']
        volume_mL = A.action_params['volume_mL']
        action_time = A.action_params['action_time']
        chemical = A.action_params['chemical']
        mass = A.action_params['mass']
        supplier = A.action_params['supplier']
        lot_number = A.action_params['lot_number']
        servkey = servKey
    else:
        A = Action() # this generates AUID and DUID, but DUID will be unrelated to previous actions
        A.action_server = servKey
        A.action_name = "create_new_liquid_sample_no"
        A.action_params['source'] = source 
        A.action_params['sourcevol_mL'] = sourcevol_mL 
        A.action_params['volume_mL'] = volume_mL 
        A.action_params['action_time'] = action_time 
        A.action_params['chemical'] = chemical 
        A.action_params['mass'] = mass 
        A.action_params['supplier'] = supplier 
        A.action_params['lot_number'] = lot_number 
        A.action_params['servkey'] = servKey 
    active = await actserv.contain_action(A)
    await active.enqueue_data({"id": await dataserv.create_new_liquid_sample_no(A.action_uuid,
                                                  A.decision_uuid,
                                                  source,
                                                  sourcevol_mL,
                                                  volume_mL,
                                                  action_time,
                                                  chemical,
                                                  mass,
                                                  supplier,
                                                  lot_number,
                                                  servkey)},
    )
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_last_liquid_sample_no")
async def get_last_liquid_sample_no(action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_last_liquid_sample_no"
    active = await actserv.contain_action(A)
    await active.enqueue_data({"liquid_sample": await dataserv.get_last_liquid_sample_no()})
    finished_act = await active.finish()
    return finished_act.as_dict()



@app.post(f"/{servKey}/get_liquid_sample_no")
async def get_liquid_sample_no(liquid_sample_no: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        liquid_sample_no = A.action_params['liquid_sample_no']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_liquid_sample_no"
        A.action_params['liquid_sample_no'] = liquid_sample_no
    active = await actserv.contain_action(A)
    await active.enqueue_data({"liquid_sample": await dataserv.get_liquid_sample_no(liquid_sample_no)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/get_liquid_sample_no_json")
async def get_liquid_sample_no_json(liquid_sample_no: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        liquid_sample_no = A.action_params['liquid_sample_no']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_liquid_sample_no_json"
        A.action_params['liquid_sample_no'] = liquid_sample_no
    active = await actserv.contain_action(A)
    await active.enqueue_data({"liquid_sample": await dataserv.get_liquid_sample_no_json(liquid_sample_no)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post('/endpoints')
def get_all_urls():
    """Return a list of all endpoints on this server."""
    return actserv.get_endpoint_urls(app)


@app.post("/shutdown")
def post_shutdown():
    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    return ""

    
if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
