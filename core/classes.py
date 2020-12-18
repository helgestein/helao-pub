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
        self.is_running = False
        self.is_idle = True
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

    async def set_run(self):
        self.is_running = True
        self.is_idle = False
        await self.update('running')

    async def set_idle(self):
        self.is_idle = True
        self.is_running = False
        await self.update('idle')


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

    async def block(self):
        self.is_blocked = True

    async def unblock(self):
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
