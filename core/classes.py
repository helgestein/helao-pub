from asyncio import Queue
from time import strftime
from munch import munchify
import json
import asyncio
import websockets
import requests
from collections import deque
from pydantic import BaseModel
import aiofiles
from enum import Enum
from fastapi import WebSocket
import uuid
import copy
import os


# work in progress
class LocalDataHandler:
    def __init__(self):
        self.filename = ''
        self.fileheader = ''
        self.filepath = 'C:\\temp' # some default value
        self.fileext = '.txt' # some default value
        self.f = None


    async def open_file(self):
        # (1) check if path exists, else create it
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
        # (2) check if file already exists
        # append to file if exists, else create a new one
        # does fileextension contain a period?
        if self.fileext.find('.',0,1) == -1:
           self.fileext = '.'+self.fileext
           
        if os.path.exists(os.path.join(self.filepath, self.filename+self.fileext)):
            # file exists, append to file
            self.f = await aiofiles.open(os.path.join(self.filepath, self.filename+self.fileext),'a')
        else:
            # file does not exists, create file
            self.f = await aiofiles.open(os.path.join(self.filepath, self.filename+self.fileext),'w')


    async def write_header(self):
        await self.f.write(self.fileheader + '\n')


    async def write_data(self, data):
        await self.f.write(data + '\n')


    async def close_file(self):
        await self.f.close()


class StatusHandler:
    def __init__(self):
        self.q = Queue(maxsize=10)
        self.is_running = False
        self.is_idle = True
        self.status = 'idle'
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.procid = 'NA'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid}
        self.q.put_nowait(self.dict)


    async def update(self, state: str):
        self.status = state
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid}
        if self.q.full():
            _ = await self.q.get()
            self.q.task_done()
        await self.q.put(self.dict)

    async def set_run(self):
        self.is_running = True
        self.is_idle = False
        await self.update('running')

    async def set_idle(self):
        self.is_idle = True
        self.is_running = False
        await self.update('idle')

    async def set_error(self):
        self.is_idle = False
        self.is_running = False
        await self.update('error')

    async def set_estop(self):
        self.is_idle = False
        self.is_running = False
        await self.update('estop')


class OrchHandler:
    def __init__(self, config):
        self.msgq = Queue(maxsize=10)  # queue for orchestrator status
        # consolidated queue for action server statuses
        self.dataq = Queue(maxsize=10)
        # contains action tuples of the form [decision_id, server_key, server_action, action_params, preempt_flag, blocking_flag]
        self.actions = deque([])
        # contains decision tuples of the form [decision_id, action_library_function]
        self.decisions = deque([])
        self.is_blocked = False
        self.is_running = False
        self.is_idle = True
        self.status = 'idle'
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.last_act = {}
        self.procid = 'NA'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid, 'last_act': self.last_act, 'is_blocked': self.is_blocked, 'is_running': self.is_running, 'is_idle': self.is_idle}
        self.msgq.put_nowait(self.dict)

        self.fastServers = [k for k in config.keys() if "fast" in config[k].keys()
                            and config[k]["group"] != "orchestrators"]
        self.C = munchify(config)
        self.STATES = {S: requests.post(
            f"http://{self.C[S].host}:{self.C[S].port}/{S}/get_status").json() for S in self.fastServers}

    async def update(self, state: str):
        self.status = state
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid, 'last_act': self.last_act}
        if self.msgq.full():
            _ = await self.msgq.get()
            self.msgq.task_done()
        await self.msgq.put(self.dict)

    async def handle_socket(self, uri, key):
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    async for message in websocket:
                        statusd = json.loads(message)
                        self.STATES[key] = statusd
                        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
                        self.last_act = {key: statusd}
                        if self.dataq.full():
                            _ = await self.dataq.get()
                            self.dataq.task_done()
                        await self.dataq.put(self.STATES)
            except websockets.exceptions.ConnectionClosedError:
                print('Websocket connection unexpectedly closed. Retrying in 3 seconds.')
                await asyncio.sleep(3)

    def monitor_states(self):
        self.fastSockets = {
            S: f"ws://{self.C[S].host}:{self.C[S].port}/{S}/ws_status" for S in self.fastServers}
        if self.fastSockets:
            self.monitors = {k: asyncio.create_task(self.handle_socket(uri, k)) for k, uri in self.fastSockets.items()}

    def block(self):
        self.is_blocked = True

    def unblock(self):
        self.is_blocked = False

    async def set_run(self):
        self.is_running = True
        self.is_idle = False
        await self.update('running')

    async def set_idle(self):
        self.is_idle = True
        self.is_running = False
        await self.update('idle')

    async def raise_skip(self):
        await self.update('skipping')

    async def raise_stop(self):
        await self.update('stopping')


class Decision:
    def __init__(self, uid: str, plate_id: int, sample_no: int, actualizer):
        self.uid = uid
        self.plate_id = plate_id
        self.sample_no = sample_no
        self.actualizer = actualizer
        self.created_at = f'{strftime("%Y%m%d.%H%M%S%z")}'


class Action:
    def __init__(self, decision: Decision, server_key: str, action: str, action_pars: dict, preempt: bool = True, block: bool = True):
        self.decision = decision
        self.server = server_key
        self.action = action
        self.pars = action_pars
        self.preempt = preempt
        self.block = block
        self.created_at = f'{strftime("%Y%m%d.%H%M%S%z")}'


# return class for FastAPI calls
class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None
    err_code: str = None


# return class for status ws
class return_status(BaseModel):
    measurement_type: str
    parameters: dict
    status: dict


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"

    
class wsHandler:
    def __init__(self, q, name):
        self.subscribers = 0
        self.dataq = q
        self.lastuuid = None
        self.lastq = None
        self.name = name

        self.IOloop_run = False
        self.myloop = asyncio.get_event_loop()
        #add IOloop
        self.myloop.create_task(self.wsdata_IOloop())


    async def wsdata_IOloop(self):
        self.IOloop_run = True
        while self.IOloop_run:
            try:
                if self.subscribers > 0: # > 0
                    self.IOloop_run = True
                    self.lastuuid = uuid.uuid4()
                    self.lastq = await self.dataq.get()
                    #print(f' ... {self.name} got data:')
                    #print(self.lastq)
                else:
                    await asyncio.sleep(1)
            except Exception:
                print(f' ... Connection to {self.name} unexpectedly lost. Retrying in 3 seconds.')
                await asyncio.sleep(3)
                
                
    # use in wsapi def via 'await websocket_slave(mywebsocket)'
    async def websocket_slave(self, mywebsocket: WebSocket):
        await mywebsocket.accept()
        localuuid = None
        
        self.subscribers = self.subscribers + 1
        while self.IOloop_run:
            try:
                if localuuid != self.lastuuid:
                    # deep copy, else id() will be the same
                    localuuid = copy.deepcopy(self.lastuuid)
                    #print(' ...  sending data', self.lastq)
                    await mywebsocket.send_text(json.dumps(self.lastq))
                else:
                    await asyncio.sleep(1)
            except Exception:#mywebsocket.exceptions.ConnectionClosedError:
                    #print(f'Slave Websocket {self.name} connection unexpectedly closed. Retrying in 3 seconds.')
                    #await asyncio.sleep(3)
                    print(f' ... Slave Websocket {self.name} connection unexpectedly closed.')
                    self.subscribers = self.subscribers - 1
                    return
        self.subscribers = self.subscribers - 1
