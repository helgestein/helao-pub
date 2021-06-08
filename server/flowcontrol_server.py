import os
import sys
import json
from importlib import import_module
#from asyncio import Queue
#from time import strftime
import asyncio


import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager
from classes import sample_class
from classes import getuid
from classes import action_runparams
from classes import Action_params

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


# check if 'simulate' settings is present
if not 'simulate' in S:
    # default if no simulate is defined
    print('"simulate" not defined, switching to Gamry Simulator.')
    S['simulate']= False


if S.simulate:
    print('Gamry simulator loaded.')
    from gamry_simulate import gamry
else:
    from gamry_driver import gamry
    from gamry_driver import Gamry_Irange


app = FastAPI(title=servKey,
              description="ORCH ACTIONs", version=1.0)


@app.on_event("startup")
def startup_event():
    global stat
    stat = StatusHandler()
    global wsdata
    wsdata = wsConnectionManager()
    global wsstatus
    wsstatus = wsConnectionManager()
    
    
    
    
    