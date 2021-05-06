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

    async def set_run(self, uuid: str = 'dummy', action_name: str = 'dummy'):
        self.is_running = True
        self.is_idle = False
        if action_name not in self.states:
            self.states[action_name] = [uuid]
        else:
            self.states[action_name].append(uuid)
        await self.update('running')

    async def set_idle(self, uuid: str = 'dummy', action_name: str = 'dummy'):
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
    # Updating plate calibration will automatically update the system transformation
    # matrix. When angles are changed updated them also here and run update_Msystem 
    def __init__(self, Minstr, seq = None):
        # instrument specific matrix
        # motor to instrument
        self.Minstrxyz = np.asmatrix(np.identity(4))
        self.Minstr = np.asmatrix(np.identity(4))
        self.Minstrinv = np.asmatrix(np.identity(4))
        # plate Matrix
        # instrument to plate
        self.Mplate = np.asmatrix(np.identity(4))
        self.Mplatexy = np.asmatrix(np.identity(3))
        # system Matrix
        # motor to plate
        self.M = np.asmatrix(np.identity(4))
        self.Minv = np.asmatrix(np.identity(4))
        # need to update the angles here each time the axis is rotated
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.seq = seq
        
        # pre calculates the system Matrix M
        self.update_Msystem()


    def transform_platexy_to_motorxy(self, platexy):
        '''simply calculates motorxy based on platexy
        plate warping (z) will be a different call'''
        platexy = np.asarray(platexy)
        if len(platexy) == 3:
            platexy = np.insert(platexy,2,0)
        # for _ in range(4-len(platexy)):
        #     platexy = np.append(platexy,1)
        print(' ... M:\n', self.M)
        print(' ... xy:', platexy)
        motorxy = np.dot(self.M,platexy)
        motorxy = np.delete(motorxy,2)
        motorxy = np.array(motorxy)[0]
        return motorxy


    def transform_motorxy_to_platexy(self, motorxy):
        '''simply calculates platexy from current motorxy'''
        motorxy = np.asarray(motorxy)
        if len(motorxy) == 3:
            motorxy = np.insert(motorxy,2,0)
        print(' ... Minv:\n', self.Minv)
        print(' ... xy:', motorxy)
        platexy = np.dot(self.Minv,motorxy)
        platexy = np.delete(platexy,2)
        platexy = np.array(platexy)[0]
        return platexy


    def transform_motorxyz_to_instrxyz(self, motorxyz):
        '''simply calculatesinstrxyz from current motorxyz'''
        motorxyz = np.asarray(motorxyz)
        if len(motorxyz) == 3:
            # append 1 at end
            motorxyz = np.append(motorxyz,1)
        print(' ... Minstrinv:\n', self.Minstrinv)
        print(' ... xyz:', motorxyz)
        instrxyz = np.dot(self.Minstrinv,motorxyz)
        return np.array(instrxyz)[0]


    def transform_instrxyz_to_motorxyz(self, instrxyz):
        '''simply calculates motorxyz from current instrxyz'''
        instrxyz = np.asarray(instrxyz)
        if len(instrxyz) == 3:
            instrxyz = np.append(instrxyz,1)
        print(' ... Minstr:\n', self.Minstr)
        print(' ... xyz:', instrxyz)
        
        motorxyz = np.dot(self.Minstr,instrxyz)
        return np.array(motorxyz)[0]


    def Rx(self):
        '''returns rotation matrix around x-axis'''
        alphatmp = np.mod(self.alpha, 360) # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if alphatmp == 0:# or alphatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif alphatmp == 90:# or alphatmp == -270:
            return np.matrix([[1,0,0,0],
                                [0,0,-1,0],
                                [0,1,0,0],
                                [0,0,0,1]])
        elif alphatmp == 180:# or alphatmp == -180:
            return np.matrix([[1,0,0,0],
                                [0,-1,0,0],
                                [0,0,-1,0],
                                [0,0,0,1]])
        elif alphatmp == 270:# or alphatmp == -90:
            return np.matrix([[1,0,0,0],
                                [0,0,1,0],
                                [0,-1,0,0],
                                [0,0,0,1]])
        else:
            return np.matrix([[1,0,0,0],
                                [0,np.cos(np.pi/180*alphatmp),-1.0*np.sin(np.pi/180*alphatmp),0],
                                [0,np.sin(np.pi/180*alphatmp),np.cos(np.pi/180*alphatmp),0],
                                [0,0,0,1]])


    def Ry(self):
        '''returns rotation matrix around y-axis'''
        betatmp = np.mod(self.beta, 360) # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if betatmp == 0:# or betatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif betatmp == 90:# or betatmp == -270:
            return np.matrix([[0,0,1,0],
                                [0,1,0,0],
                                [-1,0,0,0],
                                [0,0,0,1]])
        elif betatmp == 180:# or betatmp == -180:
            return np.matrix([[-1,0,0,0],
                                [0,1,0,0],
                                [0,0,-1,0],
                                [0,0,0,1]])
        elif betatmp == 270:# or betatmp == -90:
            return np.matrix([[0,0,-1,0],
                                [0,1,0,0],
                                [1,0,0,0],
                                [0,0,0,1]])
        else:
            return np.matrix([[np.cos(np.pi/180*self.beta),0,np.sin(np.pi/180*self.beta),0],
                                [0,1,0,0],
                                [-1.0*np.sin(np.pi/180*self.beta),0,np.cos(np.pi/180*self.beta),0],
                                [0,0,0,1]])


    def Rz(self):
        '''returns rotation matrix around z-axis'''
        gammatmp = np.mod(self.gamma, 360) # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if gammatmp == 0:# or gammatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif gammatmp == 90:# or gammatmp == -270:
            return np.matrix([[0,-1,0,0],
                                [1,0,0,0],
                                [0,0,1,0],
                                [0,0,0,1]])
        elif gammatmp == 180:# or gammatmp == -180:
            return np.matrix([[-1,0,0,0],
                                [0,-1,0,0],
                                [0,0,1,0],
                                [0,0,0,1]])
        elif gammatmp == 270:# or gammatmp == -90:
            return np.matrix([[0,1,0,0],
                                [-1,0,0,0],
                                [0,0,1,0],
                                [0,0,0,1]])
        else:
            return np.matrix([[np.cos(np.pi/180*gammatmp),-1.0*np.sin(np.pi/180*gammatmp),0,0],
                                [np.sin(np.pi/180*gammatmp),np.cos(np.pi/180*gammatmp),0,0],
                                [0,0,1,0],
                                [0,0,0,1]])

    
    def Mx(self):
        '''returns Mx part of Minstr'''
        Mx = np.asmatrix(np.identity(4))
        Mx[0,0:4] = self.Minstrxyz[0,0:4]
        return Mx


    def My(self):
        '''returns My part of Minstr'''
        My = np.asmatrix(np.identity(4))
        My[1,0:4] = self.Minstrxyz[1,0:4]
        return My


    def Mz(self):
        '''returns Mz part of Minstr'''
        Mz = np.asmatrix(np.identity(4))
        Mz[2,0:4] = self.Minstrxyz[2,0:4]
        return Mz
    
    
    def Mplatewarp(self, platexy):
        '''returns plate warp correction matrix (Z-correction. 
        Only valid for a single platexy coordinate'''
        return np.asmatrix(np.identity(4)) # TODO, just returns identity matrix for now


    def update_Msystem(self):
        '''updates the transformation matrix for new plate calibration or
        when angles are changed.
        Follows stacking sequence from bottom to top (plate)'''
        if self.seq == None:
            # default case, we simply have xy calibration
            self.M = np.dot(self.Minstrxyz, self.Mplate)
        else:
            self.Minstr = np.asmatrix(np.identity(4))
            # more complicated
            # check for some common sequences:
            Mcommon1 = False # to check against when common combinations are already found
            axstr = ''
            for ax in self.seq.keys():
                axstr += ax
            # check for xyz or xy (with no z)
            # sequence does not matter so should define it like this in the config
            # if we want to use this
            if axstr.find('xy') == 0 and axstr.find('z') <= 2:
                self.Minstr = self.Minstrxyz
                Mcommon1 = True
            
            for ax in self.seq.keys():
                if ax == 'x' and not Mcommon1:
                    self.Minstr = np.dot(self.Minstr, self.Mx())
                elif ax == 'y' and not Mcommon1:
                    self.Minstr = np.dot(self.Minstr, self.My())
                elif ax == 'z' and not Mcommon1:
                    self.Minstr = np.dot(self.Minstr, self.Mz())
                elif ax == 'Rx':
                    self.Minstr = np.dot(self.Minstr, self.Rx())
                elif ax == 'Ry':
                    self.Minstr = np.dot(self.Minstr, self.Ry())
                elif ax == 'Rz':
                    self.Minstr = np.dot(self.Minstr, self.Rz())
            
            self.M = np.dot(self.Minstr, self.Mplate)

            # precalculate the inverse as we also need it a lot
            try:
                self.Minv = self.M.I
            except Exception:
                print('------------------------------ System Matrix singular ---------------------------')
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minv = np.matrix([[0,0,0,0],
                                       [0,0,0,0],
                                       [0,0,0,0],
                                       [0,0,0,-1]])

            try:
                self.Minstrinv = self.Minstr.I
            except Exception:
                print('------------------------------ Instrument Matrix singular ---------------------------')
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minstrinv = np.matrix([[0,0,0,0],
                                       [0,0,0,0],
                                       [0,0,0,0],
                                       [0,0,0,-1]])



            
            print(' ... new system matrix:')
            print(self.M)
            print(' ... new inverse system matrix:')
            print(self.Minv)


    def update_Mplatexy(self, Mxy):
        '''updates the xy part of the plate calibration'''
        Mxy = np.matrix(Mxy)
        # assign the xy part        
        self.Mplate[0:2,0:2] = Mxy[0:2,0:2]
        # assign the last row (offsets), notice the difference in col (3x3 vs 4x4)
#        self.Mplate[0:2,3] = Mxy[0:2,2] # something does not work with this one is a 1x2 the other 2x1 for some reason
        self.Mplate[0,3] = Mxy[0,2]
        self.Mplate[1,3] = Mxy[1,2]
        # self.Mplate[3,0:4] should always be 0,0,0,1 and should never change
        
        # update the system matrix so we save calculation time later
        self.update_Msystem()


    def get_Mplatexy(self):
        '''returns the xy part of the platecalibration'''
        self.Mplatexy = np.asmatrix(np.identity(3))
        self.Mplatexy[0:2,0:2] = self.Mplate[0:2,0:2]
        self.Mplatexy[0,2] = self.Mplate[0,3]
        self.Mplatexy[1,2] = self.Mplate[1,3]
        return self.Mplatexy
    
    
    def get_Mplate_Msystem(self, Mxy):
        '''removes Minstr from Msystem to obtain Mplate for alignment'''
        Mxy = np.asarray(Mxy)
        Mglobal = np.asmatrix(np.identity(4))
        Mglobal[0:2,0:2] = Mxy[0:2,0:2]
        Mglobal[0,3] = Mxy[0,2]
        Mglobal[1,3] = Mxy[1,2]
        
        try:
            Minstrinv = self.Minstr.I
            Mtmp = np.dot(Minstrinv, Mglobal)
            self.Mplatexy = np.asmatrix(np.identity(3))
            self.Mplatexy[0:2,0:2] = Mtmp[0:2,0:2]
            self.Mplatexy[0,2] = Mtmp[0,3]
            self.Mplatexy[1,2] = Mtmp[1,3]

            return self.Mplatexy
        except Exception:
            print('------------------------------ Instrument Matrix singular ---------------------------')
            # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
            self.Minv = np.matrix([[0,0,0],
                                   [0,0,0],
                                   [0,0,-1]])

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