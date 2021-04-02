# NIdaqmx server
# https://nidaqmx-python.readthedocs.io/en/latest/task.html
# http://127.0.0.1:8006/docs#/default
# https://readthedocs.org/projects/nidaqmx-python/downloads/pdf/stable/


# TODO:
# done - add wsdata with buffering for visualizers
# - add wsstatus
# - test what happens if NImax broswer has nothing configured and only lists the device
# done - Current and voltage stream with interrut handler?
# - create tasks for action library
# - handshake as stream with interrupt

import os
import sys

from importlib import import_module
import json
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify

#import requests
import asyncio
#import aiohttp
#from enum import Enum
#import numpy as np
import time

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


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))
from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager
from classes import LocalDataHandler
from classes import sample_class


################## Helper functions ##########################################
# this could also move into a separate driver, but should not be necessary
# as all of this can also be in the FastAPI functions itself
class cNIMAX:
    # in principle we can also just call predefined tasks from NImax app,
    # but I define my own here to be more flexible
    
    def __init__(self, config_dict):
        self.config_dict = config_dict
        print(' ... init NI-MAX')
 
        if not 'local_data_dump' in self.config_dict:
            self.config_dict['local_data_dump'] = 'C:\\temp'

        self.local_data_dump = self.config_dict['local_data_dump']


        # seems to work by just defining the scale and then only using its name
        self.Iscale = nidaqmx.scale.Scale.create_lin_scale('NEGATE3',-1.0,0.0,UnitsPreScaled.AMPS,'AMPS')
        self.time_stamp = time.time()
        
        self.qIV = asyncio.Queue(maxsize=100)#,loop=asyncio.get_event_loop())
        self.qsettings = asyncio.Queue(maxsize=100)#,loop=asyncio.get_event_loop())
        # this defines the time axis, need to calculate our own
        self.samplingrate = 10 # samples per second
        # used to keep track of time during data readout
        self.IVtimeoffset = 0.0
        self.buffersize = 1000 # finite samples or size of buffer depending on mode
        
        
        self.task_CellCurrent = None
        self.task_CellVoltage = None
        self.task_IV_run = False
        self.activeCell = [False for _ in range(9)]


        # for saving data localy
        self.datafile = LocalDataHandler()
        self.FIFO_epoch = None
        #self.FIFO_header = ''
        self.FIFO_NImaxheader = '' # measuement specific, will be reset each measurement
        self.FIFO_name = ''
        self.FIFO_dir = ''
        self.FIFO_column_headings = ['t_s', 'ICell1_A', 'ICell2_A', 'ICell3_A', 'ICell4_A', 'ICell5_A', 'ICell6_A', 'ICell7_A', 'ICell8_A', 'ICell9_A',
                                     'ECell1_V', 'ECell2_V', 'ECell4_V', 'ECell4_V', 'ECell5_V', 'ECell6_V', 'ECell7_V', 'ECell8_V', 'ECell9_V']


        # holds all sample information
        self.FIFO_sample = sample_class()


    def create_IVtask(self):
        # Voltage reading is MASTER
        self.task_CellCurrent = nidaqmx.Task()
        for myname, mydev  in self.config_dict.dev_CellCurrent.items():
            self.task_CellCurrent.ai_channels.add_ai_current_chan(mydev,
                                                        name_to_assign_to_channel = 'Cell_'+myname,
                                                        terminal_config=TerminalConfiguration.DIFFERENTIAL,
                                                        min_val=-0.02,
                                                        max_val=+0.02,
                                                        units=VoltageUnits.FROM_CUSTOM_SCALE,
                                                        shunt_resistor_loc=CurrentShuntResistorLocation.EXTERNAL,
                                                        ext_shunt_resistor_val=5.0,
                                                        custom_scale_name='NEGATE3' # TODO: this can be a per channel calibration
                                                        )
        self.task_CellCurrent.ai_channels.all.ai_lowpass_enable = True
        self.task_CellCurrent.timing.cfg_samp_clk_timing(self.samplingrate, 
                                                         source="", 
                                                         active_edge=Edge.RISING, 
                                                         sample_mode=AcquisitionType.CONTINUOUS, 
                                                         samps_per_chan=self.buffersize)
        # TODO can increase the callbackbuffersize if needed
        #self.task_CellCurrent.register_every_n_samples_acquired_into_buffer_event(10,self.streamCURRENT_callback)
        self.task_CellCurrent.register_every_n_samples_acquired_into_buffer_event(10,self.streamIV_callback)

        # Voltage reading is SLAVE
        # we cannot combine both tasks into one as they run on different DAQs        
        # define the VOLT and CURRENT task as they need to stay in memory
        self.task_CellVoltage = nidaqmx.Task()
        for myname,mydev  in self.config_dict.dev_CellVoltage.items():
            self.task_CellVoltage.ai_channels.add_ai_voltage_chan(mydev,
                                                      name_to_assign_to_channel = 'Cell_'+myname,
                                                      terminal_config=TerminalConfiguration.DIFFERENTIAL,
                                                      min_val=-10.0,
                                                      max_val=+10.0,
                                                      units=VoltageUnits.VOLTS,
                                                      )

        # does this globally enable lowpass or only for channels in task?
        self.task_CellVoltage.ai_channels.all.ai_lowpass_enable = True        
        #self.task_CellVoltage.ai_lowpass_enable = True            
        self.task_CellVoltage.timing.cfg_samp_clk_timing(self.samplingrate, 
                                                       source="", 
                                                       active_edge=Edge.RISING, 
                                                       sample_mode=AcquisitionType.CONTINUOUS, 
                                                       samps_per_chan=self.buffersize)
        # each card need its own physical trigger input

        if self.config_dict.dev_CellVoltage_trigger != '' and self.config_dict.dev_CellCurrent_trigger != '':
            self.task_CellVoltage.triggers.start_trigger.trig_type = TriggerType.DIGITAL_EDGE
            self.task_CellVoltage.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.config_dict.dev_CellVoltage_trigger, 
                trigger_edge = Edge.RISING)

            self.task_CellCurrent.triggers.start_trigger.trig_type = TriggerType.DIGITAL_EDGE
            self.task_CellCurrent.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.config_dict.dev_CellCurrent_trigger, 
                trigger_edge = Edge.RISING)
 

    def streamIV_callback(self, task_handle, every_n_samples_event_type,number_of_samples, callback_data):
        # TODO: how to turn task_handle into the task object?
        if self.task_IV_run:
            try:
                # start seq: V then current, so read current first then Volt
                # put callback only on current (Volt should the always have enough points)
                # readout is requested-1 when callback is on requested
                dataI = self.task_CellCurrent.read(number_of_samples_per_channel=number_of_samples)
                dataV = self.task_CellVoltage.read(number_of_samples_per_channel=number_of_samples)
                # this is also what NImax seems to do
                time = [self.IVtimeoffset+i/self.samplingrate for i in range(len(dataI[0]))]
                # update timeoffset
                self.IVtimeoffset += number_of_samples/self.samplingrate
                #print(' ... NImax VOLT data: ',data)
                if self.qIV.full():
                    print(' ... NImax qIV is full ...')
                    _ = self.qIV.get_nowait()
                new_data = {'t_s':time, 'I_A':dataI, 'E_V':dataV}
                self.qIV.put_nowait(new_data)

                for i in range(len(dataI[0])):
                    self.datafile.write_data_sync(str(new_data['t_s'][i])+'\t'+
                                               str(new_data['I_A'][0][i])+'\t'+
                                               str(new_data['I_A'][1][i])+'\t'+
                                               str(new_data['I_A'][2][i])+'\t'+
                                               str(new_data['I_A'][3][i])+'\t'+
                                               str(new_data['I_A'][4][i])+'\t'+
                                               str(new_data['I_A'][5][i])+'\t'+
                                               str(new_data['I_A'][6][i])+'\t'+
                                               str(new_data['I_A'][7][i])+'\t'+
                                               str(new_data['I_A'][8][i])+'\t'+
                                               str(new_data['E_V'][0][i])+'\t'+
                                               str(new_data['E_V'][1][i])+'\t'+
                                               str(new_data['E_V'][2][i])+'\t'+
                                               str(new_data['E_V'][3][i])+'\t'+
                                               str(new_data['E_V'][4][i])+'\t'+
                                               str(new_data['E_V'][5][i])+'\t'+
                                               str(new_data['E_V'][6][i])+'\t'+
                                               str(new_data['E_V'][7][i])+'\t'+
                                               str(new_data['E_V'][8][i])
                                               )
            except Exception:
                print(' ... canceling NImax IV stream')                     
        return 0


    # waits for TTL handshake, e.g. high signal
    async def run_task_RSH_TTL_handshake(self):
        with nidaqmx.Task() as task_handshake:
            if 'port' in self.config_dict.dev_RSHTTLhandshake.keys() and 'term' in self.config_dict.dev_RSHTTLhandshake.keys():
                task_handshake.ci_channels.add_ci_count_edges_chan(self.config_dict.dev_RSHTTLhandshake['port'],
                                                                   edge=Edge.RISING,
                                                                   initial_count=0,
                                                                   count_direction=CountDirection.COUNT_UP
                                                                   )
                task_handshake.ci_channels[0].ci_count_edges_term = self.config_dict.dev_RSHTTLhandshake['term']


                # TODO: need to improve this once the real hardware is ready
                while True:
                    print(' ... waiting for RSH handshake ...')
                    data = task_handshake.read()
                    if data:
                        print(' ... got RSH handshake ...')
                        break
                    await asyncio.sleep(0.5)
                
                return {"name":"RSH_TTL_handshake",
                    "status": data
                   }


    async def run_task_getFSW(self, FSW):
        with nidaqmx.Task() as task_FSW:
            if FSW in self.config_dict.dev_FSW.keys():
                task_FSW.di_channels.add_di_chan(self.config_dict.dev_FSW[FSW],
                                                 line_grouping=LineGrouping.CHAN_PER_LINE)
                data = task_FSW.read(number_of_samples_per_channel=1)
                return {"name":[FSW],
                    "status": data
                   }
                
            
    async def run_task_FSWBCD(self, BCDs, value):
        BCD_list = await self.sep_str(BCDs)
        cmds = []
        with nidaqmx.Task() as task_FSWBCD:
            for BCD in BCD_list:
                if BCD in self.config_dict.dev_FSWBCDCmd.keys():
                    task_FSWBCD.do_channels.add_do_chan(self.config_dict.dev_FSWBCDCmd[BCD],
                                                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    cmds.append(value)
            if cmds:
                task_FSWBCD.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}


    async def run_task_Pumps(self, pumps, value):
        pump_list = await self.sep_str(pumps)
        cmds = []
        with nidaqmx.Task() as task_Pumps:
            for pump in pump_list:
                if pump in self.config_dict.dev_Pumps.keys():
                    task_Pumps.do_channels.add_do_chan(self.config_dict.dev_Pumps[pump],
                                                       line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    cmds.append(value)
            if cmds:
                task_Pumps.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}


    async def run_task_GasFlowValves(self, valves, value):
        valve_list = await self.sep_str(valves)
        cmds = []
        with nidaqmx.Task() as task_GasFlowValves:
            for valve in valve_list:
                if valve in self.config_dict.dev_GasFlowValves.keys():
                   task_GasFlowValves.do_channels.add_do_chan(self.config_dict.dev_GasFlowValves[valve],
                                                              line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                   cmds.append(value)
            if cmds:
                task_GasFlowValves.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}


    async def run_task_Master_Cell_Select(self, cells, value):
        cell_list = await self.sep_str(cells)
        if len(cell_list)>1:
            print(' ... Multiple cell selected. Only one can be Master cell. Using first one!')
            print(cell_list)
            cell_list = [cell_list[0]]
            print(cell_list)
        cmds = []
        with nidaqmx.Task() as task_MasterCell:
            for cell in cell_list:
                if cell in self.config_dict.dev_MasterCellSelect.keys():
                    task_MasterCell.do_channels.add_do_chan(self.config_dict.dev_MasterCellSelect[cell],
                                                            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    cmds.append(value)
            if cmds:
                task_MasterCell.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}


    async def run_task_Active_Cells_Selection(self, cells, value):
        cell_list = await self.sep_str(cells)
        cmds = []
        with nidaqmx.Task() as task_ActiveCell:
            for cell in cell_list:
                if cell in self.config_dict.dev_ActiveCellsSelection.keys():
                    task_ActiveCell.do_channels.add_do_chan(self.config_dict.dev_ActiveCellsSelection[cell],
                                                            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    cmds.append(value)
                
                self.activeCell[int(cell)-1] = value

            if self.qsettings.full():
                print(' ... NImax qsettings is full ...')
                _ = self.qsettings.get_nowait()
            self.qsettings.put_nowait({'activeCell':self.activeCell})


            if cmds:
                task_ActiveCell.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}


    # TODO: test what happens if we clear all NIMax settings?
    async def run_task_Cell_IV(self, on):
        if on and not self.task_IV_run:


            ### save to file start settings
            self.FIFO_epoch =  time.time_ns()
            self.FIFO_name = f'NImax_{time.strftime("%Y%m%d_%H%M%S%z.txt")}'
            self.FIFO_dir = self.local_data_dump
            # open new file and write header
            self.datafile.filename = self.FIFO_name
            self.datafile.filepath = self.FIFO_dir
            # if header is != '' then it will be written when file is opened first time
            # not if the file already exists
            #datafile.fileheader = ''
            self.datafile.open_file_sync()         
            # ANEC2 will also measure more then one sample at a time, so we need to have a list of samples
            self.datafile.write_sampleinfo_sync(self.FIFO_sample)        
            # NImax specific data
            #self.datafile.write_data_sync(self.FIFO_NImaxheader)
            self.datafile.write_data_sync('%epoch_ns='+str(self.FIFO_epoch))
            self.datafile.write_data_sync('%version=0.1')
            self.datafile.write_data_sync('%column_headings='+'\t'.join(self.FIFO_column_headings))
            ### save to file end settings



            self.create_IVtask()
            # start slave first
            self.task_CellVoltage.start()
            # then start master to trigger slave
            self.task_CellCurrent.start()
            self.task_IV_run = True


        elif not on and self.task_IV_run:
            self.task_IV_run = False
#            self.task_CellCurrent.stop()
#            self.task_CellVoltage.stop()
            self.task_CellCurrent.close()
            self.task_CellVoltage.close()
            # close file
            self.datafile.close_file_sync()

        return {
            "meas": self.task_IV_run,
            "name":['Cell_'+key for key in self.config_dict.dev_CellCurrent.keys()],
            "status":[on for _ in self.config_dict.dev_CellCurrent.keys()],
            "err_code": 0,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }



    async def sep_str(self, cells):  
        sepvals = [',','\t',';','::',':']
        new_cells = None
        for sep in sepvals:
            if not (cells.find(sep) == -1):
                    new_cells = cells.split(sep)
                    break    

        # single axis
        if new_cells == None:
            new_cells = cells

        # convert single axis move to list        
        if type(new_cells) is not list:
            new_cells = [new_cells]

        return new_cells


################## END Helper functions #######################################

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


app = FastAPI(title="NIdaqmx server",
    description="",
    version="1.0")


@app.post(f"/{servKey}/run_task_GasFlowValves")
async def run_task_GasFlowValves(valves: str, on: bool = True):
    """Provide list of Valves (number) separated by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_GasFlowValves",
                    "parameters": {
                        "valves": valves,
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_GasFlowValves(valves, on),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_Master_Cell_Select")
async def run_task_Master_Cell_Select(cells: str, on: bool = True):
    """Provide list of Cells separated by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_Master_Cell_Select",
                    "parameters": {
                        "cells": cells,
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_Master_Cell_Select(cells, on),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_Active_Cells_Selection")
async def run_task_Active_Cells_Selection(cells: str, on: bool = True):
    """Provide list of Cells (number) separated by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_Active_Cells_Selection",
                    "parameters": {
                        "cells": cells,
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_Active_Cells_Selection(cells, on),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_Pumps")
async def run_task_Pumps(pumps: str, on: bool = True):
    """Provide list of Pumps separated by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_Pumps",
                    "parameters": {
                        "pumps": pumps,
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_Pumps(pumps, on),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_FSWBCD")
async def run_task_FSWBCD(BCDs: str, on: bool = True):
    """Provide list of Pumps separated by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_FSWBCD",
                    "parameters": {
                        "BCD": BCDs,
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_FSWBCD(BCDs, on),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_FSW_error")
async def run_task_FSW_error():
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_FSW_error",
                    "parameters": {
                        },
                    },
        data=await NIMAX.run_task_getFSW('Error'),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_FSW_done")
async def run_task_FSW_done():
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_FSW_done",
                    "parameters": {
                        },
                    },
        data=await NIMAX.run_task_getFSW('Done'),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_RSH_TTL_handshake")
async def run_task_RSH_TTL_handshake():
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_RSH_TTL_handshake",
                    "parameters": {
                        },
                    },
        data=await NIMAX.run_task_RSH_TTL_handshake(),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_task_Cell_IV")
async def run_task_Cell_IV(on: bool = True):
    """Get the current/voltage measurement for each cell.
    Only active cells are plotted in visualizer."""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task_Cell_IV",
                    "parameters": {
                        "ON": on
                        },
                    },
        data=await NIMAX.run_task_Cell_IV(on),
    )
    await stat.set_idle()
    return retc


@app.on_event("startup")
def startup_event():
    global NIMAX
    NIMAX = cNIMAX(S.params)
    global stat
    stat = StatusHandler()
    # websockets
    global wsdata
    wsdata = wsConnectionManager()
    global wsstatus
    wsstatus = wsConnectionManager()
    global wsdatasettings
    wsdatasettings = wsConnectionManager()


@app.websocket(f"/{servKey}/ws_data_settings")
async def websocket_data_setings(websocket: WebSocket):
    await wsdatasettings.send(websocket, NIMAX.qsettings, 'NImax_data_settings')


@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    await wsdata.send(websocket, NIMAX.qIV, 'NImax_data')


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'NImax_status')


@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return return_status(
        measurement_type="get_status",
        parameters={},
        status=stat.dict,
    )


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


@app.on_event("shutdown")
def shutdown():
    return ""


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
