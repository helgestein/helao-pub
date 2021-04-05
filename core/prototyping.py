import ntplib
import os
from classes import MultisubscriberQueue
from time import ctime, time, strftime
import asyncio
import aiohttp
import aiofiles
from copy import copy

class ID:
    "ID class for process-sample identification."
    def __init__(self):
        self.data = []
        self.decisionID = None
        self.plateID = None
        self.sampleID = None
        self.filePath = None
        self.auxFiles = []

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
    also created as initial subscribers to prevent queue overflow.
    
    The data writing method will update a class attribute with the currently open file.
    For a given root directory, files and folders will be written as follows:
      {root_dir}/
      {year_weeknum}/
        {decision_id}__{descString}/
            {YYmmdd.HHMMSS}__{plateid}_{sampleno}__datafile.ext
            {YYmmdd.HHMMSS}.rcp
    
    """
    def __init__(self, serverName):
        self.serverName = serverName
        self.status = None
        self.active = ID()
        self.last = ID()
        self.fileConn = None # aiofiles connection
        self.fileSaveRoot = '.'
        self.statusQ = MultisubscriberQueue()
        self.dataQ = MultisubscriberQueue()
        self.statusClients = set()
        self.dataClients= set()
        self.ntpServer = 'time.nist.gov'
        self.ntpResponse = None
        self.ntpLastSync = None
        self.ntpOffset = None # add to system time for correction
        self.getNtpTime()
    
    def getNtpTime(self):
        "Check system clock against NIST clock for trigger operations."
        c = ntplib.NTPClient()
        response = c.request(self.ntpServer, version=3)
        self.ntpResponse = response
        self.ntpLastSync = response.orig_time
        self.ntpOffset = response.offset
        print(f"retrieved time at {ctime(self.ntpResponse.tx_timestamp)} from {self.ntpServer}")
        
    def attachStatusClient(self, clientAddr):
        "Add client for pushing status updates via HTTP POST."
        self.statusClients.add(clientAddr)
   
    def detachStatusClient(self, clientAddr):
        "Remove client from receiving status updates via HTTP POST"
        self.statusClients.remove(clientAddr)
        
    async def selfStatusTask(self, retryLimit=5):
        "Self-subscribe to status queue, log status changes, POST to clients."
        async for statusMsg in self.statusQ.subscribe():
            self.status = statusMsg
            for clientAddr in self.statusClients:
                async with aiohttp.ClientSession() as session:
                    success = False
                    for _ in range(retryLimit):
                        async with session.post(
                            f"http://{clientAddr}/update_status", params = {"server": self.serverName, "status": statusMsg}
                        ) as resp:
                            response = await resp
                        if response.status<400:
                            success = True
                            break
                if success:
                    print(f"Updated {self.serverName} status to {statusMsg} on {clientAddr}.")
                else:
                    print(f"Failed to push status message to {clientAddr} after {retryLimit} attempts.") 
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
                await self.writeData(lines)
    
    async def syncNtpTask(self, resyncTime=600):
        "Regularly sync with NTP server."
        while True:
            if time() - self.ntpLastSync > resyncTime:
                self.getNtpTime()
            else:
                await asyncio.sleep(0.5)
    
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
    
    async def writeData(self, outputStr):
        "Appends lines to fileConn."
        if not outputStr.endswith("\n"):
            outputStr += "\n"
        await self.fileConn.write(outputStr)
    
    
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
    