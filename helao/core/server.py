""" servers.py
Standard HelaoFastAPI action server and orchestrator classes.

"""
from importlib import import_module
import os
import sys
import json
import uuid
import shutil
from copy import copy
from collections import defaultdict, deque
from socket import gethostname
from time import ctime, time, strftime, strptime, time_ns
from typing import Optional, Union
from math import floor

import numpy as np
import ntplib
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import wrap
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.openapi.utils import get_flat_params

from helao.core.helper import MultisubscriberQueue, dict_to_rcp, eval_val
from helao.core.schema import Action, Decision
from helao.core.model import return_dec, return_declist, return_act, return_actlist

async_copy = wrap(shutil.copy)


class HelaoFastAPI(FastAPI):
    """Standard FastAPI class with HELAO config attached for simpler import."""

    def __init__(self, helao_cfg: dict, helao_srv: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helao_cfg = helao_cfg
        self.helao_srv = helao_srv


async def setupAct(action_dict: dict, request: Request, scope: dict):
    servKey, _, action_name = request.url.path.strip("/").partition("/")
    body_params = await request.json()
    param_names = list(body_params.keys()) + list(request.query_params.keys())
    scope.update(body_params)
    A = Action(action_dict, action_server=servKey, action_name=action_name)
    for k in param_names:
        if k not in A.action_params.keys() and k not in ["request", "action_dict"]:
            if scope[k] is not None:
                A.action_params[k] = scope[k]
            else:
                print(k, "is None")
    return A


def makeActServ(
    config, server_key, server_title, description, version, driver_class=None
):
    app = HelaoFastAPI(
        config, server_key, title=server_title, description=description, version=version
    )

    @app.on_event("startup")
    def startup_event():
        app.base = Base(app)
        if driver_class:
            app.driver = driver_class(app.base)

    @app.websocket("/ws_status")
    async def websocket_status(websocket: WebSocket):
        """Broadcast status messages.

        Args:
        websocket: a fastapi.WebSocket object
        """
        await app.base.ws_status(websocket)

    @app.websocket("/ws_data")
    async def websocket_data(websocket: WebSocket):
        """Broadcast status dicts.

        Args:
        websocket: a fastapi.WebSocket object
        """
        await app.base.ws_data(websocket)

    @app.post("/get_status")
    def status_wrapper():
        return app.base.status

    @app.post("/attach_client")
    async def attach_client(client_addr: str):
        await app.base.attach_client(client_addr)

    @app.post("/endpoints")
    def get_all_urls():
        """Return a list of all endpoints on this server."""
        return app.base.get_endpoint_urls(app)


    return app


def makeOrchServ(
    config, server_key, server_title, description, version, driver_class=None
):
    app = HelaoFastAPI(
        config, server_key, title=server_title, description=description, version=version
    )

    @app.on_event("startup")
    async def startup_event():
        """Run startup actions.

        When FastAPI server starts, create a global OrchHandler object, initiate the
        monitor_states coroutine which runs forever, and append dummy decisions to the
        decision queue for testing.
        """
        app.orch = Orch(app)
        if driver_class:
            app.driver = driver_class(app.orch)

    @app.post("/update_status")
    async def update_status(server: str, status: str):
        await app.orch.update_status(act_serv=server, status_dict=json.loads(status))

    @app.post(f"/attach_client")
    async def attach_client(client_addr: str):
        await app.orch.attach_client(client_addr)

    @app.websocket("/ws_status")
    async def websocket_status(websocket: WebSocket):
        """Subscribe to orchestrator status messages.

        Args:
        websocket: a fastapi.WebSocket object
        """
        await app.orch.ws_status(websocket)

    @app.websocket("/ws_data")
    async def websocket_data(websocket: WebSocket):
        """Subscribe to action server status dicts.

        Args:
        websocket: a fastapi.WebSocket object
        """
        await app.orch.ws_data(websocket)

    @app.post("/start")
    async def start_process():
        """Begin processing decision and action queues."""
        if app.orch.loop_state == "stopped":
            if (
                app.orch.action_dq or app.orch.decision_dq
            ):  # resume actions from a paused run
                await app.orch.start_loop()
            else:
                print("decision list is empty")
        else:
            print("already running")
        return {}

    @app.post("/estop")
    async def estop_process():
        """Emergency stop decision and action queues, interrupt running actions."""
        if app.orch.loop_state == "started":
            await app.orch.estop_loop()
        elif app.orch.loop_state == "E-STOP":
            print("orchestrator E-STOP flag already raised")
        else:
            print("orchestrator is not running")
        return {}

    @app.post("/stop")
    async def stop_process():
        """Stop processing decision and action queues after current actions finish."""
        if app.orch.loop_state == "started":
            await app.orch.intend_stop()
        elif app.orch.loop_state == "E-STOP":
            print("orchestrator E-STOP flag was raised; nothing to stop")
        else:
            print("orchestrator is not running")
        return {}

    @app.post("/clear_estop")
    async def clear_estop():
        """Remove emergency stop condition."""
        if app.orch.loop_state != "E-STOP":
            print("orchestrator is not currently in E-STOP")
        else:
            await app.orch.clear_estop()

    @app.post("/skip")
    async def skip_decision():
        """Clear the present action queue while running."""
        if app.orch.loop_state == "started":
            await app.orch.intend_skip()
        else:
            print("orchestrator not running, clearing action queue")
            await asyncio.sleep(0.001)
            app.orch.action_dq.clear()
        return {}

    @app.post("/clear_actions")
    async def clear_actions():
        """Clear the present action queue while stopped."""
        print("clearing action queue")
        await asyncio.sleep(0.001)
        app.orch.action_dq.clear()
        return {}

    @app.post("/clear_decisions")
    async def clear_decisions():
        """Clear the present decision queue while stopped."""
        print("clearing decision queue")
        await asyncio.sleep(0.001)
        app.orch.decision_dq.clear()
        return {}

    @app.post("/append_decision")
    async def append_decision(
        decision_dict: dict = None,
        orch_name: str = None,
        decision_label: str = None,
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        """Add a decision object to the end of the decision queue.

        Args:
        decision_dict: Decision parameters (optional), as dict.
        orch_name: Orchestrator server key (optional), as str.
        plate_id: The sample's plate id (no checksum), as int.
        sample_no: A sample number, as int.
        actualizer: The name of the actualizer for building the action list, as str.
        actual_pars: Actualizer parameters, as dict.
        result_dict: Action responses dict keyed by action_enum.
        access: Access control group, as str.

        Returns:
        Nothing.
        """
        await app.orch.add_decision(
            decision_dict,
            orch_name,
            decision_label,
            actualizer,
            actual_pars,
            result_dict,
            access,
            prepend=False,
        )
        return {}

    @app.post("/prepend_decision")
    async def prepend_decision(
        decision_dict: dict = None,
        orch_name: str = None,
        decision_label: str = None,
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        """Add a decision object to the start of the decision queue.

        Args:
        decision_dict: Decision parameters (optional), as dict.
        orch_name: Orchestrator server key (optional), as str.
        plate_id: The sample's plate id (no checksum), as int.
        sample_no: A sample number, as int.
        actualizer: The name of the actualizer for building the action list, as str.
        actual_pars: Actualizer parameters, as dict.
        result_dict: Action responses dict keyed by action_enum.
        access: Access control group, as str.

        Returns:
        Nothing.
        """
        await app.orch.add_decision(
            decision_dict,
            orch_name,
            decision_label,
            actualizer,
            actual_pars,
            result_dict,
            access,
            prepend=True,
        )
        return {}

    @app.post("/insert_decision")
    async def insert_decision(
        idx: int,
        decision_dict: dict = None,
        orch_name: str = None,
        decision_label: str = None,
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        """Insert a decision object at decision queue index.

        Args:
        idx: index in decision queue for insertion, as int
        decision_dict: Decision parameters (optional), as dict.
        orch_name: Orchestrator server key (optional), as str.
        plate_id: The sample's plate id (no checksum), as int.
        sample_no: A sample number, as int.
        actualizer: The name of the actualizer for building the action list, as str.
        actual_pars: Actualizer parameters, as dict.
        result_dict: Action responses dict keyed by action_enum.
        access: Access control group, as str.

        Returns:
        Nothing.
        """
        await app.orch.add_decision(
            decision_dict,
            orch_name,
            decision_label,
            actualizer,
            actual_pars,
            result_dict,
            access,
            at_index=idx,
        )
        return {}

    @app.post("/list_decisions")
    def list_decisions():
        """Return the current list of decisions."""
        return app.orch.list_decisions()

    @app.post("/active_decision")
    def active_decision():
        """Return the active decision."""
        return app.orch.get_decision(last=False)

    @app.post("/last_decision")
    def last_decision():
        """Return the last decision."""
        return app.orch.get_decision(last=True)

    @app.post("/list_actions")
    def list_actions():
        """Return the current list of actions."""
        return app.orch.list_actions()

    @app.post("/endpoints")
    def get_all_urls():
        """Return a list of all endpoints on this server."""
        return app.orch.get_endpoint_urls(app)

    @app.on_event("shutdown")
    def disconnect():
        """Run shutdown actions."""
        # emergencyStop = True
        time.sleep(0.75)

    return app


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
        self, fastapp: HelaoFastAPI, calibration: dict = {},
    ):
        self.server_name = fastapp.helao_srv
        self.server_cfg = fastapp.helao_cfg["servers"][self.server_name]
        self.world_cfg = fastapp.helao_cfg
        self.hostname = gethostname()
        self.save_root = None
        self.technique_name = None
        self.aloop = asyncio.get_running_loop()

        if "technique_name" in self.world_cfg.keys():
            print(
                f" ... Found technique_name in config: {self.world_cfg['technique_name']}"
            )
            self.technique_name = self.world_cfg["technique_name"]
        else:
            raise ValueError(
                "Missing 'technique_name' in config, cannot create server object."
            )

        self.calibration = calibration
        if "save_root" in self.world_cfg.keys():
            self.save_root = self.world_cfg["save_root"]
            print(
                f" ... Found root save directory in config: {self.world_cfg['save_root']}"
            )
            if not os.path.isdir(self.save_root):
                print(" ... Warning: root save directory does not exist. Creatig it.")
                os.makedirs(self.save_root)
        else:
            raise ValueError(
                " ... Warning: root save directory was not defined. Logs, RCPs, and data will not be written."
            )
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
                self.ntp_last_sync, self.ntp_offset = tmps[0].strip().split(",")
                self.ntp_offset = float(self.ntp_offset)
        elif self.ntp_last_sync is None:
            asyncio.gather(self.get_ntp_time())
        self.init_endpoint_status(fastapp)
        self.fast_urls = self.get_endpoint_urls(fastapp)
        self.status_logger = self.aloop.create_task(self.log_status_task())
        self.ntp_syncer = self.aloop.create_task(self.sync_ntp_task())

    def init_endpoint_status(self, app: FastAPI):
        "Populate status dict with FastAPI server endpoints for monitoring."
        for route in app.routes:
            if route.path.startswith(f"/{self.server_name}"):
                self.status[route.name] = []
                self.endpoints.append(route.name)
        print(
            f" ... Found {len(self.status)} endpoints for status monitoring on {self.server_name}."
        )

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

    async def contain_action(
        self,
        action: Action,
        file_type: str = "stream_csv",
        file_group: str = "stream_files",
        filename: Optional[str] = None,
        header: Optional[str] = None,
    ):
        self.actives[action.action_uuid] = Base.Active(
            self, action, file_type, file_group, filename, header
        )
        await self.actives[action.action_uuid].myinit()
        return self.actives[action.action_uuid]

    async def get_active_info(self, action_uuid: str):
        if action_uuid in self.actives.keys():
            action_dict = await self.actives[action_uuid].active.as_dict()
            return action_dict
        else:
            print(f" ... Specified action uuid {action_uuid} was not found.")
            return None

    async def get_ntp_time(self):
        "Check system clock against NIST clock for trigger operations."
        c = ntplib.NTPClient()
        response = c.request(self.ntp_server, version=3)
        self.ntp_response = response
        self.ntp_last_sync = response.orig_time
        self.ntp_offset = response.offset
        print("#############################################################")
        print(" ... ntp_offset: ", self.ntp_offset)
        print("#############################################################")

        time_inst = await aiofiles.open("ntpLastSync.txt", "w")
        await time_inst.write(f"{self.ntp_last_sync},{self.ntp_offset}")
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
                        params={
                            "server": self.server_name,
                            "status": json.dumps(current_status),
                        },
                    ) as response:
                        # response = await resp
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
                                params={
                                    "server": self.server_name,
                                    "status": status_msg,
                                },
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
                    await self.get_ntp_time()
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

        def __init__(
            self,
            base,  # outer instance
            action: Action,
            file_type: str = "stream_csv",
            file_group: str = "stream_files",
            filename: Optional[str] = None,
            header: Optional[str] = None,
        ):
            self.base = base
            self.action = action
            self.action.file_type = file_type
            self.action.file_group = file_group
            self.action.filename = filename

            if header:
                self.action.header = header
                self.column_names = [
                    x.strip()
                    for x in header.split("\n")[-1]
                    .replace("%columns=", "")
                    .replace("%column_headings=", "")
                    .replace("\t", ",")
                    .split(",")
                ]
                print(self.column_names)
            self.action.set_atime(offset=self.base.ntp_offset)
            self.file_conn = None
            # if Action is not created from Decision+Actualizer, Action is independent
            if self.action.decision_timestamp is None:
                self.action.set_dtime(offset=self.base.ntp_offset)
            decision_date = self.action.decision_timestamp.split(".")[0]
            decision_time = self.action.decision_timestamp.split(".")[-1]
            year_week = strftime("%y.%U", strptime(decision_date, "%Y%m%d"))
            if not self.base.save_root:
                print(
                    " ... Root save directory not specified, cannot save action results."
                )
                self.action.save_data = False
                self.action.save_rcp = False
                self.action.output_dir = None
            else:
                self.action.save_data = True
                self.action.save_rcp = True
                self.action.output_dir = os.path.join(
                    self.base.save_root,
                    year_week,
                    decision_date,
                    f"{decision_time}_{self.action.decision_label}",
                    f"{self.action.action_queue_time}__{self.action.action_server}__{self.action.action_name}__{self.action.action_uuid}",
                )
            self.data_logger = self.base.aloop.create_task(self.log_data_task())

        async def myinit(self):
            # print('#################################################')
            # print('myinit')
            # print('#################################################')
            if self.action.save_rcp:
                os.makedirs(self.action.output_dir, exist_ok=True)
                self.action.actionnum = (
                    f"{self.action.action_abbr}{self.action.action_enum}"
                )
                self.action.filetech_key = f"files_technique__{self.action.actionnum}"
                initial_dict = {
                    "technique_name": self.base.technique_name,
                    "server_name": self.base.server_name,
                    "orchestrator": self.action.orch_name,
                    "machine_name": self.base.hostname,
                    "access": self.action.access,
                    "samples_in": self.action.samples_in,
                    "output_dir": self.action.output_dir,
                }
                initial_dict.update(self.base.calibration)
                initial_dict.update(
                    {
                        "decision_uuid": self.action.decision_uuid,
                        "action_uuid": self.action.action_uuid,
                        "action_enum": self.action.action_enum,
                        "action_name": self.action.action_name,
                        f"{self.action.technique_name}_params__{self.action.actionnum}": self.action.action_params,
                    }
                )
                await self.write_to_rcp(initial_dict)

                if self.action.save_data:
                    sample_no = str(self.action.save_data).replace("True", "noSampleID")
                    if self.action.plate_id is None:
                        self.action.plate_id = "noPlateID"
                    if self.action.header:
                        if isinstance(self.action.header, list):
                            header_lines = len(self.action.header)
                            self.action.header = "\n".join(self.header)
                        else:
                            header_lines = len(self.action.header.split("\n"))
                        header_parts = ",".join(
                            self.action.header.split("\n")[-1]
                            .replace(",", "\t")
                            .split()
                        )
                        file_info = f"{self.action.file_type};{header_parts};{header_lines};{sample_no}"
                    else:
                        file_info = f"{self.action.file_type};{sample_no}"
                    if self.action.filename is None:  # generate filename
                        if self.action.action_enum is not None:
                            self.action.filename = f"act{self.action.action_enum:.2f}_{self.action.action_abbr}__{self.action.plate_id}_{sample_no}.csv"
                        else:
                            self.action.filename = f"actNone_{self.action.action_abbr}__{self.action.plate_id}_{sample_no}.csv"
                    self.action.file_dict[self.action.filetech_key][
                        self.action.file_group
                    ].update({self.action.filename: file_info})
                    await self.set_output_file(self.action.filename, self.action.header)
            await self.add_status()

        async def add_status(self):
            self.base.status[self.action.action_name].append(self.action.action_uuid)
            print(
                f" ... Added {self.action.action_uuid} to {self.action.action_name} status list."
            )
            await self.base.status_q.put(
                {self.action.action_name: self.base.status[self.action.action_name]}
            )

        async def clear_status(self):
            self.base.status[self.action.action_name].remove(self.action.action_uuid)
            print(
                f" ... Removed {self.action.action_uuid} from {self.action.action_name} status list."
            )
            await self.base.status_q.put(
                {self.action.action_name: self.base.status[self.action.action_name]}
            )

        async def set_estop(self):
            self.base.status[self.action.action_name].remove(self.action.action_uuid)
            self.base.status[self.action.action_name].append(
                f"{self.action.action_uuid}__estop"
            )
            print(
                f" ... E-STOP {self.action.action_uuid} on {self.action.action_name} status."
            )
            await self.base.status_q.put(
                {self.action.action_name: self.base.status[self.action.action_name]}
            )

        async def set_error(self, err_msg: Optional[str]=None):
            self.base.status[self.action.action_name].remove(self.action.action_uuid)
            self.base.status[self.action.action_name].append(
                f"{self.action.action_uuid}__error"
            )
            print(
                f" ... ERROR {self.action.action_uuid} on {self.action.action_name} status."
            )
            if err_msg:
                self.action.error_code = err_msg
            else:
                self.action.error_code = "-1 unspecified error"
            await self.base.status_q.put(
                {self.action.action_name: self.base.status[self.action.action_name]}
            )

        async def set_realtime(
            self, epoch_ns: Optional[float] = None, offset: Optional[float] = None
        ):
            if offset is None:
                if self.base.ntp_offset is not None:
                    offset_ns = int(np.floor(self.base.ntp_offset * 1e9))
                else:
                    offset_ns = 0.0
            else:
                offset_ns = int(np.floor(offset * 1e9))
            if epoch_ns is None:
                action_real_time = time_ns() + offset_ns
            else:
                action_real_time = epoch_ns + offset_ns
            return action_real_time

        async def set_output_file(self, filename: str, header: Optional[str] = None):
            "Set active save_path, write header if supplied."
            output_path = os.path.join(self.action.output_dir, filename)
            print("#########################################################")
            print(" ... writing data to:", output_path)
            print("#########################################################")
            # create output file and set connection
            self.file_conn = await aiofiles.open(output_path, mode="a+")
            if header:
                if not header.endswith("\n"):
                    header += "\n"
                await self.file_conn.write(header)

        async def write_live_data(self, output_str: str):
            "Appends lines to file_conn."
            if self.file_conn:
                print('#########################################################')
                print(' ... appending data to file connection')
                print('#########################################################')
                if not output_str.endswith("\n"):
                    output_str += "\n"
                await self.file_conn.write(output_str)

        async def enqueue_data(self, data, errors: list = []):
            data_msg = {
                self.action.action_uuid: {
                    "data": data,
                    "action_name": self.action.action_name,
                    "errors": errors,
                }
            }
            await self.base.data_q.put(data_msg)

        async def log_data_task(self):
            "Self-subscribe to data queue, write to present file path."
            print("#########################################################")
            print(" ... starting data logger")
            print("#########################################################")
            # data_msg should be a dict {uuid: list of values or a list of list of values}
            try:
                async for data_msg in self.base.data_q.subscribe():
                    print(data_msg)
                    print(self.action.action_uuid)
                    if (
                        self.action.action_uuid in data_msg.keys()
                    ):  # only write data for this action
                        # print('#################################################')
                        # print('1 ... data logger: received message')
                        # print('#################################################')
                        data_dict = data_msg[self.action.action_uuid]
                        data_val = data_dict["data"]
                        # if isinstance(data_val, list) or isinstance(data_val, tuple):
                        #     # print('#################################################')
                        #     # print('2 ... data logger: message is tuple/list')
                        #     # print('#################################################')
                        #     lines = "\n".join(
                        #         [",".join([str(x) for x in l]) for l in data_val]
                        #     )
                        # elif isinstance(data_val, dict):
                        #     # print('#################################################')
                        #     # print('3 ... data logger: message is dict')
                        #     # print('#################################################')
                        #     # print(self.column_names)
                        #     # print(data_val)
                        #     # for col in self.column_names:
                        #     #     if col!='unknown1':
                        #     #         print(col, data_val[col])
                        #     columns = [
                        #         data_val[col]
                        #         for col in self.column_names
                        #         if col != "unknown1"
                        #     ]
                        #     # print(columns)
                        #     lines = "\n".join(
                        #         [",".join([str(x) for x in l]) for l in zip(*columns)]
                        #     )
                        #     # print(lines)
                        # else:
                        #     # print('#################################################')
                        #     # print('4 ... data logger: message is not dict or tuple/list')
                        #     # print('#################################################')
                        #     lines = str(data_val)
                        self.action.data.append(data_val)
                        print(self.action.data)
                        if self.file_conn:
                            print('#################################################')
                            print('5 ... data logger: writing lines to file')
                            print('#################################################')
                            await self.write_live_data(json.dumps(data_val))
                            # await self.write_live_data(lines)
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
            _output_path = os.path.join(self.action.output_dir, filename)
            print("#########################################################")
            print(" ... writing non stream data to:", _output_path)
            print("#########################################################")
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
            self.action.file_dict[self.action.filetech_key]["aux_files"].update(
                {filename: file_info}
            )
            print(f" ... Wrote {numlines} lines to {_output_path}")

        async def write_to_rcp(self, rcp_dict: dict):
            "Create new rcp if it doesn't exist, otherwise append rcp_dict to file."
            output_path = os.path.join(
                self.action.output_dir, f"{self.action.action_queue_time}.rcp"
            )
            print("#########################################################")
            print(" ... writing rcp to:", output_path)
            print("#########################################################")
            output_str = dict_to_rcp(rcp_dict)
            file_instance = await aiofiles.open(output_path, mode="a+")
            await file_instance.write(output_str)
            await file_instance.close()

        async def append_sample(
            self,
            sample_no,
            type,
            plate_id: Optional[int] = None,
            tray_id: Optional[str] = None,
            slot: Optional[int] = None,
            vial: Optional[int] = None,
            custom_location: Optional[str] = None,
        ):
            "Add sample to samples_out dict"
            if type == "solid":
                self.action.samples_out["plate_samples"].update({sample_no: plate_id})
            elif type == "liquid":
                liquid_dict = {
                    sample_no: {
                        k: v
                        for k, v in zip(
                            ["tray_id", "slot", "vial", "custom_location"],
                            [tray_id, slot, vial, custom_location],
                        )
                        if v
                    }
                }
                self.action.samples_out["liquid_samples"].update(liquid_dict)
            else:
                print(f"Type '{type}' is not supported.")

        async def finish(self):
            "Close file_conn, finish rcp, copy aux, set endpoint status, and move active dict to past."
            await asyncio.sleep(1)
            print(" ... finishing data logging.")
            if self.file_conn:
                await self.file_conn.close()
                self.file_conn = None
            if self.action.samples_out:
                await self.write_to_rcp({"samples_out": self.action.samples_out})
            if self.action.file_dict:
                await self.write_to_rcp(self.action.file_dict)
            await self.clear_status()
            self.data_logger.cancel()
            _ = self.base.actives.pop(self.action.action_uuid, None)
            return self.action

        async def track_file(self, file_type: str, file_path: str, sample_no: str):
            "Add auxiliary files to file dictionary."
            if os.path.dirname(file_path) != self.action.output_dir:
                self.action.file_paths.append(file_path)
            file_info = f"{file_type};{sample_no}"
            filename = os.path.basename(file_path)
            self.action.file_dict[self.action.filetech_key]["aux_files"].update(
                {filename: file_info}
            )
            print(
                f" ... {filename} added to files_technique__{self.action.actionnum} / aux_files list."
            )

        async def relocate_files(self):
            "Copy auxiliary files from folder path to rcp directory."
            for x in self.action.file_paths:
                new_path = os.path.join(self.action.output_dir, os.path.basename(x))
                await async_copy(x, new_path)


class Orch(Base):
    """Base class for async orchestrator with trigger support and pushed status update.

    Websockets are not used for critical communications. Orch will attach to all action
    servers listed in a config and maintain a dict of {serverName: status}, which is
    updated by POST requests from action servers. Orch will simultaneously dispatch as
    many action_dq as possible in action queue until it encounters any of the following
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

    def __init__(self, fastapp: HelaoFastAPI):
        super().__init__(fastapp)
        self.import_actualizers()
        # instantiate decision/experiment queue, action queue
        self.decision_dq = deque([])
        self.action_dq = deque([])
        self.dispatched_actions = {}
        self.active_decision = None
        self.last_decision = None

        # compilation of action server status dicts
        self.global_state_dict = defaultdict(lambda: defaultdict(list))
        self.global_state_dict['_internal']['async_dispatcher'] = []
        self.global_q = MultisubscriberQueue()  # passes global_state_dict dicts

        # global state of all instruments as string [idle|busy] independent of dispatch loop
        self.global_state_str = None

        # uuid lists for estop and error tracking used by update_global_state_task
        self.error_uuids = []
        self.estop_uuids = []
        self.running_uuids = []

        self.init_success = False  # need to subscribe to all fastapi servers in config
        # present dispatch loop state [started|stopped]
        self.loop_state = "stopped"

        # separate from global state, signals dispatch loop control [skip|stop|None]
        self.loop_intent = None

        # pointer to dispatch_loop_task
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
                " ... Orchestrator cannot process decision_dq unless all FastAPI servers in config file are accessible."
            )

    async def update_status(self, act_serv: str, status_dict: dict):
        """Dict update method for action server to push status messages.

        Async task for updating orch status dict {act_serv_key: {act_name: [act_uuid]}}
        """
        last_dict = self.global_state_dict[act_serv]
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
        self.global_state_dict[act_serv].update(status_dict)
        await self.global_q.put(self.global_state_dict)

    async def update_global_state(self, status_dict: dict):
        _running_uuids = []
        for act_serv, act_named in status_dict.items():
            for act_name, uuids in act_named.items():
                for myuuid in uuids:
                    uuid_tup = (act_serv, act_name, myuuid)
                    if myuuid.endswith("__estop"):
                        self.estop_uuids.append(uuid_tup)
                    elif myuuid.endswith("__error"):
                        self.error_uuids.append(uuid_tup)
                    else:
                        _running_uuids.append(uuid_tup)
        self.running_uuids = _running_uuids

    async def update_global_state_task(self):
        """Self-subscribe to global_q and update status dict."""
        async for status_dict in self.global_q.subscribe():
            await self.update_global_state(status_dict)
            running_states, _ = self.check_global_state()
            if self.estop_uuids and self.loop_state == "started":
                await self.estop_loop()
            elif self.error_uuids and self.loop_state == "started":
                self.global_state_str = "error"
            elif len(running_states) == 0:
                self.global_state_str = "idle"
            else:
                self.global_state_str = "busy"
                print(" ... ", running_states)

    def check_global_state(self):
        """Return global state of action servers."""
        running_states = []
        idle_states = []
        for act_serv, act_dict in self.global_state_dict.items():
            for act_name, act_uuids in act_dict.items():
                if len(act_uuids) == 0:
                    idle_states.append(f"{act_serv}:{act_name}")
                else:
                    running_states.append(f"{act_serv}:{act_name}:{len(act_uuids)}")
        return running_states, idle_states

    async def async_dispatcher(self, A: Action):
        """Request non-blocking action_dq which may run concurrently.

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
                response = await resp.json()
                return response

    async def dispatch_loop_task(self):
        """Parse decision and action queues, and dispatch action_dq while tracking run state flags."""
        print(" ... running operator orch")
        print(" ... orch status:", self.global_state_str)
        # clause for resuming paused action list
        print(" ... orch descisions: ", self.decision_dq)
        try:
            self.loop_state = "started"
            while self.loop_state == "started" and (self.action_dq or self.decision_dq):
                await asyncio.sleep(
                    0.001
                )  # allows status changes to affect between action_dq, also enforce unique timestamp
                if not self.action_dq:
                    print(" ... getting action_dq from new decision")
                    # generate uids when populating, generate timestamp when acquring
                    self.last_decision = copy(self.active_decision)
                    self.active_decision = self.decision_dq.popleft()
                    self.active_decision.technique_name = self.technique_name
                    self.active_decision.set_dtime(offset=self.ntp_offset)
                    actual = self.active_decision.actual
                    # additional actualizer params should be stored in decision.actual_pars
                    unpacked_acts = self.action_lib[actual](self.active_decision)
                    for i, act in enumerate(unpacked_acts):
                        act.action_enum = f"{i}"
                        # act.gen_uuid()
                    # TODO:update actualizer code
                    self.action_dq = deque(unpacked_acts)
                    self.dispatched_actions = {}
                    print(" ... got ", self.action_dq)
                    print(" ... optional params ", self.active_decision.actual_pars)
                else:
                    if self.loop_intent == "stop":
                        print(" ... stopping orchestrator")
                        # monitor status of running action_dq, then end loop
                        async for _ in self.global_q.subscribe():
                            if self.global_state_str == "idle":
                                self.loop_state = "stopped"
                                await self.intend_none()
                                break
                    elif self.loop_intent == "skip":
                        # clear action queue, forcing next decision
                        self.action_dq.clear()
                        await self.intend_none()
                        print(" ... skipping to next decision")
                    else:
                        # all action blocking is handled like preempt, check Action requirements
                        A = self.action_dq.popleft()
                        # append previous results to current action
                        A.result_dict = self.active_decision.result_dict
                        # see async_dispatcher for unpacking
                        if isinstance(A.start_condition, int):
                            if A.start_condition == 0:
                                print(
                                    " ... orch is dispatching an unconditional action"
                                )
                            else:
                                if A.start_condition == 1:
                                    print(
                                        " ... orch is waiting for endpoint to become available"
                                    )
                                    async for _ in self.global_q.subscribe():
                                        endpoint_free = (
                                            len(
                                                self.global_state_dict[A.action_server][
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
                                                for _, uuid_list in self.global_state_dict[
                                                    A.action_server
                                                ].items()
                                            ]
                                        )
                                        if server_free:
                                            break
                                else:  # start_condition is 3 or unsupported value
                                    print(
                                        " ... orch is waiting for all action_dq to finish"
                                    )
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
                                        len(self.global_state_dict[k][v] == 0)
                                        for k, vlist in condition_dict.items()
                                        if vlist and isinstance(vlist, list)
                                        for v in vlist
                                    ]
                                    + [
                                        len(uuid_list) == 0
                                        for k, v in condition_dict.items()
                                        if v == [] or v is None
                                        for _, uuid_list in self.global_state_dict[
                                            k
                                        ].items()
                                    ]
                                )
                                if conditions_free:
                                    break
                        else:
                            print(
                                " ... invalid start condition, waiting for all action_dq to finish"
                            )
                            async for _ in self.global_q.subscribe():
                                running_states, _ = self.check_global_state()
                                global_free = len(running_states) == 0
                                if global_free:
                                    break
                        print(
                            f" ... dispatching action {A.action} on server {A.server}"
                        )
                        # keep running list of dispatched actions
                        self.dispatched_actions[A.action_enum] = copy(A)
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
        await self.force_stop_running_action_q()
        await self.intend_none()

    async def force_stop_running_action_q(self):
        running_uuids = []
        estop_uuids = []
        for act_serv, act_named in self.global_state_dict.items():
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

    async def clear_estate(self, clear_estop=True, clear_error=True):
        if not clear_estop and not clear_error:
            print(
                " ... both clear_estop and clear_error parameters are False, nothing to clear"
            )
        await self.update_global_state()
        cleared_status = copy(self.global_state_dict)
        if clear_estop:
            for serv, act, myuuid in self.estop_uuids:
                print(f" ... clearing E-STOP {act} on {serv}")
                cleared_status[serv][act] = cleared_status[serv][act].remove(myuuid)
        if clear_error:
            for serv, act, myuuid in self.error_uuids:
                print(f" ... clearing error {act} on {serv}")
                cleared_status[serv][act] = cleared_status[serv][act].remove(myuuid)
        await self.global_q.put(cleared_status)
        print(" ... resetting dispatch loop state")
        self.loop_state = "stopped"
        print(
            f" ... {len(self.running_uuids)} running action_dq did not fully stop after E-STOP/error was raised"
        )

    async def add_decision(
        self,
        decision_dict: dict = None,
        orch_name: str = None,
        decision_label: str = None,
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
        prepend: Optional[bool] = False,
        at_index: Optional[int] = None,
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
                    " ... decision_label not specified, no past decision_dq to inherit so using default 'nolabel"
                )
        await asyncio.sleep(0.001)
        if at_index:
            self.decision_dq.insert(at_index)
        elif prepend:
            self.decision_dq.appendleft(D)
            print(f" ... decision {D.decision_uuid} prepended to queue")
        else:
            self.decision_dq.append(D)
            print(f" ... decision {D.decision_uuid} appended to queue")

    def list_decisions(self):
        """Return the current queue of decision_dq."""
        declist = [
            return_dec(
                index=i,
                uid=dec.decision_uuid,
                label=dec.decision_label,
                actualizer=dec.actual,
                pars=dec.actual_pars,
                access=dec.access,
            )
            for i, dec in enumerate(self.decision_dq)
        ]
        retval = return_declist(decision_dq=declist)
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
        retval = return_declist(decision_dq=declist)
        return retval

    def list_actions(self):
        """Return the current queue of action_dq."""
        actlist = [
            return_act(
                index=i,
                uid=act.action_uuid,
                server=act.action_server,
                action=act.action_name,
                pars=act.action_params,
                preempt=act.start_condition,
            )
            for i, act in enumerate(self.action_dq)
        ]
        retval = return_actlist(action_dq=actlist)
        return retval

    def supplement_error_action(self, check_uuid: str, sup_action: Action):
        """Insert action at front of action queue with subversion of errored action, inherit parameters if desired."""
        if self.error_uuids == []:
            print("There are no error statuses to replace")
        else:
            matching_error = [tup for tup in self.error_uuids if tup[2] == check_uuid]
            if matching_error:
                _, _, error_uuid = matching_error[0]
                EA = [
                    A
                    for _, A in self.dispatched_actions.items()
                    if A.action_uuid == error_uuid
                ][0]
                # up to 99 supplements
                new_enum = round(EA.action_enum + 0.01, 2)
                new_action = sup_action
                new_action.action_enum = new_enum
                self.action_dq.appendleft(new_action)
            else:
                print(f"uuid {check_uuid} not found in list of error statuses:")
                print(", ".join(self.error_uuids))

    def remove_decision(
        self, by_index: Optional[int] = None, by_uuid: Optional[str] = None
    ):
        """Remove decision in list by enumeration index or uuid."""
        if by_index:
            i = by_index
        elif by_uuid:
            i = [
                i
                for i, D in enumerate(list(self.decision_dq))
                if D.decision_uuid == by_uuid
            ][0]
        else:
            print("No arguments given for locating existing decision to remove.")
            return None
        del self.decision_dq[i]

    def replace_action(
        self,
        sup_action: Action,
        by_index: Optional[int] = None,
        by_uuid: Optional[str] = None,
        by_enum: Optional[Union[int, float]] = None,
    ):
        """Substitute a queued action."""
        if by_index:
            i = by_index
        elif by_uuid:
            i = [
                i
                for i, A in enumerate(list(self.action_dq))
                if A.action_uuid == by_uuid
            ][0]
        elif by_enum:
            i = [
                i
                for i, A in enumerate(list(self.action_dq))
                if A.action_enum == by_enum
            ][0]
        else:
            print("No arguments given for locating existing action to replace.")
            return None
        current_enum = self.action_dq[i].action_enum
        new_action = sup_action
        new_action.action_enum = current_enum
        self.action_dq.insert(i, new_action)
        del self.action_dq[i + 1]

    def append_action(self, sup_action: Action):
        """Add action to end of current action queue."""
        if len(self.action_dq) == 0:
            last_enum = floor(max(list(self.dispatched_actions.keys())))
        else:
            last_enum = floor(self.action_dq[-1].action_enum)
        new_enum = int(last_enum + 1)
        new_action = sup_action
        new_action.action_enum = new_enum
        self.action_dq.append(new_action)

    async def shutdown(self):
        await self.detach_subscribers()
        self.status_logger.cancel()
        self.ntp_syncer.cancel()
        self.status_subscriber.cancel()
