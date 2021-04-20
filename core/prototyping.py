import os
import json
import uuid
import shutil
from copy import copy
from collections import defaultdict
from socket import gethostname
from time import ctime, time, strftime, strptime
from typing import Optional

import shortuuid
import ntplib
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import wrap
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from classes import MultisubscriberQueue 

async_copy = wrap(shutil.copy)

def gen_uuid(label: str, trunc: int=8):
    "Generate a uuid, encode with larger character set, and trucate."
    uuid1 = uuid.uuid1()
    uuid3 = uuid.uuid3(uuid.NAMESPACE_URL, f"{uuid1}-{label}")
    short = shortuuid.encode(uuid3)[:trunc]
    return short

def rcp_to_dict(rcppath: str):  # read common info/rcp/exp/ana structure into dict
    dlist = []

    def tab_level(astr):
        """Count number of leading tabs in a string
        """
        return (len(astr) - len(astr.lstrip("    "))) / 4

    if rcppath.endswith(".zip"):
        if "analysis" in os.path.dirname(rcppath):
            ext = ".ana"
        elif "experiment" in os.path.dirname(rcppath):
            ext = ".exp"
        else:
            ext = ".rcp"
        rcpfn = os.path.basename(rcppath).split(".copied")[0] + ext
        archive = zipfile.ZipFile(rcppath, "r")
        with archive.open(rcpfn, "r") as f:
            for l in f:
                k, v = l.decode("ascii").split(":", 1)
                lvl = tab_level(l.decode("ascii"))
                dlist.append({"name": k.strip(), "value": v.strip(), "level": lvl})
    else:
        with open(rcppath, "r") as f:
            for l in f:
                k, v = l.split(":", 1)
                lvl = tab_level(l)
                dlist.append({"name": k.strip(), "value": v.strip(), "level": lvl})

    def ttree_to_json(ttree, level=0):
        result = {}
        for i in range(0, len(ttree)):
            cn = ttree[i]
            try:
                nn = ttree[i + 1]
            except:
                nn = {"level": -1}

            # Edge cases
            if cn["level"] > level:
                continue
            if cn["level"] < level:
                return result
            # Recursion
            if nn["level"] == level:
                dict_insert_or_append(result, cn["name"], cn["value"])
            elif nn["level"] > level:
                rr = ttree_to_json(ttree[i + 1 :], level=nn["level"])
                dict_insert_or_append(result, cn["name"], rr)
            else:
                dict_insert_or_append(result, cn["name"], cn["value"])
                return result
        return result

    def dict_insert_or_append(adict, key, val):
        """Insert a value in dict at key if one does not exist
        Otherwise, convert value to list and append
        """
        if key in adict:
            if type(adict[key]) != list:
                adict[key] = [adict[key]]
            adict[key].append(val)
        else:
            adict[key] = val

    return ttree_to_json(dlist)


def dict_to_rcp(d: dict, level: int=0):
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{'    '*level}{k}:")
            lines.append(dict_to_rcp(v, level + 1))
        else:
            lines.append(f"{'    '*level}{k}: {str(v).strip()}")
    return "\n".join(lines)



class Decision(object):
    "Sample-process grouping class."
    def __init__(self, inputdict: dict=None, orch_name: str='orchestrator', decision_label: str='nolabel', decision_enum: int=None, access: str='hte'):
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.orch_name = imports.get('orch_name', orch_name)
        self.decision_uuid = imports.get('decision_uuid', None)
        self.decision_timestamp = imports.get('decision_timestamp', None)
        self.decision_label = imports.get('decision_label', decision_label)
        self.decision_enum = imports.get('decision_enum', decision_enum)
        self.access = imports.get('access', access)
        self.plate_id = imports.get('plate_id', None)
        self.sample_no = imports.get('sample_no', None)
        check_args = {"plate_id": self.plate_id, "sample_no": self.sample_no}
        missing_args = [k for k,v in check_args.items() if v is None]
        if missing_args:
            print(f'Decision {" and ".join(missing_args)} not specified. Placeholder decisions will only affect the decision queue enumeration.')
        if self.decision_uuid is None and self.action.name:
            self.get_uuid()
    def as_dict(self):
        return vars(self)
    def get_uuid(self, orch_name: str='orchestrator'):
        "server_name can be any string used in generating random uuid"
        if self.decision_uuid:
            print(f'decision_uuid: {self.decision_uuid} already exists')
        else:
            self.decision_uuid = gen_uuid(self.orch_name)
            print(f'decision_uuid: {self.decision_uuid} assigned')
    def set_dtime(self):
        self.decision_timestamp = strftime("%Y%m%d.%H%M%S")


class Action(Decision):
    "Sample-process identifier class."
    def __init__(self, inputdict: dict=None, action_server: str=None, action_name: str=None, action_params: dict={}, action_enum: int=None, action_abbr: str=None, save_rcp: bool=False, save_datastream=None, start_condition: int=3):
        super().__init__(inputdict) # grab decision keys
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.action_uuid = imports.get('action_uuid', None)
        self.action_timestamp = imports.get('action_timestamp', None)
        self.action_server = imports.get('action_server', action_server)
        self.action_name = imports.get('action_name', action_name)
        self.action_params = imports.get('action_params', action_params)
        self.action_enum = imports.get('action_enum', action_enum)
        self.action_abbr = imports.get('action_abbr', action_abbr)
        self.save_rcp = imports.get('save_rcp', save_rcp)
        self.save_datastream = imports.get('save_datastream', save_datastream)
        self.start_condition = imports.get('start_condition', start_condition)
        self.file_dict = defaultdict(lambda: defaultdict(dict))
        self.file_dict.update(imports.get('file_dict', {}))
        self.file_paths = imports.get('file_paths', [])
        self.data = imports.get('data', [])
        # reassign these if specified in input
        self.plate_id = imports.get('plate_id', self.plate_id)
        self.sample_no = imports.get('sample_no', self.sample_no)
        check_args = {"server": self.action_server, "name": self.action_name}
        missing_args = [k for k,v in check_args.items() if v is None]
        if missing_args:
            print(f'Action {" and ".join(missing_args)} not specified. Placeholder actions will only affect the action queue enumeration.')
        if self.action_uuid is None and self.action_name:
            self.get_uuid()
    def get_uuid(self):
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
    def __init__(self, server_name: str, fastapp: FastAPI, save_root: str, technique_name: Optional[str]=None, calibration: dict={}):
        self.hostname = gethostname()
        self.server_name = server_name
        self.technique_name = server_name if technique_name is None else technique_name
        self.calibration = calibration
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
        self.get_fast_endpoints(fastapp)
        
    def get_fast_endpoints(self, app: FastAPI):
        "Populate status dict with FastAPI server endpoints for monitoring."
        self.status = {route.name: [] for route in app.routes if route.path.startswith(f'/{self.server_name}')}
        print(f"Found {len(self.status)} endpoints for status monitoring.")
    
    def get_ntp_time(self):
        "Check system clock against NIST clock for trigger operations."
        c = ntplib.NTPClient()
        response = c.request(self.ntp_server, version=3)
        self.ntp_response = response
        self.ntp_last_sync = response.orig_time
        self.ntp_offset = response.offset
        open('ntpLastSync.txt', 'w').write(self.ntp_last_sync)
        print(f"retrieved time at {ctime(self.ntp_response.tx_timestamp)} from {self.ntp_server}")
        
    def attach_client(self, client_addr: str):
        "Add client for pushing status updates via HTTP POST."
        self.status_clients.add(client_addr)
        print(f"Added {client_addr} to status subscriber list.")
   
    def detach_client(self, client_addr: str):
        "Remove client from receiving status updates via HTTP POST"
        self.status_clients.remove(client_addr)
        
    async def ws_status(self, websocket: WebSocket):
        "Subscribe to status queue and send message to websocket client."
        await websocket.accept()
        try:
            async for status_msg in self.status_q.subscribe():
                await websocket.send_text(json.dumps(status_msg))
        except WebSocketDisconnect:
            print(f"Status websocket client {websocket.client[0]}:{websocket.client[1]} disconnected.")
        
    async def ws_data(self, websocket: WebSocket):
        "Subscribe to data queue and send messages to websocket client."
        await websocket.accept()
        try:
            async for data_msg in self.data_q.subscribe():
                await websocket.send_text(json.dumps(data_msg))
        except WebSocketDisconnect:
            print(f"Data websocket client {websocket.client[0]}:{websocket.client[1]} disconnected.")

    async def log_status_task(self, retry_limit: int=5):
        "Self-subscribe to status queue, log status changes, POST to clients."
        async for status_msg in self.status_q.subscribe():
            self.status = status_msg
            for client_addr in self.status_clients:
                async with aiohttp.ClientSession() as session:
                    success = False
                    for _ in range(retry_limit):
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
                            
    async def detach_subscribers(self):
        await self.status_q.put(StopAsyncIteration)
        await self.data_q.put(StopAsyncIteration)
        await asyncio.sleep(5)
    
    async def log_data_task(self):
        "Self-subscribe to data queue, write to present file path."
        async for data_msg in self.data_q.subscribe():
            # dataMsg should be a list of values or a list of list of values
            if isinstance(data_msg[0], list):
                lines = "\n".join([",".join([str(x) for x in l]) for l in data_msg])
                self.data += data_msg
            else:
                lines = ",".join([str(x) for x in data_msg])
                self.data.append(data_msg)
            if self.file_conn:
                await self.write_live_data(lines)
    
    async def sync_ntp_task(self, resync_time: int=600):
        "Regularly sync with NTP server."
        while True:
            if time() - self.ntp_last_sync > resync_time:
                self.get_ntp_time()
            else:
                await asyncio.sleep(0.5)
    
    async def set_output_file(self, filename: str, header: Optional[str]=None):
        "Set active save_path, write header if supplied."
        output_path = os.path.join(self.active.output_dir, filename)
        # create output file and set connection
        self.file_conn = await aiofiles.open(output_path, mode="a+")
        if header:
            if not header.endswith("\n"):
                header += "\n"
            await self.file_conn.write(header)

    async def write_live_data(self, output_str: str):
        "Appends lines to file_conn."
        if self.file_conn:
            if not output_str.endswith("\n"):
                output_str += "\n"
            await self.file_conn.write(output_str)
                 
    async def write_file(self, file_type: str, filename: str, output_str: str, header: Optional[str]=None):
        "Write complete file, not used with queue streaming."
        _output_path = os.path.join(self.active.output_dir, filename)           
        # create output file and set connection
        file_instance = await aiofiles.open(_output_path, mode="w")
        numlines = len(output_str.split('\n'))
        if header:
            header_lines = len(header.split('\n'))
            header_parts = ','.join(header.split('\n')[-1].replace(",", "\t").split())
            file_info = f'{file_type};{header_parts};{header_lines};{numlines};{self.active.sample_no}'
            if not header.endswith("\n"):
                header += "\n"
            output_str = header + output_str
        else:
            file_info = f'{file_type};{numlines};{self.active.sample_no}'
        await file_instance.write(output_str)
        await file_instance.close()
        self.active.file_dict[self.active.filetech_key]["aux_files"].update({filename: file_info})
        print(f"Wrote {numlines} lines to {_output_path}")
        

    async def setup_act(self, action: Action, file_type:str='stream_csv', file_group:str='stream_files', filename: Optional[str]=None, header:Optional[str]=None):
        "Populate active decision, set active file connection, write initial rcp, set endpoint status."
        self.active = action
        self.active.set_atime()
        decision_date = self.active.decision_timestamp.split('.')[0]
        decision_time = self.active.decision_timestamp.split('.')[-1]
        year_week = strftime("%y.%U", strptime(decision_date, "%Y%m%d"))
        self.active.output_dir = os.path.join(self.save_root,
                                                 year_week,
                                                 decision_date,
                                                 f"{decision_time}_{self.active.decision_label}",
                                                 f"{self.active.action_timestamp}__{self.active.action_uuid}"
                                                 )
        if self.active.save_rcp:
            os.makedirs(self.active.output_dir, exist_ok=True)
            self.active.actionnum = f"{self.active.action_abbr}{self.active.action_enum}"
            self.active.filetech_key = f"files_technique__{self.active.actionnum}"
            initial_dict = {
                "technique_name": self.technique_name,
                "server_name": self.server_name,
                "orchestrator": self.orch_name,
                "machine": self.hostname,
                "access": self.active.access,
                "plate_id": self.active.plate_id,
                "output_dir": self.active.output_dir,
            }
            if self.calibration:
                initial_dict.update(self.calibration)
            initial_dict.update({
                "decision_uuid": self.active.decision_uuid,
                "decision_enum": self.active.decision_enum,
                "action_uuid": self.active.action_uuid,
                "action_enum": self.active.action_enum,
                "action_name": self.active.action_name,
                f"{self.technique_name}_params__{self.active.actionnum}": self.active.action_params
            })
            await self.write_to_rcp(initial_dict)
            if self.active.save_datastream is not False:
                if header:
                    if isinstance(header, list):
                        header_lines = len(header)
                        header = "\n".join(header)
                    else:
                        header_lines = len(header.split('\n'))
                    header_parts = ','.join(header.split('\n')[-1].replace(",", "\t").split())
                    file_info = f'{file_type};{header_parts};{header_lines};{self.active.sample_no}'
                else:
                    file_info = f'{file_type};{self.active.sample_no}'
                if filename is None: # generate filename
                    filename = f"act{self.active.action_enum:02}_{self.active.action_abbr}__{self.active.plate_id}_{self.active.sample_no}.csv"
                self.active.file_dict[self.active.filetech_key][file_group].update({filename: file_info})
                await self.set_output_file(filename, header)


    async def write_to_rcp(self, rcp_dict: dict):
        "Create new rcp if it doesn't exist, otherwise append rcp_dict to file."
        output_path = os.path.join(self.active.output_dir, f"{self.active.action_timestamp}.rcp")           
        output_str = dict_to_rcp(rcp_dict)
        file_instance = await aiofiles.open(output_path, mode="a+")
        await file_instance.write(output_str)
        await file_instance.close()       
    
    async def finish_act(self):
        "Close file_conn, finish rcp, copy aux, set endpoint status, and move active dict to past."
        if self.file_conn:
            await self.file_conn.close()
            self.file_conn = None
        if self.active.file_dict:
            await self.write_to_rcp(self.active.file_dict)
        self.last = copy(self.active)
        self.active = None
        await self.status_q.put('idle')
        
    async def track_file(self, file_type: str, file_path: str):
        "Add auxiliary files to file dictionary."
        if os.path.dirname(file_path) != self.active.output_dir:
            self.active.file_paths.append(file_path)
        file_info = f"{file_type};{self.active.sample_no}"
        filename = os.path.basename(file_path)
        self.active.file_dict[self.active.filetech_key]["aux_files"].update({filename: file_info})
        print(f"{filename} added to files_technique__{self.active.actionnum} / aux_files list.")
    
    async def relocate_files(self):
        "Copy auxiliary files from folder path to rcp directory."
        for x in self.active.file_paths:
            new_path = os.path.join(self.active.output_dir, os.path.basename(x))
            await async_copy(x, new_path)
        


class Orch(Base):#TODO
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
    def __init__(self, server_name: str, fastapp: FastAPI, save_root: str=None):
        super.__init__(server_name, fastapp, save_root)
    
    
class ActiveLearningOrch(Orch):
    """Orchestrator with active learning support.
    
    Provide new endpoints for:
      1) setting parameters to be active-learned
      2) setting initial condition, AL method (RF or GP) and acquisition params
      3) setting final condition
    
    End of action|experiment queue will yield an objective metric and uncertainty for
    entire decision space, populating decision queue with next acquired decision point.
    
    """
    def __init__(self, server_name: str, fastapp: FastAPI, save_root: str=None):
        super.__init__(server_name, fastapp, save_root)