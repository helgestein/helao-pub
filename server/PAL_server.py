
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
import aiofiles

import paramiko
import base64
from enum import Enum
from enum import auto
# from fastapi_utils.enums import StrEnum
import aiohttp
from datetime import datetime

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


class VT54():
    def __init__(self, max_vol_mL: float = 2.0):
        self.type = 'VT54'
        self.max_vol_mL = max_vol_mL
        self.vials = [False for i in range(54)]
        self.vol_mL = [0.0 for i in range(54)]
        self.liquid_sample_no = [None for i in range(54)]
         
    
    def first_empty(self):
        res = next((i for i, j in enumerate(self.vials) if not j), None)
        # printing result
        print ("The values till first True value : " + str(res))
        return res
    
    
    def update_vials(self, vial_dict):
        for i, vial in enumerate(vial_dict):
            try:
                self.vials[i] = bool(vial)
            except Exception:
                self.vials[i] = False
    
    
    def update_vol(self, vol_dict):
        for i, vol in enumerate(vol_dict):
            try:
                self.vol_mL[i] = float(vol)
            except Exception:
                self.vol_mL[i] = 0.0

    
    def update_liquid_sample_no(self, sample_dict):
        for i, sample in enumerate(sample_dict):
            try:
                self.liquid_sample_no[i] = int(sample)                
            except Exception:
                self.liquid_sample_no[i] = None
        


    def as_dict(self):
        return vars(self)
    

class PALtray():
    def __init__(self, slot1 = None, slot2 = None, slot3 = None):
        self.slots = [slot1, slot2, slot3]

    def as_dict(self):
        return vars(self)

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
        

        # configure the tray
        
        self.trays = [PALtray(slot1 = None, slot2 = None, slot3 = None), 
                      PALtray(slot1 = VT54(max_vol_mL=2.0), slot2 = VT54(max_vol_mL=2.0), slot3 = None)]

        self.PAL_file = 'PAL_holder_DB.json'
        # load backup of vial table, if file does not exist it will use the default one from above
        asyncio.gather(self.load_PAL_system_vial_table_from_backup())
        
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


    async def load_PAL_system_vial_table_from_backup(self):
        file_path = os.path.join(self.local_data_dump,self.PAL_file)
        print(' ... loading PAL table from',file_path)
        if not os.path.exists(file_path):
            return False
        
        
        self.fjsonread = await aiofiles.open(file_path,'r')
        trays_dict = dict()
        await self.fjsonread.seek(0)
        async for line in self.fjsonread:
                newline = json.loads(line)
                tray_no = newline.get('tray_no', None)
                slot_no = newline.get('slot_no', None)
                content = newline.get('content', None)
                if tray_no is not None:
                    if slot_no is not None:
                        if tray_no not in trays_dict:
                            trays_dict[tray_no] = dict()
                        trays_dict[tray_no][slot_no] = content
                    else:
                        trays_dict[tray_no] = None
        await self.fjsonread.close()
        
        
        # load back into self.trays
        # this does not care about the sequence
        # (double entries will be overwritten by the last one in the dict)
        # reset old tray DB
        self.trays = []
        for traynum, trayitem in trays_dict.items():
            print(' ... tray num', traynum)
            # check if long enough
            for i in range(traynum):
                if len(self.trays) < i+1:
                    # not long enough, add None
                    self.trays.append(None)

            if trayitem is not None:
                slots = []
                for slotnum, slotitem in trayitem.items():
                    # if slots is not long enough, extend it
                    for i in range(slotnum):
                        if len(slots) < i+1:
                            slots.append(None)

                    print(' ... slot num', slotnum)
                    if slotitem is not None:
                        if slotitem['type'] == 'VT54':
                            print(' ... got VT54')
                            slots[slotnum-1] = VT54(max_vol_mL=slotitem['max_vol_mL'])
                            slots[slotnum-1].update_vials(slotitem['vials'])
                            slots[slotnum-1].update_vol(slotitem['vol_mL'])
                            slots[slotnum-1].update_liquid_sample_no(slotitem['liquid_sample_no'])
                        else:
                            print(f' ... slot type {slotitem["type"]} not supported')
                            slots[slotnum-1] = None
                    else:
                        print(' ... got empty slot')
                        slots[slotnum-1] = None
                        
                self.trays[traynum-1] = PALtray(slot1 = slots[0], slot2 = slots[1], slot3 = slots[2])
            else:
                self.trays[traynum-1] = None
        return True






    
    async def backup_PAL_system_vial_table(self):
        datafile = LocalDataHandler()
        datafile.filepath = self.local_data_dump
        datafile.filename = self.PAL_file
        print(' ... updating table:', datafile.filepath, datafile.filename)
        await datafile.open_file_async(mode = 'w+')
        
        for mytray_no, mytray in enumerate(self.trays):
            if mytray is not None:
                for slot_no, slot in enumerate(mytray.slots):
                    if slot is not None:
                        tray_dict = dict(tray_no = mytray_no + 1,
                                         slot_no = slot_no + 1,
                                         content = slot.as_dict())
                        await datafile.write_data_async(json.dumps(tray_dict))
                    else:
                        tray_dict = dict(tray_no = mytray_no + 1,
                                         slot_no = slot_no + 1,
                                         content = None)
                        await datafile.write_data_async(json.dumps(tray_dict))
            else:
                tray_dict = dict(tray_no = mytray_no + 1,
                                 slot_no = None,
                                 content = None)
                await datafile.write_data_async(json.dumps(tray_dict))

        await datafile.close_file_async()
    

    async def update_PAL_system_vial_table(self, tray: int, slot: int, vial: int, vol_mL: float, liquid_sample_no: int):
        tray -= 1
        slot -= 1
        vial -= 1
        if self.trays[tray] is not None:
            if self.trays[tray].slots[slot] is not None:
                if self.trays[tray].slots[slot].vials[vial] is not True:
                    self.trays[tray].slots[slot].vials[vial] = True
                    self.trays[tray].slots[slot].vol_mL[vial] = vol_mL
                    self.trays[tray].slots[slot].liquid_sample_no[vial] = liquid_sample_no
                    # backup file
                    await self.backup_PAL_system_vial_table()
                    return True
                else:
                    return False            
            else:
                return False
        else:
            return False
        pass


    async def write_vial_holder_table_as_CSV(self, tray: int = 2, slot: int = 1):
        # save full table as backup too
        await self.backup_PAL_system_vial_table()

        datafile = LocalDataHandler()
        datafile.filename = f'VialTable__tray{tray+1}__slot{slot+1}__{datetime.now().strftime("%Y%m%d.%H%M%S%f")}.csv'
        datafile.filepath = self.local_data_dump
        print(' ... saving vial holder table to:', datafile.filepath, datafile.filename)
        await datafile.open_file_async()
        await datafile.write_data_async(','.join(['vial_no', 'liquid_sample_no', 'vol_mL']))
        for i, _ in enumerate(self.trays[tray].slots[slot].vials):
            await datafile.write_data_async(','.join([str(i+1),
                                                      str(self.trays[tray].slots[slot].liquid_sample_no[i]),
                                                      str(self.trays[tray].slots[slot].vol_mL[i])]))
        # await datafile.write_data_async('\t'.join(logdata))
        await datafile.close_file_async()

        



    async def get_vial_holder_table(self, tray: int = 2, slot: int = 1, csv = False):
        '''Returns vial tray sample table'''
        print(' ... getting table')
        tray -= 1
        slot -= 1
        if self.trays[tray] is not None:
            if self.trays[tray].slots[slot] is not None:
                if csv:
                    await self.write_vial_holder_table_as_CSV(tray, slot)
                return self.trays[tray].slots[slot].as_dict()
            else:
                return {}
        else:
            return {}


    async def get_new_vial_position(self, req_vol: float = 2.0):
        '''Returns an empty vial position for given max volume.\n
        For mixed vial sizes the req_vol helps to choose the proper vial for sample volume.\n
        It will select the first empty vial which has the smallest volume that still can hold req_vol'''
        print(self.trays)
        new_tray = None
        new_slot = None
        new_vial = None
        new_vial_vol = float('inf')

        for tray_no, tray in enumerate(self.trays):
            print(' ... tray', tray_no,tray)
            if tray is not None:
                for slot_no, slot in enumerate(tray.slots):
                    if slot is not None:
                        print(' .... slot ', slot_no,slot)
                        print(' .... ',slot.type)
                        print(' .... ',slot.max_vol_mL)
                        if slot.max_vol_mL >= req_vol and new_vial_vol > slot.max_vol_mL:
                            position = slot.first_empty()
                            if position is not None:
                                new_tray = tray_no + 1
                                new_slot = slot_no + 1
                                new_vial = position + 1
                                new_vial_vol = slot.max_vol_mL
                        
        
        return { 'tray': new_tray,
                'slot': new_slot,
                'vial': new_vial
            }


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




    async def get_last_liquid_sample_no(self):
        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_last_liquid_sample_no"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={}) as resp:
                response = await resp.json()
                return response['data']['liquid_sample']


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

        print(' ... old sampple is', PALparams.liquid_sample_no)
        if PALparams.liquid_sample_no == -1:
            print(' ... PAL need to get last sample from list')
            PALparams.liquid_sample_no = await self.get_last_liquid_sample_no()
            print(' ... last sample is ', PALparams.liquid_sample_no)
        print(' ... old sampple is', PALparams.liquid_sample_no)


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
        liquid_sampe_dict = dict(decision_uid = self.action_params['DUID'],
                                 action_uid = self.action_params['AUID'],
                                 action = self.action_params['action'],
                                 # action_pars = self.action_params['action_pars'],
                                 action_server_key = self.servkey,
                                 action_created_at = self.action_params['created_at'],
                                 action_time = self.action_params['actiontime'],
                                 action_save_path = self.FIFO_dir,
                                 action_block = self.action_params['block'],
                                 action_preempt = self.action_params['preempt'],
                                 plate_id = self.action_params['plate_id'],
                                 sample_no = self.action_params['sample_no'],
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


@app.post(f"/{servKey}/update_PAL_system_vial_table")
async def update_PAL_system_vial_table(vial: int, vol_mL: float, liquid_sample_no: int, tray: int = 2, slot: int = 1, action_params = ''):
    '''Updates PAL vial Table. If sucessful (slot was empty) returns True, else it returns False.'''
    await stat.set_run()
    retc = return_class(
        measurement_type="PAL_command",
        parameters={"command": "update_PAL_system_vial_table"},
        data={"update": await PAL.update_PAL_system_vial_table(tray, slot, vial, vol_mL, liquid_sample_no)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_vial_holder_table")
async def get_vial_holder_table(tray: int = 2, slot: int = 1, action_params = ''):
    await stat.set_run()
    retc = return_class(
        measurement_type="PAL_command",
        parameters={"command": "get_vial_holder_table"},
        data={"vial_table": await PAL.get_vial_holder_table(tray, slot)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/write_vial_holder_table_CSV")
async def write_vial_holder_table_CSV(tray: int = 2, slot: int = 1, action_params = ''):
    await stat.set_run()
    retc = return_class(
        measurement_type="PAL_command",
        parameters={"command": "get_vial_holder_table"},
        data={"vial_table": await PAL.get_vial_holder_table(tray, slot, csv = True)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_new_vial_position")
async def get_new_vial_position(req_vol: float = 2.0, action_params = ''):
    '''Returns an empty vial position for given max volume.\n
    For mixed vial sizes the req_vol helps to choose the proper vial for sample volume.\n
    It will select the first empty vial which has the smallest volume that still can hold req_vol'''
    await stat.set_run()
    retc = return_class(
        measurement_type="PAL_command",
        parameters={"command": "get_new_vial_position"},
        data={"position": await PAL.get_new_vial_position(req_vol)},
    )
    await stat.set_idle()
    return retc


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
