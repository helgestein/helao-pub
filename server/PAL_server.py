
import os
import sys

from importlib import import_module
import json
import uvicorn

from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager
from classes import LocalDataHandler


import asyncio
import time
from time import strftime

import paramiko
import base64
from enum import Enum
from enum import auto
# from fastapi_utils.enums import StrEnum
import aiohttp

import nidaqmx
from nidaqmx.constants import LineGrouping
from nidaqmx.constants import Edge
from nidaqmx.constants import AcquisitionType 
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import VoltageUnits
from nidaqmx.constants import CurrentShuntResistorLocation
from nidaqmx.constants import UnitsPreScaled
from nidaqmx.constants import CountDirection
from nidaqmx.constants import TaskMode
from nidaqmx.constants import SyncType
from nidaqmx.constants import TriggerType


from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager
from classes import sample_class
from classes import getuid
from classes import action_runparams
from classes import Action_params


##############################################################################
# PAL classes
##############################################################################


class Spacingmethod(str, Enum):
    linear = 'linear' # 1, 2, 3, 4, 5, ...
    geometric = 'gemoetric' # 1, 2, 4, 8, 16
    power = 'power'
    exponential = 'exponential'


class cPALparams():
    def __init__(self,
                 liquid_sample_no: int = None, 
                 method: str = '',
                 tool: str = '',
                 source: str = '',
                 volume_uL: int = 0, # uL
                 dest_tray: int = 2,
                 dest_slot: int = 1,
                 dest_vial: int = 1,
                 #logfile: str = 'TestLogFile.txt',
                 totalvials: int = 1,
                 sampleperiod: float = 0.0,
                 spacingmethod: Spacingmethod = 'linear',
                 spacingfactor: float = 1.0,
                 ):

        self.liquid_sample_no = liquid_sample_no
        self.method = method
        self.tool = tool
        self.source = source
        self.volume_uL = volume_uL
        self.dest_tray = dest_tray
        self.dest_slot = dest_slot
        self.dest_vial = dest_vial
        # logfile: str = 'TestLogFile.txt',
        self.totalvials = totalvials
        self.sampleperiod = sampleperiod
        self.spacingmethod = spacingmethod
        self.spacingfactor = spacingfactor       
        
    def as_dict(self):
        return vars(self)




class cPAL:
    
    def __init__(self, config_dict, stat, C, servkey):
        self.config_dict = config_dict
        self.stat = stat
        self.servkey = servkey
        
        
        
        self.dataserv = self.config_dict.data_server
        self.datahost = C[self.config_dict.data_server].host
        self.dataport = C[self.config_dict.data_server].port

        self.local_data_dump = self.config_dict['local_data_dump']

        
        
        self.sshuser = self.config_dict["user"]
        self.sshkey = self.config_dict["key"]
        self.sshhost = self.config_dict["host"]
        self.method_path = self.config_dict["method_path"]
        self.log_file = self.config_dict["log_file"]
        self.timeout = self.config_dict.get("timeout", 30*60)
        
        self.triggers = False
        self.triggerport_start = None
        self.triggerport_continue = None
        self.triggerport_done = None
        self.trigger_start = False
        self.trigger_continue = False
        self.trigger_done = False

        self.trigger_start_epoch = False
        self.trigger_continue_epoch = False
        self.trigger_done_epoch = False
        
        
        
        
        
        # will hold NImax task objects
        self.task_start = None
        self.task_continue = None
        self.task_done = None

        self.buffersize = 2 # finite samples or size of buffer depending on mode
        self.samplingrate = 10 # samples per second

        if 'dev_NImax' in self.config_dict:
            self.triggerport_start = self.config_dict['dev_NImax'].get('start', None)
            self.triggerport_continue = self.config_dict['dev_NImax'].get('continue', None)
            self.triggerport_done = self.config_dict['dev_NImax'].get('done', None)
            print('##########################################################')
            print(' ...  start trigger port',self.triggerport_start)
            print(' ...  continue trigger port',self.triggerport_continue)
            print(' ...  done trigger port',self.triggerport_done)
            print('##########################################################')
            self.triggers = True

        # self.triggers = False

        # for global IOloop
        self.IO_do_meas = False
        self.IO_estop = False
        # holds the parameters for the PAL
        self.IO_PALparams = cPALparams()
        # check for that to return FASTapi post
        self.IO_continue = False
        self.IO_error = None
        self.IO_datafile = LocalDataHandler()
        self.liquid_sample_rcp = LocalDataHandler()
        self.IO_remotedatafile = ''




        self.runparams = action_runparams

        myloop = asyncio.get_event_loop()
        #add meas IOloop
        myloop.create_task(self.IOloop())


        # for saving data localy
        self.FIFO_epoch = None
        #self.FIFO_header = ''
        self.FIFO_gamryheader = '' # measuement specific, will be reset each measurement
        self.FIFO_name = ''
        self.FIFO_dir = ''
        self.FIFO_unixdir = ''
        self.FIFO_column_headings = []
        self.FIFO_Gamryname = ''
        # holds all sample information
        #self.FIFO_sample = sample_class()

        self.def_action_params = Action_params()
        self.action_params = self.def_action_params.as_dict()



    async def create_new_liquid_sample_no(self, DUID: str = '',
                          AUID: str = '',
                          source: str = '',
                          sourcevol_mL: str = '',
                          volume_mL: float = 0.0,
                          action_time: str = strftime("%Y%m%d.%H%M%S"),
                          chemical: str = '',
                          mass: str = '',
                          supplier: str = '',
                          lot_number: str = '',
                          servkey: str = '',
                          action_params = ''
                          ):
        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/create_new_liquid_sample_no"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={
                                        'DUID': DUID,
                                        'AUID': AUID,
                                        'source': source,
                                        'sourcevol_mL': sourcevol_mL,
                                        'volume_mL': volume_mL,
                                        'action_time': action_time,
                                        'chemical': chemical,
                                        'mass': mass,
                                        'supplier': supplier,
                                        'lot_number': lot_number,
                                        'servkey':servkey}) as resp:
                response = await resp.json()
                return response['data']['id']



    async def get_sample_no_json(self, liquid_sample_no: int):
        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_liquid_sample_no_json"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'liquid_sample_no':liquid_sample_no}) as resp:
                response = await resp.json()
                return response['data']['liquid_sample']



    async def poll_start(self):
        starttime = time.time()        
        self.trigger_start = False
        with nidaqmx.Task() as task:
            task.di_channels.add_di_chan(
                self.triggerport_start, line_grouping=LineGrouping.CHAN_PER_LINE)
            while self.trigger_start == False:
                data = task.read(number_of_samples_per_channel=1)
                print('...................... start port status:', data)
                if any(data) == True:
                    print(' ... got PAL start trigger poll')
                    self.trigger_start_epoch = time.time_ns()
                    self.trigger_start = True
                    return True
                if (time.time()-starttime)>self.timeout:
                    return False
                await asyncio.sleep(1)
        return True


    async def poll_continue(self):
        starttime = time.time()
        self.trigger_continue = False
        with nidaqmx.Task() as task:
            task.di_channels.add_di_chan(
                self.triggerport_continue, line_grouping=LineGrouping.CHAN_PER_LINE)
            while self.trigger_continue == False:
                data = task.read(number_of_samples_per_channel=1)
                print('...................... continue port status:', data)
                if any(data) == True:
                    print(' ... got PAL continue trigger poll')
                    self.trigger_continue_epoch = time.time_ns()
                    self.trigger_continue = True
                    return True
                if (time.time()-starttime)>self.timeout:
                    return False
                await asyncio.sleep(1)
        return True


    async def poll_done(self):
        starttime = time.time()
        self.trigger_done = False
        with nidaqmx.Task() as task:
            task.di_channels.add_di_chan(
                self.triggerport_done, line_grouping=LineGrouping.CHAN_PER_LINE)
            while self.trigger_done == False:
                data = task.read(number_of_samples_per_channel=1)
                print('...................... done port status:', data)
                if any(data) == True:
                    print(' ... got PAL done trigger poll')
                    self.trigger_done_epoch = time.time_ns()
                    self.trigger_done = True
                    return True
                if (time.time()-starttime)>self.timeout:
                    return False
                await asyncio.sleep(1)
        return True


    async def initcommand(self, PALparams: cPALparams, runparams):
        if not self.IO_do_meas:
            try:
                # use parsed version
                self.action_params = json.loads(runparams.action_params)
            except Exception:
                # use default
                self.action_params = self.def_action_params.as_dict()
                self.action_params['actiontime'] = strftime("%Y%m%d.%H%M%S")
    
            self.runparams = runparams
            self.IO_PALparams = PALparams

            self.IO_remotedatafile = ''
            self.FIFO_name = f'PAL__{strftime("%Y%m%d_%H%M%S%z.txt")}' # need to be txt at end
            self.FIFO_dir = os.path.join(self.local_data_dump,self.action_params['save_folder'])

            print('##########################################################')
            print(' ... PAL saving to:',self.FIFO_dir)
            self.FIFO_unixdir = self.FIFO_dir
#            self.FIFO_unixdir = self.FIFO_unixdir.replace('C:\\','/cygdrive/c/')
            self.FIFO_unixdir = self.FIFO_unixdir.replace('C:\\','')
            self.FIFO_unixdir = self.FIFO_unixdir.replace('\\','/')
            print(' ... RSHS saving to: ','/cygdrive/c/',self.FIFO_unixdir)
            print('##########################################################')
            datafile = os.path.join(self.FIFO_dir,self.FIFO_name)
            remotedatafile = os.path.join(self.FIFO_dir, 'AUX__'+self.FIFO_name)#self.IO_remotedatafile
            self.IO_continue = False
            self.IO_do_meas = True
            # need to wait not until we get the last continue trigger (for multiple samples)
            # or the continue trigger if only one sample
            # idle will be set in IOloop once the done trigger is detected
            error = None
            while not self.IO_continue:
                await asyncio.sleep(1)
            error = self.IO_error

        else:
            error = "meas already in progress"
            datafile = ''
            remotedatafile = ''
            await self.stat.set_idle(runparams.statuid, runparams.statname)




        return {
            "err_code": error,
            # "eta": eta,
            "datafile": datafile,
            "remotedatafile": remotedatafile
        }            




    async def sendcommand(self, PALparams: cPALparams):
        
        # these will be constant and dont change for multi PAL sampling
        # only PALparams will be modified accordingly
        print(' ... PAL got actionparams:',self.action_params)
        DUID = self.action_params['DUID']
        AUID = self.action_params['DUID']
        actiontime = self.action_params['actiontime']


        sourceelecrolyte = await self.get_sample_no_json(PALparams.liquid_sample_no)
        
        source_chemical = sourceelecrolyte.get('chemical', [''])
        source_mass = sourceelecrolyte.get('mass', [''])
        source_supplier = sourceelecrolyte.get('supplier', [''])
        source_lotnumber = sourceelecrolyte.get('lot_number', [''])
        print(' ... sourceelectrolyte:', sourceelecrolyte)
        print(' ... source_chemical:', source_chemical)
        print(' ... source_mass:', source_mass)
        print(' ... source_supplier:', source_supplier)
        print(' ... source_lotnumber:', source_lotnumber)
        
        new_liquid_sample_no = await self.create_new_liquid_sample_no(DUID, AUID, source=PALparams.liquid_sample_no, sourcevol_mL = PALparams.volume_uL/1000.0,
                                             volume_mL = PALparams.volume_uL/1000.0, action_time=actiontime, chemical=source_chemical,
                                             mass=source_mass, supplier=source_supplier, lot_number=source_lotnumber,
                                             servkey=self.servkey)

        path_methodfile = os.path.join( self.method_path,  PALparams.method)


        start_time = None
        continue_time = None
        done_time = None
        ssh_time = None
        
        
        
        
        
        

        k = paramiko.RSAKey.from_private_key_file(self.sshkey)
        mysshclient = paramiko.SSHClient()
        mysshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        mysshclient.connect(hostname=self.sshhost, username=self.sshuser, pkey=k)

        # creating folder first on rshs
        print('##############################################################')
        unixpath = '/cygdrive/c'
        print()
        for path in self.FIFO_unixdir.split('/'):
            
            unixpath += '/'+path
            print(' ... adding',path, ' ... ',unixpath)
            if path != '':
                sshcmd = f'mkdir {unixpath}'
                print(' ... cmd', sshcmd)
                mysshclient_stdin, mysshclient_stdout, mysshclient_stderr = mysshclient.exec_command(sshcmd)
                # print('################',mysshclient_stdin)
                # print('################',mysshclient_stdout)
                # print('################',mysshclient_stderr)
        if not unixpath.endswith("/"):
            unixpath += '/'
        print(' ... final', unixpath)

        unixlogfile = 'AUX__'+self.FIFO_name
        unixlogfilefull = unixpath+unixlogfile
        sshcmd = f'touch {unixlogfilefull}'        
        mysshclient_stdin, mysshclient_stdout, mysshclient_stderr = mysshclient.exec_command(sshcmd)


        auxheader = 'Date\tMethod\tTool\tSource\tDestinationTray\tDestinationSlot\tDestinationVial\tVolume\r\n' # for \r\n
        # sshcmd = f'cd {unixpath}'
        # print(' .... ', sshcmd)
        # mysshclient_stdin, mysshclient_stdout, mysshclient_stderr = mysshclient.exec_command(sshcmd)
        # sshcmd = f'echo "{auxheader}" > {unixlogfile}'
        sshcmd = f'echo -e "{auxheader}" > {unixlogfilefull}'
        print(' .... ', sshcmd)
        mysshclient_stdin, mysshclient_stdout, mysshclient_stderr = mysshclient.exec_command(sshcmd)

        print(' ... final', unixlogfilefull)
        print('##############################################################')        
                        


        # path_logfile = self.log_file
        path_logfile = os.path.join(self.FIFO_dir, 'AUX__'+self.FIFO_name) # need to be txt at end
        self.IO_remotedatafile = path_logfile
        cmd_to_execute = f'tmux new-window PAL  /loadmethod "{path_methodfile}" "{PALparams.tool};{PALparams.source};{PALparams.volume_uL};{PALparams.dest_tray};{PALparams.dest_slot};{PALparams.dest_vial};{path_logfile}" /start /quit'
        print(' ... PAL command:')
        print(cmd_to_execute)


        ssh_time = time.time_ns()
        mysshclient_stdin, mysshclient_stdout, mysshclient_stderr = mysshclient.exec_command(cmd_to_execute)
        mysshclient.close()


        
        # only wait if triggers are configured
        error = None
        if self.triggers:
            print(' ... waiting for PAL start trigger')
            # val = await self.wait_for_trigger_start()
            val = await self.poll_start()
            if not val:
                print(' ... PAL start trigger timeout')
                error = 'start_timeout'
                self.IO_error = error
                self.IO_continue = True
            else:
                print(' ... got PAL start trigger')
                print(' ... waiting for PAL continue trigger')
                start_time = self.trigger_start_epoch
                # val = await self.wait_for_trigger_continue()
                val = await self.poll_continue()
                if not val:
                    print(' ... PAL continue trigger timeout')
                    error = 'continue_timeout'
                    self.IO_error = error
                    self.IO_continue = True
                else:
                    self.IO_continue = True # signal to return FASTAPI, but not yet status
                    print(' ... got PAL continue trigger')
                    print(' ... waiting for PAL done trigger')
                    continue_time = self.trigger_continue_epoch
                    # val = await self.wait_for_trigger_done()
                    val = await self.poll_done()
                    if not val:
                        print(' ... PAL done trigger timeout')
                        error = 'done_timeout'
                        # self.IO_error = error
                        # self.IO_continue = True
                    else:
                        # self.IO_continue = True
                        # self.IO_continue = True
                        print(' ... got PAL done trigger')
                        done_time = self.trigger_done_epoch
        
        
        logdata = [str(new_liquid_sample_no), str(PALparams.liquid_sample_no), str(ssh_time), str(start_time), str(continue_time), str(done_time), PALparams.tool, PALparams.source, str(PALparams.volume_uL), str(PALparams.dest_tray), str(PALparams.dest_slot) , str(PALparams.dest_vial), path_logfile, path_methodfile]
        await self.IO_datafile.open_file_async()
        await self.IO_datafile.write_data_async('\t'.join(logdata))
        await self.IO_datafile.close_file_async()


        # liquid_sample specific rcp
        liquid_sampe_dict = dict(d_uid = self.action_params['DUID'],
                                 a_uid = self.action_params['AUID'],
                                 action = self.action_params['action'],
                                 # action_pars = self.action_params['action_pars'],
                                 server_key = self.servkey,
                                 plate_id = self.action_params['plate_id'],
                                 sample_no = self.action_params['sample_no'],
                                 created_at = self.action_params['DUID'],
                                 action_time = self.action_params['actiontime'],
                                 save_path = self.FIFO_dir,
                                 action_created_at = self.action_params['created_at'],
                                 block = self.action_params['block'],
                                 preempt = self.action_params['preempt'],
                                 new_liquid_sample_no = new_liquid_sample_no,
                                 old_liquid_sample_no = PALparams.liquid_sample_no,
                                 epoch_PAL = ssh_time,
                                 epoch_start = start_time,
                                 epoch_continue = continue_time,
                                 epoch_done = done_time,
                                 PAL_tool =  PALparams.tool,
                                 PAL_source = PALparams.source,
                                 PAL_volume_uL = PALparams.volume_uL,
                                 PAL_dest_tray = PALparams.dest_tray,
                                 PAL_dest_slot = PALparams.dest_slot,
                                 PAL_dest_vial = PALparams.dest_vial,
                                 PAL_logfile = path_logfile,
                                 PAL_method = path_methodfile,
                                 )
        self.liquid_sample_rcp.filename = f'{new_liquid_sample_no:08d}__{actiontime}__{AUID}.preinfo'
        self.liquid_sample_rcp.filepath = self.FIFO_dir
        await self.liquid_sample_rcp.open_file_async()
        await self.liquid_sample_rcp.write_data_async(json.dumps(liquid_sampe_dict))
        await self.liquid_sample_rcp.close_file_async()

        
        
        
        # wait another 30sec for program to close
        await asyncio.sleep(20)
            
        # these will be arrays for multiple samples
        return {
            "cmd": cmd_to_execute,
            "PALtime": ssh_time,
            "start": start_time,
            "conintue": continue_time,
            "done": done_time,
            "liquid_sample_no": new_liquid_sample_no,
            "error": error
        }



    async def IOloop(self):
        while True:
            await asyncio.sleep(1)
            if self.IO_do_meas:
                # are we in estop?
                if not self.IO_estop:
                    self.IO_datafile.filename = self.FIFO_name
                    self.IO_datafile.filepath = self.FIFO_dir

                    # write file header here
                    header = ['new_liquid_sample_no', 'old_liquid_sample_no', 'epoch_PAL', 'epoch_start', 'epoch_continue', 'epoch_done', 'PAL_tool', 'PAL_source', 'PAL_volume_uL', 'PAL_dest_tray', 'PAL_dest_slot', 'PAL_dest_vial', 'PAL_logfile', 'PAL_method']
                    await self.IO_datafile.open_file_async()
                    await self.IO_datafile.write_data_async('\t'.join(header))
                    await self.IO_datafile.close_file_async()
                    

                    # here we need to implement the multi PAL sampling 
                    # by having a loop here and sending a local modified
                    # PALparams to sendcommand
                    retvals = await self.sendcommand(self.IO_PALparams)

                    self.IO_do_meas = False

                    # need to check here again in case estop was triggered during
                    # measurement
                    # need to set the current meas to idle first 
                    await self.stat.set_idle(self.runparams.statuid, self.runparams.statname)

                    if self.IO_estop:
                        print(' ... PAL is in estop.')
                        await self.stat.set_estop()
                    else:
                        print(' ... setting PAL to idle')
#                        await self.stat.set_idle()
                    print(' ... PAL is done')
                else:
                    self.IO_do_meas = False
                    print(' ... PAL is in estop.')
                    await self.stat.set_estop()



##############################################################################
# PAL class end
##############################################################################


confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]



app = FastAPI(title="PAL Autosampler Server",
    description="",
    version="1.0")


@app.on_event("startup")
def startup_event():
    # global dataserv
    # dataserv = HTEdata(S.params)
    global stat
    stat = StatusHandler()

    global PAL
    PAL = cPAL(S.params, stat, C, servKey)

    # global wsdata
    # wsdata = wsConnectionManager()
    global wsstatus
    wsstatus = wsConnectionManager()



@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'data_status')


@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return stat.dict


# relay_actuation_test2.cam
# lcfc_archive.cam
# lcfc_fill.cam
# lcfc_fill_hardcodedvolume.cam


@app.post(f"/{servKey}/run_method")
async def run_method(liquid_sample_no: int, 
               method: str = 'lcfc_fill_hardcodedvolume.cam',
               tool: str = 'LS3',
               source: str = 'electrolyte_res',
               volume_uL: int = 500, # uL
               dest_tray: int = 2,
               dest_slot: int = 1,
               dest_vial: int = 1,
               #logfile: str = 'TestLogFile.txt',
               totalvials: int = 1,
               sampleperiod: float = 0.0,
               spacingmethod: Spacingmethod = 'linear',
               spacingfactor: float = 1.0,
               action_params = '', #optional parameters
               ):



        
        
        
    runparams = action_runparams(uid=getuid(servKey), name="run_method",  action_params = action_params)
    await stat.set_run(runparams.statuid, runparams.statname)
    retc = return_class(
        measurement_type="PAL_command",
        parameters={
            "command": "sendcommand",
            "parameters": {
                'liquid_sample_no': liquid_sample_no,
                'method': method,
                'tool':  tool,
                'source': source,
                'volume_uL': volume_uL,
                'dest_tray': dest_tray,
                'dest_slot': dest_slot,
                'dest_vial': dest_vial,
                #'logfile': logfile,
                'totalvials': totalvials,
                'sampleperiod': sampleperiod,
                'spacingmethod': spacingmethod,
                'spacingfactor': spacingfactor,
                },
        },
        data=await PAL.initcommand(cPALparams(liquid_sample_no = liquid_sample_no,
                                              method = method,
                                              tool = tool,
                                              source = source,
                                              volume_uL = volume_uL,
                                              dest_tray = dest_tray,
                                              dest_slot = dest_slot,
                                              dest_vial = dest_vial,
                                              #logfile,
                                              totalvials = totalvials,
                                              sampleperiod = sampleperiod,
                                              spacingmethod = spacingmethod,
                                              spacingfactor = spacingfactor),
                                   runparams)
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc
    


@app.post('/endpoints')
def get_all_urls():
    url_list = []
    for route in app.routes:
        routeD = {'path': route.path,
                  'name': route.name
                  }
        if 'dependant' in dir(route):
            flatParams = get_flat_params(route.dependant)
            paramD = {par.name: {
                'outer_type': str(par.outer_type_).split("'")[1],
                'type': str(par.type_).split("'")[1],
                'required': par.required,
                'shape': par.shape,
                'default': par.default
            } for par in flatParams}
            routeD['params'] = paramD
        else:
            routeD['params'] = []
        url_list.append(routeD)
    return url_list


@app.post("/shutdown")
def post_shutdown():
    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    return ""

    
if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
