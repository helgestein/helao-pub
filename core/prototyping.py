import ntplib
import os
from classes import MultisubscriberQueue
from time import ctime, time, strftime
import asyncio
import aiohttp
import aiofiles
from copy import copy

import time
from random import getrandbits
import shortuuid

class Decision:
    "ID class for sample-process identification."
    def __init__(self):
        self.data = []
        self.decision_id = None
        self.plate_id = None
        self.sample_id = None
        self.save_path = None
        self.aux_files = []

class Base:
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
    def __init__(self, server_name):
        self.server_name = server_name
        self.status = None
        self.active = None
        self.last = None
        self.file_conn = None # aiofiles connection
        self.save_root = '.'
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
   
    def detach_client(self, client_addr):
        "Remove client from receiving status updates via HTTP POST"
        self.status_clients.remove(client_addr)
        
    async def log_status_task(self, retryLimit=5):
        "Self-subscribe to status queue, log status changes, POST to clients."
        async for status_msg in self.status_q.subscribe():
            self.status = status_msg
            for client_addr in self.status_clients:
                async with aiohttp.ClientSession() as session:
                    success = False
                    for _ in range(retryLimit):
                        async with session.post(
                            f"http://{client_addr}/update_status", params = {"server": self.server_name, "status": statusMsg}
                        ) as resp:
                            response = await resp
                        if response.status<400:
                            success = True
                            break
                if success:
                    print(f"Updated {self.server_name} status to {status_msg} on {clientAddr}.")
                else:
                    print(f"Failed to push status message to {client_addr} after {retryLimit} attempts.") 
            # do stuff with statusMsg (websocket handled in FastAPI definition)
                            
    async def detachSubscribers(self):
        await self.statusQ.put(StopAsyncIteration)
        await self.dataQ.put(StopAsyncIteration)
        await asyncio.sleep(5)
    
    async def selfDataTask(self):
        "Self-subscribe to data queue, write to present filePath."
        async for dataMsg in self.dataQ.subscribe():
            # dataMsg should be a list of values or a list of list of values
            if isinstance(dataMsg[0], list):
                lines = "\n".join([",".join([str(x) for x in l]) for l in dataMsg])
            else:
                lines = ",".join([str(x) for x in dataMsg])
            if self.fileConn:
                await self.writeLiveData(lines)
    
    async def syncNtpTask(self, resyncTime=600):
        "Regularly sync with NTP server."
        while True:
            if time() - self.ntpLastSync > resyncTime:
                self.getNtpTime()
            else:
                await asyncio.sleep(0.5)
                
    async def writeFile(self, outputStr, filename=None, header=None):
        pass
    
    async def setOutputFile(self, filename=None, header=None):
        "Set active filePath, write header if filename is not None."
        if filename:
            self.active['filePath'] = os.path.join(self.fileSaveRoot,
                                                    strftime('%y_%U'),
                                                    self.active['decisionID'],
                                                    strftime('%H%M%S'),
                                                    filename
                                                    )
            os.makedirs(os.path.dirname(self.active['filePath']), exist_ok=True)
            # create output file and set connection
            self.fileConn = await aiofiles.open(self.active['filePath'], mode="a+")
            if header:
                if not header.endswith("\n"):
                    header += "\n"
                await self.fileConn.write(header)
                
    async def finishAct(self):
        "Close fileConn, set idle status, and move active dict to past."
        await self.fileConn.close()
        self.fileConn = None
        self.last = copy(self.active)
        self.active = ID()
        await self.statusQ.put('idle')
    
    async def writeLiveData(self, output_str):
        "Appends lines to fileConn."
        if self.file_conn:
            if not output_str.endswith("\n"):
                output_str += "\n"
            await self.file_conn.write(output_str)
    
    async def setupAct(self):#TODO
        "Populate active ID."
        pass
    
    async def writeRcp(self):#TODO
        "Gather auxiliary filenames, save ID and action parameters to rcp."
    

class Orch:#TODO
    """Base class for async orchestrator with trigger support and pushed status update.
    
    Websockets are no longer used for critical communications. Orch will attach to all
    action servers listed in a config and maintain a dict of {serverName: status}, which
    is updated by POST requests from action servers. Orch will simultaneously dispatch
    as many actions as possible in action queue until it encounters any of the following
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
    