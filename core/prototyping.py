import ntplib
import os
from classes import MultisubscriberQueue
from time import ctime, time, strftime, strptime
import asyncio
import aiohttp
import aiofiles
from copy import copy

import time
from random import getrandbits
import shortuuid


def gen_uuid(label: str, trunc: int=8):
    uuid1 = uuid.uuid1()
    uuid3 = uuid.uuid3(uuid.NAMESPACE_URL, f"{uuid1}-{label}")
    short = shortuuid.encode(uuid3)[:trunc]
    return short


class Decision(object):
    "Sample-process grouping class."
    def __init__(self, inputdict=None):
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.decision_uuid = imports.get('decision_uuid', None)
        self.decision_timestamp = imports.get('decision_timestamp', None)
        self.decision_label = imports.get('decision_label', 'no-label')
        # self.decision_path = imports.get('decision_path', None)
        self.plate_id = imports.get('plate_id', None)
        self.sample_no = imports.get('sample_no', None)
    def as_dict(self):
        return vars(self)
    def gen_uuid(self, server_name: str='server'):
        "server_name can be any string used in generating random uuid"
        if self.decision_uuid:
            print(f'decision_uuid: {self.decision_uuid} already exists')
        else:
            self.decision_uuid = gen_uuid(server_name)
            print(f'decision_uuid: {self.decision_uuid} assigned')
    def set_dtime(self):
        self.decision_timestamp = strftime("%Y%m%d.%H%M%S")


class Action(Decision):
    "Sample-process identifier class."
    def __init__(self, inputdict=None):
        super().__init__(inputdict) # grab decision keys
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.action_uuid = imports.get('action_uuid', None)
        self.action_timestamp = imports.get('action_timestamp', None)
        # self.action_path = imports.get('action_path', None)
        self.action_server = imports.get('action_server', {})
        self.action_name = imports.get('action_name', {})
        self.action_params = imports.get('action_params', {})
        self.start_condition = imports.get('start_condition', 3)
        self.aux_files = imports.get('aux_files', [])
        self.data = imports.get('data', [])
        # reassign these if specified in input
        self.plate_id = imports.get('plate_id', self.plate_id)
        self.sample_no = imports.get('sample_no', self.sample_no)
    def gen_uuid(self):
        if self.action_uuid:
            print(f'action_uuid: {self.action_uuid} already exists')
        else:
            self.action_uuid = gen_uuid(self.action_name)
            print(f'action_uuid: {self.action_uuid} assigned')
    def set_atime(self):
        self.action_timestamp = strftime("%Y%m%d.%H%M%S")
    
class Base(object):
    """Base class for all HELAO servers.
    
    Base is a general class which implements message passing, status update, data 
    writing, and data streaming via async tasks. Every instrument and action server
    should import this class for efficient integration into an orchestrated environment.
    
    A Base initialized within a FastAPI startup event will launch three async tasks
    to the server's event loop for handling:
    (1) broadcasting status updates via websocket and http POST requests to an attached
        orchestrator's status updater if available,
    (2) data streaming via websocket,
    (3) data writing to local disk.
    
    Websocket connections are broadcast from a multisubscriber queue in order to handle
    consumption from multiple clients awaiting a single queue. Self-subscriber tasks are
    also created as initial subscribers to log all events and prevent queue overflow.
    
    The data writing method will update a class attribute with the currently open file.
    For a given root directory, files and folders will be written as follows:
    {%y.%j}/  # decision_date year.weeknum
        {%Y%m%d}/  # decision_date
            {%H%M%S}__{decision_label}__{plate_id}/  # decision_time
                {%Y%m%d.%H%M%S}__{uuid}/  # action_datetime, action_uuid
                    {sampleno}__{filename}.{ext}
                    {%Y%m%d.%H%M%S}__{uuid}.rcp  # action_datetime
                    (aux_files)
    """
    def __init__(self, server_name, save_root):
        self.server_name = server_name
        self.save_root = save_root
        self.status = None
        self.active = None
        self.last = None
        self.file_conn = None # aiofiles connection
        self.status_q = MultisubscriberQueue()
        self.data_q = MultisubscriberQueue()
        self.status_clients = set()
        self.data_clients= set()
        self.ntp_server = 'time.nist.gov'
        self.ntp_response = None
        if os.path.exists('ntpLastSync.txt'):
            self.ntp_last_sync = open('ntpLastSync.txt', 'r').readlines()[0].strip()
        elif self.ntp_last_sync is None:
            self.get_ntp_time()
        self.ntp_offset = None # add to system time for correction
        self.get_ntp_time()
    
    def get_ntp_time(self):
        "Check system clock against NIST clock for trigger operations."
        c = ntplib.NTPClient()
        response = c.request(self.ntp_server, version=3)
        self.ntp_response = response
        self.ntp_last_sync = response.orig_time
        self.ntp_offset = response.offset
        open('ntpLastSync.txt', 'w').write(self.ntp_last_sync)
        print(f"retrieved time at {ctime(self.ntp_response.tx_timestamp)} from {self.ntp_server}")
        
    def attach_client(self, client_addr):
        "Add client for pushing status updates via HTTP POST."
        self.status_clients.add(client_addr)
        print(f"Added {client_addr} to status subscriber list.")
   
    def detach_client(self, client_addr):
        "Remove client from receiving status updates via HTTP POST"
        self.status_clients.remove(client_addr)
        
    async def log_status_task(self, retry_limit=5):
        "Self-subscribe to status queue, log status changes, POST to clients."
        async for status_msg in self.status_q.subscribe():
            self.status = status_msg
            for client_addr in self.status_clients:
                async with aiohttp.ClientSession() as session:
                    success = False
                    for _ in range(retryLimit):
                        async with session.post(
                            f"http://{client_addr}/update_status", params = {"server": self.server_name, "status": status_msg}
                        ) as resp:
                            response = await resp
                        if response.status<400:
                            success = True
                            break
                if success:
                    print(f"Updated {self.server_name} status to {status_msg} on {client_addr}.")
                else:
                    print(f"Failed to push status message to {client_addr} after {retry_limit} attempts.")
            # do stuff with statusMsg (websocket handled in FastAPI definition)
                            
    async def detach_subscribers(self):
        await self.status_q.put(StopAsyncIteration)
        await self.data_q.put(StopAsyncIteration)
        await asyncio.sleep(5)
    
    async def log_data_task(self):
        "Self-subscribe to data queue, write to present filePath."
        async for data_msg in self.data_q.subscribe():
            # dataMsg should be a list of values or a list of list of values
            if isinstance(data_msg[0], list):
                lines = "\n".join([",".join([str(x) for x in l]) for l in data_msg])
            else:
                lines = ",".join([str(x) for x in data_msg])
            if self.file_conn:
                await self.write_live_data(lines)
    
    async def sync_ntp_task(self, resync_time=600):
        "Regularly sync with NTP server."
        while True:
            if time() - self.ntp_last_sync > resync_time:
                self.get_ntp_time()
            else:
                await asyncio.sleep(0.5)
                
    async def write_file(self, output_str, filename, header=None):
        "Write complete file, not used with queue streaming."
        decision_date = self.active['decision_timestamp'].split('.')[0]
        decision_time = self.active['decision_timestamp'].split('.')[-1]
        year_week = strftime("%y.%U", strptime(decision_date, "%Y%m%d"))
        output_path = os.path.join(self.save_root,
                                                year_week,
                                                decision_date,
                                                f"{decision_time}_{self.active['decision_label']}",
                                                filename
                                                )
        os.makedirs(os.path.dirname(self.active['save_path']), exist_ok=True)
        # create output file and set connection
        file_instance = await aiofiles.open(output_path, mode="w")
        if header:
            if not header.endswith("\n"):
                header += "\n"
                output_str = header + output_str
        await file_instance.write(output_str)
        await file_instance.close()
        numlines = len(output_str.split('\n'))
        print(f"Wrote {numlines} lines to {output_path}")
    
    async def set_output_file(self, filename, header=None):
        "Set active save_path, write header if supplied."
        decision_date = self.active['decision_timestamp'].split('.')[0]
        decision_time = self.active['decision_timestamp'].split('.')[-1]
        year_week = strftime("%y.%U", strptime(decision_date, "%Y%m%d"))
        self.active['save_path'] = os.path.join(self.save_root,
                                                year_week,
                                                decision_date,
                                                f"{decision_time}_{self.active['decision_label']}",
                                                filename
                                                )
        os.makedirs(os.path.dirname(self.active['save_path']), exist_ok=True)
        # create output file and set connection
        self.file_conn = await aiofiles.open(self.active['save_path'], mode="a+")
        if header:
            if not header.endswith("\n"):
                header += "\n"
            await self.file_conn.write(header)
                
    async def finish_act(self):
        "Close file_conn, set idle status, and move active dict to past."
        if self.file_conn:
            await self.file_conn.close()
            self.file_conn = None
        self.last = copy(self.active)
        self.active = None
        await self.status_q.put('idle')
    
    async def write_live_data(self, output_str):
        "Appends lines to file_conn."
        if self.file_conn:
            if not output_str.endswith("\n"):
                output_str += "\n"
            await self.file_conn.write(output_str)
    
    async def setup_act(self, action: Action):#TODO
        "Populate active decision."
        self.active = action
        pass
    
    async def write_rcp(self):#TODO
        "Gather auxiliary filenames, save ID and action parameters to rcp."
    
    async def relocate_files(self, folderpath): #TODO
        "Copy auxiliary files from folderpath to rcp directory."

class Orch(object):#TODO
    """Base class for async orchestrator with trigger support and pushed status update.
    
    Websockets are not used for critical communications. Orch will attach to all action 
    servers listed in a config and maintain a dict of {serverName: status}, which is 
    updated by POST requests from action servers. Orch will simultaneously dispatch as
    many actions as possible in action queue until it encounters any of the following
    conditions:
      (1) last executed action is final action in queue
      (2) last executed action is blocking
      (3) next action to execute is preempted
      (4) next action is on a busy action server
    which triggers a temporary async task to monitor the action server status dict until
    all conditions are cleared.
    
    POST requests from action servers are added to a multisubscriber queue and consumed
    by a self-subscriber task to update the action server status dict and log changes.
    
    """
    