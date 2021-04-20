from asyncio import Queue, wait_for
from time import strftime, time_ns
from munch import munchify
import json
import asyncio
import websockets
import requests
from collections import deque
from pydantic import BaseModel
import aiofiles
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect
import uuid
import copy
import os
from typing import List, Optional, Any
import numpy as np
import uuid
from fastapi import FastAPI
import shortuuid

# work in progress
class LocalDataHandler:
    def __init__(self):
        self.filename = ''
        self.fileheader = ''
        self.filepath = 'C:\\temp' # some default value
        #self.fileext = '.txt' # some default value
        self.f = None

        
    # helper function        
    def sample_to_header(self, sample):
        sampleheader  = '%plate='+str(sample.plateid)
        sampleheader += '\n%sample='+'\t'.join([str(sample) for sample in sample.sampleid])
        sampleheader += '\n%x='+'\t'.join([str(x) for x in sample.x])
        sampleheader += '\n%y='+'\t'.join([str(y) for y in sample.y])
        sampleheader += '\n%elements='+'\t'.join([str(element) for element in sample.elements])
        sampleheader += '\n%composition='+'\t'.join([str(comp) for comp in sample.composition])
        sampleheader += '\n%code='+'\t'.join([str(code) for code in sample.code])
        return sampleheader
        


    async def open_file_async(self):
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
           
        if os.path.exists(os.path.join(self.filepath, self.filename)):
            self.f = await aiofiles.open(os.path.join(self.filepath, self.filename),'a')
            
        else:
            self.f = await aiofiles.open(os.path.join(self.filepath, self.filename),'w')
            if len(self.fileheader)>0:
                await self.write_data_async(self.write_header)


    async def write_sampleinfo_async(self, sample):
            await self.write_data_async(self.sample_to_header(sample))
        

    async def write_data_async(self, data):
        await self.f.write(data + '\n')


    async def close_file_async(self):
        await self.f.close()
        
        
    def open_file_sync(self):

        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
           
        if os.path.exists(os.path.join(self.filepath, self.filename)):
            # and just appends new data to excisting file
            self.f = open(os.path.join(self.filepath, self.filename),'a')
            
        else:
            # file does not exists, create file
            self.f = open(os.path.join(self.filepath, self.filename),'w')
            if len(self.fileheader)>0:
                self.write_data_sync(self.write_header)


    def write_sampleinfo_sync(self, sample):
            self.write_data_sync(self.sample_to_header(sample))


    def write_data_sync(self, data):
        self.f.write(data + '\n')

        
    def close_file_sync(self):
        self.f.close()


class StatusHandler:
    def __init__(self):
        self.q = Queue(maxsize=10)
        self.is_running = False
        self.is_idle = True
        self.status = 'idle'
        self.states = {}
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.procid = 'NA' # originally intended to show current decision or process_id but not compatible with concurrent actions on same server, check self.states
        self.dict = {'status': self.status, 'states': self.states,
                     'last_update': self.last_update, 'procid': self.procid}
        self.q.put_nowait(self.dict)

# sync update_nowait: data websocket should key by ID
#
    def initStatus(self, fastapp: FastAPI, servKey: str):
        for route in fastapp.routes:
            if route.path.startswith(f"/{servKey}"):
                self.states.update({route.name: []})

    async def update(self, state: str):
        self.status = state
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.dict = {'status': self.status, 'states': self.states,
                     'last_update': self.last_update, 'procid': self.procid}
        if self.q.full():
            _ = await self.q.get()
            self.q.task_done()
        await self.q.put(self.dict)

    async def set_run(self, uuid: str, action_name: str):
        self.is_running = True
        self.is_idle = False
        self.states[action_name].append(uuid)
        await self.update('running')

    async def set_idle(self, uuid: str, action_name: str):
        self.states[action_name].remove(uuid)
        if all([len(v)==0 for v in self.states.values()]):
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
        
    async def set_meta(self, metadict, keyname="meta"):
        self.dict[keyname] = metadict
        await self.update(self.status)
        
    async def clear_meta(self, keyname="meta"):
        self.dict.pop(keyname, None)
        await self.update(self.status)


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
        
    async def set_meta(self, metadict, keyname="meta"):
        self.dict[keyname] = metadict
        await self.update(self.status)


class Decision:
    def __init__(self, uid: str, plate_id: int, sample_no: int, actualizer):
        # self.uid = uid
        self.plate_id = plate_id
        self.sample_no = sample_no
        self.actualizer = actualizer
        # self.created_at = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.save_path = None
        self.aux_files = []


class Action:
    def __init__(self, decision: Decision, server_key: str, action: str, action_pars: dict, preempt: bool = True, block: bool = True):
        self.decision = decision
        self.server = server_key
        self.action = action
        self.pars = action_pars
        self.preempt = preempt
        self.block = block
        self.created_at = f'{strftime("%Y%m%d.%H%M%S%z")}'



class transformxy():
    def transform_platexy_to_motorxy(M, platexy):
        motorxy = np.dot(np.asmatrix(M),np.asarray(platexy))
        return motorxy

    def transform_motorxy_to_platexy(M, motorxy):
        print(np.asarray(motorxy))
        print(M)
        try:
            platexy = np.dot(np.asmatrix(M).I,np.asarray(motorxy))
        except Exception:
            print('------------------------------ Matrix singular ---------------------------')
            platexy = np.array([[None, None, None]])
        return platexy


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


# class for sample parameters
# everything except plateid needs to be a list as ANEC2 will do parallel measurements
class sample_class(BaseModel):
    plateid: str = None
    sampleid: List[str] = []
    x: List[str] = []
    y: List[str] = []
    elements: List[str] = []
    composition: List[str] = []
    code: List[str] = []


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"


class wsConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send(self, websocket: WebSocket, q, name):
        await self.connect(websocket)
        try:
            while True:
                data = await q.get()
                # only send to one
                #await wsdata.send_personal_message(json.dumps(data), websocket)
                # send to all
                await self.broadcast(json.dumps(data))
        except WebSocketDisconnect:
            self.disconnect(websocket)
            await self.broadcast(" ...  Websocket {name} connection unexpectedly closed.")


# multisubscriber queue by Kyle Smith
# https://github.com/smithk86/asyncio-multisubscriber-queue
class MultisubscriberQueue(object):
    def __init__(self, **kwargs):
        """
        The constructor for MultisubscriberQueue class
        """
        super().__init__()
        self.subscribers = list()

    def __len__(self):
        return len(self.subscribers)

    def __contains__(self, q):
        return q in self.subscribers

    async def subscribe(self):
        """
        Subscribe to data using an async generator
        Instead of working with the Queue directly, the client can
        subscribe to data and have it yielded directly.
        Example:
            with MultisubscriberQueue.subscribe() as data:
                print(data)
        """
        with self.queue_context() as q:
            while True:
                val = await q.get()
                if val is StopAsyncIteration:
                    break
                else:
                    yield val

    def queue(self):
        """
        Get a new async Queue
        """
        q = Queue()
        self.subscribers.append(q)
        return q

    def queue_context(self):
        """
        Get a new queue context wrapper
        The queue context wrapper allows the queue to be automatically removed
        from the subscriber pool when the context is exited.
        Example:
            with MultisubscriberQueue.queue_context() as q:
                await q.get()
        """
        return _QueueContext(self)

    def remove(self, q):
        """
        Remove queue from the pool of subscribers
        """
        if q in self.subscribers:
            self.subscribers.remove(q)
        else:
            raise KeyError('subscriber queue does not exist')

    async def put(self, data: Any):
        """
        Put new data on all subscriber queues
        Parameters:
            data: queue data
        """
        for q in self.subscribers:
            await q.put(data)

    async def close(self):
        """
        Force clients using MultisubscriberQueue.subscribe() to end iteration
        """
        await self.put(StopAsyncIteration)


class _QueueContext(object):
    def __init__(self, parent):
        self.parent = parent
        self.queue = None

    def __enter__(self):
        self.queue = self.parent.queue()
        return self.queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent.remove(self.queue)

class IOhelper:
    def __init__(self):
        self.subscribers = 0


def getuid(servername: str):
    uuid1 = uuid.uuid1()
    uuid3 = uuid.uuid3(uuid.NAMESPACE_URL, f"{uuid1}-{servername}")
    short = shortuuid.encode(uuid3)[:8]
    return short