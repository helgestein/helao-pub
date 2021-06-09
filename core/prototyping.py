from importlib import import_module
import os
import sys
import json
import uuid
import shutil
from copy import copy
from collections import defaultdict, deque
from socket import gethostname
from time import ctime, time, strftime, strptime 
from datetime import datetime
from typing import Optional, List, Union

import shortuuid
import ntplib
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import wrap
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from classes import MultisubscriberQueue
import zipfile

async_copy = wrap(shutil.copy)


def gen_uuid(label: str, trunc: int = 8):
    "Generate a uuid, encode with larger character set, and trucate."
    uuid1 = uuid.uuid1()
    uuid3 = uuid.uuid3(uuid.NAMESPACE_URL, f"{uuid1}-{label}")
    short = shortuuid.encode(uuid3)[:trunc]
    return short


def rcp_to_dict(rcppath: str):  # read common info/rcp/exp/ana structure into dict
    dlist = []

    def tab_level(astr):
        """Count number of leading tabs in a string"""
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


def dict_to_rcp(d: dict, level: int = 0):
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

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        orch_name: str = "orchestrator",
        decision_label: str = "nolabel",
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.orch_name = imports.get("orch_name", orch_name)
        self.decision_uuid = imports.get("decision_uuid", None)
        self.decision_timestamp = imports.get("decision_timestamp", None)
        self.decision_label = imports.get("decision_label", decision_label)
        self.access = imports.get("access", access)
        self.actual = imports.get("actual", actualizer)
        self.actual_pars = imports.get("actual_pars", actual_pars)
        self.result_dict = imports.get("result_dict", result_dict)
        if self.decision_uuid is None and self.action.name:
            self.get_uuid()

    def as_dict(self):
        return vars(self)

    def gen_uuid(self, orch_name: str = "orchestrator"):
        "server_name can be any string used in generating random uuid"
        if self.decision_uuid:
            print(f"decision_uuid: {self.decision_uuid} already exists")
        else:
            self.decision_uuid = gen_uuid(self.orch_name)
            print(f"decision_uuid: {self.decision_uuid} assigned")

    def set_dtime(self, offset: float = 0):
        dtime = datetime.now()
        dtime = datetime.fromtimestamp(dtime.timestamp() + offset)
        self.decision_timestamp = dtime.strftime("%Y%m%d.%H%M%S%f")


class Action(Decision):
    "Sample-process identifier class."

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        action_server: str = None,
        action_name: str = None,
        action_params: dict = {},
        action_enum: int = None,
        action_abbr: str = None,
        save_rcp: bool = False,
        save_data: bool = False,
        start_condition: Union[int, dict] = 3,
        plate_id: Optional[int] = None,
        sample_no: Optional[int] = None,
        samples_in: Optional[list] = None,
        samples_out: Optional[list] = None,
    ):
        super().__init__(inputdict)  # grab decision keys
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.action_uuid = imports.get("action_uuid", None)
        self.action_timestamp = imports.get("action_timestamp", None)
        self.action_server = imports.get("action_server", action_server)
        self.action_name = imports.get("action_name", action_name)
        self.action_params = imports.get("action_params", action_params)
        self.action_enum = imports.get("action_enum", action_enum)
        self.action_abbr = imports.get("action_abbr", action_abbr)
        self.save_rcp = imports.get("save_rcp", save_rcp)
        self.save_data = imports.get("save_data", save_data)
        self.start_condition = imports.get("start_condition", start_condition)
        self.plate_id = imports.get("plate_id", plate_id)
        self.sample_no = imports.get("sample_no", sample_no)
        self.samples_in = imports.get("samples_in", samples_in)
        self.samples_out = imports.get("samples_out", samples_out)
        self.file_dict = defaultdict(lambda: defaultdict(dict))
        self.file_dict.update(imports.get("file_dict", {}))
        self.file_paths = imports.get("file_paths", [])
        self.data = imports.get("data", [])
        check_args = {"server": self.action_server, "name": self.action_name}
        missing_args = [k for k, v in check_args.items() if v is None]
        if missing_args:
            print(
                f'Action {" and ".join(missing_args)} not specified. Placeholder actions will only affect the action queue enumeration.'
            )
        if self.action_uuid is None and self.action_name:
            self.get_uuid()

    def gen_uuid(self):
        if self.action_uuid:
            print(f"action_uuid: {self.action_uuid} already exists")
        else:
            self.action_uuid = gen_uuid(self.action_name)
            print(f"action_uuid: {self.action_uuid} assigned")

    def set_atime(self, offset: float = 0):
        atime = datetime.now()
        atime = datetime.fromtimestamp(atime.timestamp() + offset)
        self.action_timestamp = atime.strftime("%Y%m%d.%H%M%S%f")


class HelaoFastAPI(FastAPI):
    """Standard FastAPI class with HELAO config attached for simpler import."""

    def __init__(self, helao_cfg: dict, helao_srv: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helao_cfg = helao_cfg
        self.helao_srv = helao_srv


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

    def __init__(
        self,
        fastapp: HelaoFastAPI,
        technique_name: Optional[str] = None,
        save_root: Optional[str] = None,
        calibration: dict = {},
    ):
        self.server_name = fastapp.helao_srv
        self.server_cfg = fastapp.helao_cfg["servers"][self.server_name]
        self.world_cfg = fastapp.helao_cfg
        self.hostname = gethostname()

        if "technique_name" in self.server_cfg.keys() and technique_name is None:
            print(
                f" ... Found technique_name in config: {self.server_cfg['technique_name']}"
            )
            self.technique_name = self.server_cfg["technique_name"]
        else:
            self.technique_name = (
                self.server_name if technique_name is None else technique_name
            )

        self.calibration = calibration
        if "save_root" in self.server_cfg.keys():
            print(
                f" ... Found root save directory in config: {self.server_cfg['save_root']}"
            )
            self.save_root = self.server_cfg["save_root"]
        if save_root:
            print(f" ... Root save directory was specified: {save_root}.")
            if self.save_root:
                print(" ... Overriding 'save_root' specified in config.")
            self.save_root = save_root
        if not self.save_root:
            print(
                " ... Warning: root save directory was not defined. Logs, RCPs, and data will not be written."
            )
        else:
            if not os.path.isdir(self.save_root):
                print(
                    " ... Warning: root save directory was specified but does not exist. Logs, RCPs, and data will not be written."
                )
                self.save_root = None
        self.actives = {}
        self.status = {}
        self.endpoints = []
        self.status_q = MultisubscriberQueue()
        self.data_q = MultisubscriberQueue()
        self.status_clients = set()
        self.ntp_server = "time.nist.gov"
        self.ntp_response = None
        self.ntp_offset = None  # add to system time for correction
        self.ntp_last_sync = None
        if os.path.exists("ntpLastSync.txt"):
            tmps = open("ntpLastSync.txt", "r").readlines() 
            if len(tmps) > 0:
                self.ntp_last_sync = tmps[0].strip()
            else:
                self.ntp_last_sync = None    
        elif self.ntp_last_sync is None:
            asyncio.gather(self.get_ntp_time())
        self.init_endpoint_status(fastapp)
        self.fast_urls = self.get_endpoint_urls(fastapp)
        self.status_logger = asyncio.create_task(self.log_status_task())
        self.ntp_syncer = asyncio.create_task(self.sync_ntp_task())

    def init_endpoint_status(self, app: FastAPI):
        "Populate status dict with FastAPI server endpoints for monitoring."
        for route in app.routes:
            if route.path.startswith(f"/{self.server_name}"):
                self.status[route.name] = []
                self.endpoints.append(route.name)
        print(f" ... Found {len(self.status)} endpoints for status monitoring.")

    async def add_status(self, act_name: str, act_uuid: str):
        self.status[act_name].append(act_uuid)
        print(f" ... Added {act_uuid} to {act_name} status list.")
        await self.status_q.put({act_name: self.status[act_name]})

    async def clear_status(self, act_name: str, act_uuid: str):
        self.status[act_name].remove(act_uuid)
        print(f" ... Removed {act_uuid} from {act_name} status list.")
        await self.status_q.put({act_name: self.status[act_name]})

    async def set_estop(self, act_name: str, act_uuid: str):
        self.status[act_name].remove(act_uuid)
        self.status[act_name].append(f"{act_uuid}__estop")
        print(f" ... E-STOP {act_uuid} on {act_name} status.")
        await self.status_q.put({act_name: self.status[act_name]})

    def get_endpoint_urls(self, app: HelaoFastAPI):
        """Return a list of all endpoints on this server."""
        url_list = []
        for route in app.routes:
            routeD = {"path": route.path, "name": route.name}
            if "dependant" in dir(route):
                flatParams = get_flat_params(route.dependant)
                paramD = {
                    par.name: {
                        "outer_type": str(par.outer_type_).split("'")[1],
                        "type": str(par.type_).split("'")[1],
                        "required": par.required,
                        "shape": par.shape,
                        "default": par.default,
                    }
                    for par in flatParams
                }
                routeD["params"] = paramD
            else:
                routeD["params"] = []
            url_list.append(routeD)
        return url_list

    async def get_ntp_time(self):
        "Check system clock against NIST clock for trigger operations."
        c = ntplib.NTPClient()
        response = c.request(self.ntp_server, version=3)
        self.ntp_response = response
        self.ntp_last_sync = response.orig_time
        self.ntp_offset = response.offset
        time_inst = await aiofiles.open("ntpLastSync.txt", "w")
        await time_inst.write(str(self.ntp_last_sync))
        await time_inst.close()
        print(
            f" ... retrieved time at {ctime(self.ntp_response.tx_timestamp)} from {self.ntp_server}"
        )

    async def attach_client(self, client_addr: str, retry_limit=5):
        "Add client for pushing status updates via HTTP POST."
        if client_addr in self.status_clients:
            print(f" ... Client {client_addr} is already subscribed to status updates.")
        else:
            self.status_clients.add(client_addr)
            print(f"Added {client_addr} to status subscriber list.")
            current_status = self.status
            async with aiohttp.ClientSession() as session:
                success = False
                for _ in range(retry_limit):
                    async with session.post(
                        f"http://{client_addr}/update_status",
                        params={"server": self.server_name, "status": current_status},
                    ) as resp:
                        response = await resp
                    if response.status < 400:
                        success = True
                        break
                if success:
                    print(
                        f" ... Updated {self.server_name} status to {current_status} on {client_addr}."
                    )
                else:
                    print(
                        f" ... Failed to push status message to {client_addr} after {retry_limit} attempts."
                    )

    def detach_client(self, client_addr: str):
        "Remove client from receiving status updates via HTTP POST"
        if client_addr in self.status_clients:
            self.status_clients.remove(client_addr)
            print(f"Client {client_addr} will no longer receive status updates.")
        else:
            print(f" ... Client {client_addr} is not subscribed.")

    async def ws_status(self, websocket: WebSocket):
        "Subscribe to status queue and send message to websocket client."
        await websocket.accept()
        try:
            async for status_msg in self.status_q.subscribe():
                await websocket.send_text(json.dumps(status_msg))
        except WebSocketDisconnect:
            print(
                f" ... Status websocket client {websocket.client[0]}:{websocket.client[1]} disconnected."
            )

    async def ws_data(self, websocket: WebSocket):
        "Subscribe to data queue and send messages to websocket client."
        await websocket.accept()
        try:
            async for data_msg in self.data_q.subscribe():
                await websocket.send_text(json.dumps(data_msg))
        except WebSocketDisconnect:
            print(
                f" ... Data websocket client {websocket.client[0]}:{websocket.client[1]} disconnected."
            )

    async def log_status_task(self, retry_limit: int = 5):
        "Self-subscribe to status queue, log status changes, POST to clients."
        try:
            async for status_msg in self.status_q.subscribe():
                self.status.update(status_msg)
                for client_addr in self.status_clients:
                    async with aiohttp.ClientSession() as session:
                        success = False
                        for _ in range(retry_limit):
                            async with session.post(
                                f"http://{client_addr}/update_status",
                                params={"server": self.server_name, "status": status_msg},
                            ) as resp:
                                response = await resp
                            if response.status < 400:
                                success = True
                                break
                    if success:
                        print(
                            f" ... Updated {self.server_name} status to {status_msg} on {client_addr}."
                        )
                    else:
                        print(
                            f" ... Failed to push status message to {client_addr} after {retry_limit} attempts."
                        )
                # TODO:write to log if save_root exists
        except asyncio.CancelledError:
            print(" ... status logger task was cancelled")

    async def detach_subscribers(self):
        await self.status_q.put(StopAsyncIteration)
        await self.data_q.put(StopAsyncIteration)
        await asyncio.sleep(5)

    async def sync_ntp_task(self, resync_time: int = 600):
        "Regularly sync with NTP server."
        try:
            while True:
                time_inst = await aiofiles.open("ntpLastSync.txt", "r")
                ntp_last_sync = await time_inst.readline()
                await time_inst.close()
                self.ntp_last_sync = float(ntp_last_sync.strip())
                if time() - self.ntp_last_sync > resync_time:
                    self.get_ntp_time()
                else:
                    wait_time = time() - self.ntp_last_sync
                    await asyncio.sleep(wait_time)
        except asyncio.CancelledError:
            print(" ... ntp sync task was cancelled")

    async def shutdown(self):
        await self.detach_subscribers()
        self.status_logger.cancel()
        self.ntp_syncer.cancel()

    class Active(object):
        """Active action holder which wraps data queing and rcp writing."""

        async def __init__(
            self,
            base,  # outer instance
            action: Action,
            file_type: str = "stream_csv",
            file_group: str = "stream_files",
            filename: Optional[str] = None,
            header: Optional[str] = None,
        ):
            self.base = base
            self.active = action
            self.header = header
            self.column_names = [x.strip() for x in header.split("\n")[-1].replace("%columns=", "").replace("\t", ",").split(",")]
            self.active.set_atime(offset=self.base.ntp_offset)
            self.file_conn = None
            decision_date = self.active.decision_timestamp.split(".")[0]
            decision_time = self.active.decision_timestamp.split(".")[-1]
            year_week = strftime("%y.%U", strptime(decision_date, "%Y%m%d"))
            if not self.base.save_root:
                print(" ... Root save directory not specified, cannot save action results.")
                self.active.save_data = False
                self.active.save_rcp = False
                self.active.output_dir = None
            else:
                self.active.output_dir = os.path.join(
                    self.base.save_root,
                    year_week,
                    decision_date,
                    f"{decision_time}_{self.active.decision_label}",
                    f"{self.active.action_timestamp}__{self.active.action_uuid}",
                )
            if self.active.save_rcp:
                os.makedirs(self.active.output_dir, exist_ok=True)
                self.active.actionnum = (
                    f"{self.active.action_abbr}{self.active.action_enum}"
                )
                self.active.filetech_key = f"files_technique__{self.active.actionnum}"
                initial_dict = {
                    "technique_name": self.base.technique_name,
                    "server_name": self.base.server_name,
                    "orchestrator": self.base.orch_name,
                    "machine": self.base.hostname,
                    "access": self.active.access,
                    "plate_id": self.active.plate_id,
                    "output_dir": self.active.output_dir,
                }
                initial_dict.update(self.calibration)
                initial_dict.update(
                    {
                        "decision_uuid": self.active.decision_uuid,
                        "decision_enum": self.active.decision_enum,
                        "action_uuid": self.active.action_uuid,
                        "action_enum": self.active.action_enum,
                        "action_name": self.active.action_name,
                        f"{self.technique_name}_params__{self.active.actionnum}": self.active.action_params,
                    }
                )
                await self.write_to_rcp(initial_dict)
                if self.active.save_data:
                    if header:
                        if isinstance(header, list):
                            header_lines = len(header)
                            header = "\n".join(header)
                        else:
                            header_lines = len(header.split("\n"))
                        header_parts = ",".join(
                            header.split("\n")[-1].replace(",", "\t").split()
                        )
                        file_info = f"{file_type};{header_parts};{header_lines};{self.active.sample_no}"
                    else:
                        file_info = f"{file_type};{self.active.sample_no}"
                    if filename is None:  # generate filename
                        filename = f"act{self.active.action_enum:02}_{self.active.action_abbr}__{self.active.plate_id}_{self.active.sample_no}.csv"
                    self.active.file_dict[self.active.filetech_key][file_group].update(
                        {filename: file_info}
                    )
                    await self.set_output_file(filename, header)
                    # self.data_streamer = asyncio.create_task(self.transfer_data())
            await self.base.add_status(self.active.action_name, self.active.action_uuid)
            self.data_logger = asyncio.create_task(self.log_data_task())
            self.base.actives[self.active.action_uuid] = self.active.as_dict()
            
        # async def transfer_data(self):
        #     "Transfers queue data from driver class to Base class multisubscriber queue."
        #     try:
        #         while True:
        #             data_msg = await self.datastream.get()
        #             await self.base.data_q.put(data_msg)
        #     except asyncio.CancelledError:
        #         print("data streamer was cancelled")

        async def set_output_file(self, filename: str, header: Optional[str] = None):
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

        async def enqueue_data(self, data):
            data_msg = {self.active.action_uuid: data}
            await self.base.data_q.put(data_msg)

        async def log_data_task(self):
            "Self-subscribe to data queue, write to present file path."
            try:
                async for data_msg in self.base.data_q.subscribe():
                    # dataMsg should be a dict {uuid: list of values or a list of list of values}
                    if (
                        self.active.action_uuid in data_msg.keys()
                    ):  # only write data for this action
                        data_val = data_msg[self.active.action_uuid]
                        if isinstance(data_val, list):
                            lines = "\n".join(
                                [",".join([str(x) for x in l]) for l in data_val]
                            )
                            self.active.data += data_msg
                        elif isinstance(data_val, dict):
                            columns = [data_val[col] for col in self.column_names]
                            lines = "\n".join(
                                [",".join([str(x) for x in l]) for l in zip(*columns)]
                            )
                        else:
                            lines = ",".join([str(x) for x in data_msg])
                            self.active.data.append(data_msg)
                        if self.file_conn:
                            await self.write_live_data(lines)
            except asyncio.CancelledError:
                print(" ... data logger task was cancelled")

        async def write_file(
            self,
            file_type: str,
            filename: str,
            output_str: str,
            header: Optional[str] = None,
            sample_str: Optional[str] = None,
        ):
            "Write complete file, not used with queue streaming."
            _output_path = os.path.join(self.active.output_dir, filename)
            # create output file and set connection
            file_instance = await aiofiles.open(_output_path, mode="w")
            numlines = len(output_str.split("\n"))
            if header:
                header_lines = len(header.split("\n"))
                header_parts = ",".join(
                    header.split("\n")[-1].replace(",", "\t").split()
                )
                file_info = ";".join(
                    [
                        f"{x}"
                        for x in (
                            file_type,
                            header_parts,
                            header_lines,
                            numlines,
                            sample_str,
                        )
                    ]
                )
                if not header.endswith("\n"):
                    header += "\n"
                output_str = header + output_str
            else:
                file_info = ";".join(
                    [f"{x}" for x in (file_type, numlines, sample_str)]
                )
            await file_instance.write(output_str)
            await file_instance.close()
            self.active.file_dict[self.active.filetech_key]["aux_files"].update(
                {filename: file_info}
            )
            print(f" ... Wrote {numlines} lines to {_output_path}")

        async def write_to_rcp(self, rcp_dict: dict):
            "Create new rcp if it doesn't exist, otherwise append rcp_dict to file."
            output_path = os.path.join(
                self.active.output_dir, f"{self.active.action_timestamp}.rcp"
            )
            output_str = dict_to_rcp(rcp_dict)
            file_instance = await aiofiles.open(output_path, mode="a+")
            await file_instance.write(output_str)
            await file_instance.close()

        async def finish(self):
            "Close file_conn, finish rcp, copy aux, set endpoint status, and move active dict to past."
            if self.file_conn:
                await self.file_conn.close()
                self.file_conn = None
                # self.data_streamer.cancel()
            if self.active.file_dict:
                await self.write_to_rcp(self.active.file_dict)
            await self.base.clear_status(
                self.active.action_name, self.active.action_uuid
            )
            self.data_logger.cancel()
            _ = self.base.actives.pop(self.active.action_uuid, None)
            return self.active

        async def track_file(self, file_type: str, file_path: str):
            "Add auxiliary files to file dictionary."
            if os.path.dirname(file_path) != self.active.output_dir:
                self.active.file_paths.append(file_path)
            file_info = f"{file_type};{self.active.sample_no}"
            filename = os.path.basename(file_path)
            self.active.file_dict[self.active.filetech_key]["aux_files"].update(
                {filename: file_info}
            )
            print(
                f" ... {filename} added to files_technique__{self.active.actionnum} / aux_files list."
            )

        async def relocate_files(self):
            "Copy auxiliary files from folder path to rcp directory."
            for x in self.active.file_paths:
                new_path = os.path.join(self.active.output_dir, os.path.basename(x))
                await async_copy(x, new_path)

    async def contain_action(
        self,
        action: Action,
        file_type: str = "stream_csv",
        file_group: str = "stream_files",
        filename: Optional[str] = None,
        header: Optional[str] = None,
    ):
        self.actives[action.action_uuid] = await Base.Active(
            self, action, file_type, file_group, filename, header
        )
        return self.actives[action.action_uuid]

    async def get_active_info(self, action_uuid: str):
        if action_uuid in self.actives.keys():
            action_dict = await self.actives[action_uuid].active.as_dict()
            return action_dict
        else:
            print(f" ... Specified action uuid {action_uuid} was not found.")
            return None


class Orch(Base):
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

    def __init__(
        self,
        fastapp: HelaoFastAPI,
        technique_name: Optional[str] = None,
        save_root: Optional[str] = None,
    ):
        super().__init__(fastapp, technique_name, save_root)
        self.import_actualizers()
        # instantiate decision/experiment queue, action queue
        self.decisions = deque([])
        self.actions = deque([])
        self.active_decision = None
        self.last_decision = None
        self.global_status = defaultdict(lambda: defaultdict(list))
        self.global_q = MultisubscriberQueue()  # passes global_status dicts

        # global state of all instruments as string [idle|busy] independent of dispatch loop
        self.global_state = None

        self.init_success = False  # need to subscribe to all fastapi servers in config
        self.loop_state = "stopped"  # present dispatch loop state [started|stopped]

        # separate from global state, signals dispatch loop control [skip|stop|None]
        self.loop_intent = None
        self.loop_task = None
        self.status_subscriber = asyncio.create_task(self.subscribe_all())
        

    def import_actualizers(self, library_path: str = None):
        """Import actualizer functions into environment."""
        if library_path is None:
            if "action_library_path" not in self.world_cfg.keys():
                print(
                    " ... library_path argument not specified and key is not present in config."
                )
                return False
            library_path = self.world_cfg["action_library_path"]
        if not os.path.isdir(library_path):
            print(
                f" ... library path {library_path} was specified but is not a valid directory"
            )
            return False
        sys.path.append(library_path)
        self.action_lib = {}
        for actlib in self.world_cfg["action_libraries"]:
            tempd = import_module(actlib).__dict__
            self.action_lib.update({func: tempd[func] for func in tempd["ACTUALIZERS"]})
        print(
            f" ... imported {len(self.world_cfg['action_libraries'])} actualizers specified by config."
        )
        return True

    async def subscribe_all(self, retry_limit: int = 5):
        """Subscribe to all fastapi servers in config."""
        orch_addr = self.server_cfg["host"]
        orch_port = self.server_cfg["port"]
        fails = []
        for serv_key, serv_dict in self.world_cfg["servers"].items():
            if "fast" in serv_dict.keys():
                serv_addr = serv_dict["host"]
                serv_port = serv_dict["port"]
                async with aiohttp.ClientSession() as session:
                    success = False
                    for _ in range(retry_limit):
                        async with session.post(
                            f"http://{serv_addr}:{serv_port}/attach_client",
                            params={"client_addr": f"{orch_addr}:{orch_port}"},
                        ) as resp:
                            response = await resp
                        if response.status < 400:
                            success = True
                            break
                    if success:
                        print(f"Subscribed to {serv_key} at {serv_addr}:{serv_port}")
                    else:
                        fails.append(serv_key)
                        print(
                            f" ... Failed to subscribe to {serv_key} at {serv_addr}:{serv_port}. Check connection."
                        )
        if len(fails) == 0:
            self.init_success = True
        else:
            print(
                " ... Orchestrator cannot process decisions unless all FastAPI servers in config file are accessible."
            )

    async def update_status(self, act_serv: str, status_dict: dict):
        """Dict update method for action server to push status messages.

        Async task for updating orch status dict {act_serv_key: {act_name: [act_uuid]}}
        """
        last_dict = self.global_status[act_serv]
        for act_name, acts in status_dict.items():
            if set(acts) != set(last_dict[act_name]):
                started = set(acts).difference(last_dict[act_name])
                removed = set(last_dict[act_name]).difference(acts)
                ongoing = set(acts).intersection(last_dict[act_name])
                if removed:
                    print(f" ... {act_serv}:{act_name} finished {','.join(removed)}")
                if started:
                    print(f" ... {act_serv}:{act_name} started {','.join(started)}")
                if ongoing:
                    print(f" ... {act_serv}:{act_name} ongoing {','.join(ongoing)}")
        self.global_status[act_serv].update(status_dict)
        await self.global_q.put(self.global_status)

    async def update_global_state_task(self):
        """Self-subscribe to global_q and update status dict."""
        async for status_dict in self.global_q.subscribe():
            estop_uuids = []
            for act_serv, act_named in status_dict.items():
                for act_name, uuids in act_named.items():
                    for myuuid in uuids:
                        if uuid.endswith("__estop"):
                            estop_uuids.append((act_serv, act_name, myuuid))
            running_states, _ = self.check_global_state()
            if estop_uuids and self.loop_state=="started":
                await self.estop_loop()
            elif len(running_states) == 0:
                self.global_state = "idle"
            else:
                self.global_state = "busy"
                print(' ... ', running_states)

    def check_global_state(self):
        """Return global state of action servers."""
        running_states = []
        idle_states = []
        for act_serv, act_dict in self.global_status.items():
            for act_name, act_uuids in act_dict.items():
                if len(act_uuids) == 0:
                    idle_states.append(f"{act_serv}:{act_name}")
                else:
                    running_states.append(f"{act_serv}:{act_name}:{len(act_uuids)}")
        return running_states, idle_states

    async def async_dispatcher(self, A: Action):
        """Request non-blocking actions which may run concurrently.

        Send action object to action server for processing.

        Args:
            A: an action type object contain action server name, endpoint, parameters

        Returns:
            Response string from http POST request to action server
        """
        actd = self.world_cfg["servers"][A.action_server]
        act_addr = actd["host"]
        act_port = actd["port"]
        Adict = A.as_dict()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{act_addr}:{act_port}/{A.action_server}/{A.action_name}",
                params=Adict,
            ) as resp:
                response = await resp.text()
                return response

    async def dispatch_loop_task(self):
        """Parse decision and action queues, and dispatch actions while tracking run state flags."""
        print(" ... running operator orch")
        print(" ... orch status:", self.global_state)
        # clause for resuming paused action list
        print(" ... orch descisions: ", self.decisions)
        try:
            self.loop_state = "started"
            while self.loop_state == "started" and (self.actions or self.decisions):
                await asyncio.sleep(
                    0.001
                )  # allows status changes to affect between actions, also enforce unique timestamp
                if not self.actions:
                    print(" ... getting actions from new decision")
                    # generate uids when populating, generate timestamp when acquring
                    self.last_decision = copy(self.active_decision)
                    self.active_decision = self.decisions.popleft()
                    self.active_decision.set_dtime(offset=self.ntp_offset)
                    actual = self.active_decision.actual
                    # additional actualizer params should be stored in decision.actual_pars
                    unpacked_acts = self.action_lib[actual](self.active_decision)
                    for i, act in enumerate(unpacked_acts):
                        act.action_enum = i
                        # act.gen_uuid()
                    self.actions = deque(unpacked_acts)  # TODO:update actualizer code
                    print(" ... got ", self.actions)
                    print(" ... optional params ", self.active_decision.actual_pars)
                else:
                    if self.loop_intent == "stop":
                        print(" ... stopping orchestrator")
                        # monitor status of running actions, then end loop
                        async for _ in self.global_q.subscribe():
                            if self.global_state == "idle":
                                self.loop_state = "stopped"
                                await self.intend_none()
                                break
                    elif self.loop_intent == "skip":
                        # clear action queue, forcing next decision
                        self.actions.clear()
                        await self.intend_none()
                        print(" ... skipping to next decision")
                    else:
                        # all action blocking is handled like preempt, check Action requirements
                        A = self.actions.popleft()
                        # append previous results to current action
                        A.result_dict = self.active_decision.result_dict
                        # see async_dispatcher for unpacking
                        if isinstance(A.start_condition, int):
                            if A.start_condition == 0:
                                print(" ... orch is dispatching an unconditional action")
                            else:
                                if A.start_condition == 1:
                                    print(
                                        " ... orch is waiting for endpoint to become available"
                                    )
                                    async for _ in self.global_q.subscribe():
                                        endpoint_free = (
                                            len(
                                                self.global_status[A.action_server][
                                                    A.action_name
                                                ]
                                            )
                                            == 0
                                        )
                                        if endpoint_free:
                                            break
                                elif A.start_condition == 2:
                                    print(
                                        " ... orch is waiting for server to become available"
                                    )
                                    async for _ in self.global_q.subscribe():
                                        server_free = all(
                                            [
                                                len(uuid_list) == 0
                                                for _, uuid_list in self.global_status[
                                                    A.action_server
                                                ].items()
                                            ]
                                        )
                                        if server_free:
                                            break
                                else:  # start_condition is 3 or unsupported value
                                    print(" ... orch is waiting for all actions to finish")
                                    async for _ in self.global_q.subscribe():
                                        running_states, _ = self.check_global_state()
                                        global_free = len(running_states) == 0
                                        if global_free:
                                            break
                        elif isinstance(A.start_condition, dict):
                            print(
                                " ... waiting for multiple conditions on external servers"
                            )
                            condition_dict = A.start_condition
                            async for _ in self.global_q.subscribe():
                                conditions_free = all(
                                    [
                                        len(self.global_status[k][v] == 0)
                                        for k, vlist in condition_dict.items()
                                        if vlist and isinstance(vlist, list)
                                        for v in vlist
                                    ]
                                    + [
                                        len(uuid_list) == 0
                                        for k, v in condition_dict.items()
                                        if v == [] or v is None
                                        for _, uuid_list in self.global_status[k].items()
                                    ]
                                )
                                if conditions_free:
                                    break
                        else:
                            print(
                                " ... invalid start condition, waiting for all actions to finish"
                            )
                            async for _ in self.global_q.subscribe():
                                running_states, _ = self.check_global_state()
                                global_free = len(running_states) == 0
                                if global_free:
                                    break
                        print(f" ... dispatching action {A.action} on server {A.server}")
                        result = await self.async_dispatcher(A)
                        self.active_decision.result_dict[A.action_enum] = result
            print(" ... decision queue is empty")
            print(" ... stopping operator orch")
            self.loop_state = "stopped"
            await self.intend_none()
            return True
        except asyncio.CancelledError:
            return False

    async def start_loop(self):
        if self.loop_state == "stopped":
            self.loop_task = asyncio.create_task(self.dispatch_loop_task())
        elif self.loop_state == "E-STOP":
            print(" ... E-STOP flag was raised, clear E-STOP before starting.")
        else:
            print(" ... loop already started.")
        return self.loop_state

    async def estop_loop(self):
        self.loop_state = "E-STOP"
        self.loop_task.cancel()
        await self.force_stop_running_actions()
        await self.intend_none()

    async def force_stop_running_actions(self):
        running_uuids = []
        estop_uuids = []
        for act_serv, act_named in self.global_status.items():
            for act_name, uuids in act_named.items():
                for myuuid in uuids:
                    uuid_tup = (act_serv, act_name, myuuid)
                    if uuid.endswith("__estop"):
                        estop_uuids.append(uuid_tup)
                    else:
                        running_uuids.append(uuid_tup)
        running_servers = list(set([serv for serv, _, _ in running_uuids]))
        for serv in running_servers:
            serv_conf = self.world_cfg["servers"][serv]
            async with aiohttp.ClientSession() as session:
                print(f" ... Sending force-stop request to {serv}")
                async with session.post(
                    f"http://{serv_conf['host']}:{serv_conf['port']}/force_stop"
                ) as resp:
                    response = await resp.text()
                    print(response)

    async def intend_skip(self):
        await asyncio.sleep(0.001)
        self.loop_intent = "skip"

    async def intend_stop(self):
        await asyncio.sleep(0.001)
        self.loop_intent = "stop"

    async def intend_none(self):
        await asyncio.sleep(0.001)
        self.loop_intent = None
        
    async def clear_estop(self):
        running_uuids = []
        estop_uuids = []
        for act_serv, act_named in self.global_status.items():
            for act_name, uuids in act_named.items():
                for myuuid in uuids:
                    uuid_tup = (act_serv, act_name, myuuid)
                    if uuid.endswith("__estop"):
                        estop_uuids.append(uuid_tup)
                    else:
                        running_uuids.append(uuid_tup)
        cleared_status = copy(self.global_status)
        for serv,act,myuuid in estop_uuids:
            print(f" ... clearing E-STOP {act} on {serv}")
            cleared_status[serv][act] = cleared_status[serv][act].remove(myuuid)
        await self.global_q.put(cleared_status)
        print(" ... resetting dispatch loop state")
        self.loop_state = "stopped"
        print(f" ... {len(running_uuids)} running actions did not fully stop after E-STOP was raised")

    async def add_decision(
        self,
        decision_dict: dict = None,
        orch_name: str = None,
        decision_label: str = None,
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
        prepend=False,
    ):
        D = Decision(
            decision_dict,
            orch_name,
            decision_label,
            actualizer,
            actual_pars,
            result_dict,
            access,
        )
        # reminder: decision_dict values take precedence over keyword args but we grab
        # active or last decision label if decision_label is not specified
        if D.orch_name is None:
            D.orch_name = self.server_name
        if decision_label is None:
            if self.active_decision is not None:
                active_label = self.active_decision.decision_label
                print(
                    f" ... decision_label not specified, inheriting {active_label} from active decision"
                )
                D.decision_label = active_label
            elif self.last_decision is not None:
                last_label = self.last_decision.decision_label
                print(
                    f" ... decision_label not specified, inheriting {last_label} from previous decision"
                )
                D.decision_label = last_label
            else:
                print(
                    " ... decision_label not specified, no past decisions to inherit so using default 'nolabel"
                )
        await asyncio.sleep(0.001)
        if prepend:
            self.decisions.appendleft(D)
            print(f" ... decision {D.decision_uuid} prepended to queue")
        else:
            self.decisions.append(D)
            print(f" ... decision {D.decision_uuid} appended to queue")

    def list_decisions(self):
        """Return the current queue of decisions."""
        declist = [
            return_dec(
                index=i,
                uid=dec.decision_uuid,
                label=dec.decision_label,
                actualizer=dec.actual,
                pars=dec.actual_pars,
                access=dec.access,
            )
            for i, dec in enumerate(self.decisions)
        ]
        retval = return_declist(decisions=declist)
        return retval

    def get_decision(self, last=False):
        """Return the active or last decision."""
        if last:
            dec = self.last_decision
        else:
            dec = self.active_decision
        if dec is not None:
            declist = [
                return_dec(
                    index=-1,
                    uid=dec.decision_uuid,
                    label=dec.decision_label,
                    actualizer=dec.actual,
                    pars=dec.actual_pars,
                    access=dec.access,
                )
            ]
        else:
            declist = [
                return_dec(
                    index=-1,
                    uid=None,
                    label=None,
                    actualizer=None,
                    pars=None,
                    access=None,
                )
            ]
        retval = return_declist(decisions=declist)
        return retval

    def list_actions(self):
        """Return the current queue of actions."""
        actlist = [
            return_act(
                index=i,
                uid=act.action_uuid,
                server=act.action_server,
                action=act.action_name,
                pars=act.action_params,
                preempt=act.start_condition,
            )
            for i, act in enumerate(self.actions)
        ]
        retval = return_actlist(actions=actlist)
        return retval

    async def shutdown(self):
        await self.detach_subscribers()
        self.status_logger.cancel()
        self.ntp_syncer.cancel()
        self.status_subscriber.cancel()


class return_dec(BaseModel):
    """Return class for queried Decision objects."""

    index: int
    uid: str
    label: str
    actualizer: str
    pars: dict
    access: str


class return_declist(BaseModel):
    """Return class for queried Decision list."""

    decisions: List[return_dec]


class return_act(BaseModel):
    """Return class for queried Action objects."""

    index: int
    uid: str
    server: str
    action: str
    pars: dict
    preempt: int


class return_actlist(BaseModel):
    """Return class for queried Action list."""

    actions: List[return_act]