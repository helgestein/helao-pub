from asyncio import Queue
from time import strftime
from munch import munchify
import json
import asyncio
import websockets
import requests
from collections import deque

class StatusHandler:
    def __init__(self):
        self.q = Queue(maxsize=10)
        self.status = 'idle'
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.procid = 'NA'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid}

    async def update(self, state: str):
        self.status = state
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid}
        if self.q.full():
            _ = await self.q.get()
            self.q.task_done()
        await self.q.put(self.dict)


class OrchHandler:
    def __init__(self, config):
        self.msgq = Queue(maxsize=10) # queue for orchestrator status
        self.dataq = Queue(maxsize=10) # consolidated queue for action server statuses
        self.actions = deque([])
        self.decisions = deque([])
        self.blocked = False
        
        self.status = 'idle'
        self.last_update = f'{strftime("%Y%m%d.%H%M%S%z")}'
        self.last_act = {}
        self.procid = 'NA'
        self.dict = {'status': self.status,
                     'last_update': self.last_update, 'procid': self.procid, 'last_act': self.last_act, 'blocked': self.blocked}
        
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

    async def monitor_states(self):
        self.fastSockets = {
            S: f"ws://{self.C[S].host}:{self.C[S].port}/{S}/ws_status" for S in self.fastServers}
        while True:
            await asyncio.wait([self.handle_socket(uri, k) for k, uri in self.fastSockets])
