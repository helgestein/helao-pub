""" A device class for the Gamry USB potentiostat, used by a FastAPI server instance.

The 'gamry' device class exposes potentiostat measurement functions provided by the
GamryCOM comtypes Win32 module. Class methods are specific to Gamry devices. Device 
configuration is read from config/config.py. 
"""

import comtypes
import comtypes.client as client
import asyncio
import time
from enum import Enum
import psutil
from time import strftime
from classes import LocalDataHandler
#from classes import sample_class
import os
from classes import action_runparams
from classes import Action_params
import json


class Gamry_modes(str, Enum):
    CA = "CA"
    CP = "CP"
    CV = "CV"
    LSV = "LSV"
    EIS = "EIS"
    OCV = "OCV"

class Gamry_Irange(str, Enum):
    #NOTE: The ranges listed below are for 300 mA or 30 mA models. For 750 mA models, multiply the ranges by 2.5. For 600 mA models, multiply the ranges by 2.0.
    auto = 'auto'
    mode0 = '3pA'
    mode1 = '30pA' 
    mode2 = '300pA'
    mode3 = '3nA'
    mode4 = '30nA'
    mode5 = '300nA'
    mode6 = '3μA'
    mode7 = '30μA'
    mode8 = '300μA'
    mode9 = '3mA'
    mode10 = '30mA'
    mode11 = '300mA'
    mode12 = '3A'
    mode13 = '30A'
    mode14 = '300A'
    mode15 = '3kA'

def gamry_error_decoder(e):
    if isinstance(e, comtypes.COMError):
        hresult = 2 ** 32 + e.args[0]
        if hresult & 0x20000000:
            return GamryCOMError(
                "0x{0:08x}: {1}".format(2 ** 32 + e.args[0], e.args[1])
            )
    return e


# definition of error handling things from gamry
class GamryCOMError(Exception):
    pass


class GamryDtaqEvents(object):
    def __init__(self, dtaq):
        self.dtaq = dtaq
        self.acquired_points = []
        self.status = "idle"
        # self.buffer = buff
        self.buffer_size = 0

    def cook(self):
        count = 1
        while count > 0:
            count, points = self.dtaq.Cook(1000)
            # The columns exposed by GamryDtaq.Cook vary by dtaq and are
            # documented in the Toolkit Reference Manual.
            self.acquired_points.extend(zip(*points))
            # self.buffer[time.time()] = self.acquired_points[-1]
            # self.buffer_size += sys.getsizeof(self.acquired_points[-1]

    def _IGamryDtaqEvents_OnDataAvailable(self, this):
        self.cook()
        self.status = "measuring"

    def _IGamryDtaqEvents_OnDataDone(self, this):
        self.cook()  # a final cook
        self.status = "done"


##########################################################################
# Dummy class for when the Gamry is not used
##########################################################################
class dummy_sink:
    def __init__(self):
        self.status = "idle"


class gamry:
    def __init__(self, config_dict, stat):
        # save instrument config
        self.config_dict = config_dict
        # get Gamry object (Garmry.com)
       
        # a busy gamrycom can lock up the server
        self.kill_GamryCom()
        self.GamryCOM = client.GetModule(['{BD962F0D-A990-4823-9CF5-284D1CDD9C6D}', 1, 0])
        #self.GamryCOM = client.GetModule(self.config_dict["path_to_gamrycom"])


        self.pstat = None
         # will get the statushandler from the server to set the idle status after measurment
        self.stat = stat

        if not 'dev_id' in self.config_dict:
            self.config_dict['dev_id'] = 0
        # if not 'dev_family' in self.config_dict:
        #     self.config_dict['dev_family'] = 'Reference'
        
        if not 'local_data_dump' in self.config_dict:
            self.config_dict['local_data_dump'] = 'C:\\INST\\RUNS'
        
        self.local_data_dump = self.config_dict['local_data_dump']
        
        self.Gamry_devid = self.config_dict['dev_id']
        # self.Gamry_family = self.config_dict['dev_family']

        asyncio.gather(self.init_Gamry(self.Gamry_devid))

        
        # for Dtaq
        self.wsdataq = asyncio.Queue()
        self.dtaqsink = dummy_sink()
        self.dtaq = None
        # empty the data before new one is collected
        #self.data = collections.defaultdict(list)
        
        # for global IOloop
        self.IO_do_meas = False
        self.IO_meas_mode = None
        self.IO_sigramp = None
        self.IO_TTLwait = -1
        self.IO_TTLsend = -1
        self.IO_estop = False
        self.IO_Irange = Gamry_Irange('auto')
        
        # parameters which will be parsed via fastapi calls
        # will contain status uid, name, and additional parameters from previous server calls of a decision
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
        self.FIFO_column_headings = []
        self.FIFO_Gamryname = ''
        # holds all sample information
        #self.FIFO_sample = sample_class()
        
        self.def_action_params = Action_params()
        self.action_params = self.def_action_params.as_dict()

    ##########################################################################
    # This is main Gamry measurement loop which always needs to run
    # else if measurement is done in FastAPI calls we will get timeouts
    ##########################################################################
    async def IOloop(self):
        while True:
            await asyncio.sleep(0.5)
            if self.IO_do_meas:
                # are we in estop?
                if not self.IO_estop:
                    print(' ... Gramry got measurement request')
                    await self.measure()
                    # we need to close the connection else the Gamry is still is use 
                    # which can cause trouble if the script ends witout closing the connection
                    await self.close_connection()
                    self.IO_do_meas = False
                    # need to check here again in case estop was triggered during
                    # measurement
                    # need to set the current meas to idle first 
                    await self.stat.set_idle(self.runparams.statuid, self.runparams.statname)
                    if self.IO_estop:
                        print(' ... Gramry is in estop.')
                        await self.stat.set_estop()
                    else:
                        print(' ... setting Gamry to idle')
#                        await self.stat.set_idle()
                    print(' ... Gramry measurement is done')
                else:
                    self.IO_do_meas = False
                    print(' ... Gramry is in estop.')
                    await self.stat.set_estop()


    ##########################################################################
    # script can be blocked or crash if GamryCom is still open and busy
    ##########################################################################
    def kill_GamryCom(self):
        pyPids = {p.pid: p for p in psutil.process_iter(
            ['name', 'connections']) if p.info['name'].startswith('GamryCom')}
        
        for pid in pyPids.keys():
            print(' ... killing GamryCom on PID: ', pid)
            p = psutil.Process(pid)
            for _ in range(3):
                # os.kill(p.pid, signal.SIGTERM)
                p.terminate()
                time.sleep(0.5)
                if not psutil.pid_exists(p.pid):
                    print(" ... Successfully terminated GamryCom.")
                    return True
            if psutil.pid_exists(p.pid):
                print(
                    " ... Failed to terminate server GamryCom after 3 retries.")
                return False


    ##########################################################################
    # connect to a Gamry
    ##########################################################################
    async def init_Gamry(self, devid):
        try:
            self.devices = client.CreateObject('GamryCOM.GamryDeviceList')
            print(' ... GamryDeviceList:', self.devices.EnumSections())

            if len(self.devices.EnumSections()) >= devid:
                self.FIFO_Gamryname = self.devices.EnumSections()[devid]
                                
                if self.FIFO_Gamryname.find('IFC') == 0:
                    self.pstat = client.CreateObject('GamryCOM.GamryPC6Pstat')                    
                    print(' ... Gamry, using Interface', self.pstat)
                elif self.FIFO_Gamryname.find('REF') == 0:
                    self.pstat = client.CreateObject('GamryCOM.GamryPC5Pstat')            
                    print(' ... Gamry, using Reference', self.pstat)
                # else: # old version before Framework 7.06
                #     self.pstat = client.CreateObject('GamryCOM.GamryPstat')
                #     print(' ... Gamry, using Farmework , 7.06?', self.pstat)

                self.pstat.Init(self.devices.EnumSections()[devid])
                print(' ... ',self.pstat)
                
                
            else:
                self.pstat = None
                print(f' ... No potentiostat is connected on DevID {devid}! Have you turned it on?')

        except Exception as e:
            # this will lock up the potentiostat server 
            # happens when a not activated Gamry is connected and turned on
            # TODO: find a way to avoid it
            print(' ... fatal error initializing Gamry:', e)

    ##########################################################################
    # Open connection to Gamry
    ##########################################################################
    async def open_connection(self):
        # this just tries to open a connection with try/catch
        await asyncio.sleep(0.001)
        if not self.pstat:
            await self.init_Gamry(self.Gamry_devid)
        try:
            if self.pstat:
                self.pstat.Open()
                return {"potentiostat_connection": "connected"}
            else:
                return {"potentiostat_connection": "not initialized"}
                
        except Exception:
            #self.pstat = None
            return {"potentiostat_connection": "error"}


    ##########################################################################
    # Close connection to Gamry
    ##########################################################################
    async def close_connection(self):
        # this just tries to close a connection with try/catch
        await asyncio.sleep(0.001)
        try:
            if self.pstat:
                self.pstat.Close()
                return {"potentiostat_connection": "closed"}
            else:
                return {"potentiostat_connection": "not initialized"}
        except Exception:
            #self.pstat = None
            return {"potentiostat_connection": "error"}


    ##########################################################################
    # setting up the measurement parameters
    # need to initialize and open connection to gamry first
    ##########################################################################
    async def measurement_setup(self, AcqFreq, mode: Gamry_modes = None, *argv):
        await asyncio.sleep(0.001)
        if self.pstat:
            Irangesdict = dict(
                mode0 = 0,
                mode1 = 1,
                mode2 = 2,
                mode3 = 3,
                mode4 = 4,
                mode5 = 5,
                mode6 = 6,
                mode7 = 7,
                mode8 = 8,
                mode9 = 9,
                mode10 = 10,
                mode11 = 11,
                mode12 = 12,
                mode13 = 13,
                mode14 = 14,
                mode15 = 15)


            ## InitializePstat (from exp script)
            #https://www.gamry.com/application-notes/instrumentation/changing-potentiostat-speed-settings/
            self.pstat.SetCell(self.GamryCOM.CellOff)
            #####pstat.InstrumentSpecificInitialize ()
            self.pstat.SetPosFeedEnable(False) # False





            self.pstat.SetIEStability(self.GamryCOM.StabilityFast)#pstat.SetStability (StabilityFast)
            #Fast (0), Medium (1), Slow (2)
            #StabilityFast (0), StabilityNorm (1), StabilityMed (1), StabilitySlow (2)
            #pstat.SetCASpeed(1)#GamryCOM.CASpeedNorm)
            #CASpeedFast (0), CASpeedNorm (1), CASpeedMed (2), CASpeedSlow (3) 
            self.pstat.SetSenseSpeedMode(True)
            #pstat.SetConvention (PHE200_IConvention)
            self.pstat.SetIConvention(self.GamryCOM.Anodic) # anodic currents are positive
                

            self.pstat.SetGround(self.GamryCOM.Float)

            # Set current channel range.
            # Setting the IchRange using a voltage is preferred. The measured current is converted into a voltage on the I channel using the I/E converter.
            #0 0.03 V range, 1 0.30 V range, 2 3.00 V range, 3 30.00 V (PCI4) 12V (PC5)
            self.pstat.SetIchRange(12.0)  # The floating point number is the maximum anticipated voltage (in Volts).
            self.pstat.SetIchRangeMode(True) # auto-set
            self.pstat.SetIchOffsetEnable(False)
            self.pstat.SetIchFilter(AcqFreq)

            # Set voltage channel range.
            self.pstat.SetVchRange(12.0)
            self.pstat.SetVchRangeMode(True)
            self.pstat.SetVchOffsetEnable(False)
            self.pstat.SetVchFilter(AcqFreq)

            # Sets the range of the Auxiliary A/D input.
            self.pstat.SetAchRange(3.0)

            #pstat.SetIERangeLowerLimit(None)
            
            # Sets the I/E Range of the potentiostat.
            self.pstat.SetIERange(0.03)
            # Enable or disable current measurement auto-ranging.
            self.pstat.SetIERangeMode(True)


            if self.IO_Irange == Gamry_Irange.auto:
                print(' ... auto I range selected')
                self.pstat.SetIERange(0.03)
                self.pstat.SetIERangeMode(True)
            else:
                print(f' ... {self.IO_Irange.value} I range selected')
                print(f' ... {Irangesdict[self.IO_Irange.name]} I range selected')
                self.pstat.SetIERange(Irangesdict[self.IO_Irange.name])
                self.pstat.SetIERangeMode(False)
            # elif self.IO_Irange == Gamry_Irange.mode0:
            #     self.pstat.SetIERangeMode(False)
            #     self.pstat.SetIERange(0)



            # Sets the voltage of the auxiliary DAC output.
            self.pstat.SetAnalogOut(0.0)

            # Set the cell voltage of the Pstat.
            #self.pstat.SetVoltage(0.0)

            # Set the current interrupt IR compensation mode.
            self.pstat.SetIruptMode(self.GamryCOM.IruptOff)


            # the format of the data array is dependent upon the specific Dtaq
            # e.g. which subheader to use

            if mode == Gamry_modes.CA:
                Dtaqmode = "GamryCOM.GamryDtaqChrono"
                Dtaqtype = self.GamryCOM.ChronoAmp
                self.FIFO_column_headings = ['t_s', 'Ewe_V', 'Vu', 'I_A', 'Q', 'Vsig', 'Ach_V', 'IERange', 'Overload_HEX', 'StopTest']
                self.pstat.SetCtrlMode(self.GamryCOM.PstatMode)
            elif mode == Gamry_modes.CP:
                Dtaqmode = "GamryCOM.GamryDtaqChrono"
                Dtaqtype = self.GamryCOM.ChronoPot
                self.FIFO_column_headings = ['t_s', 'Ewe_V', 'Vu', 'I_A', 'Q', 'Vsig', 'Ach_V', 'IERange', 'Overload_HEX', 'StopTest']
                self.pstat.SetCtrlMode(self.GamryCOM.GstatMode)
            elif mode == Gamry_modes.CV:
                Dtaqmode = "GamryCOM.GamryDtaqRcv"
                Dtaqtype = None
                self.FIFO_column_headings = ['t_s', 'Ewe_V', 'Vu', 'I_A', 'Vsig', 'Ach_V', 'IERange', 'Overload_HEX', 'StopTest', 'Cycle', 'unknown1']
                self.pstat.SetCtrlMode(self.GamryCOM.PstatMode)
            elif mode == Gamry_modes.LSV:
                Dtaqmode = "GamryCOM.GamryDtaqCpiv"
                Dtaqtype = None
                self.FIFO_column_headings = ['t_s', 'Ewe_V', 'Vu', 'I_A', 'Vsig', 'Ach_V', 'IERange', 'Overload_HEX', 'StopTest', 'unknown1']
                self.pstat.SetCtrlMode(self.GamryCOM.PstatMode)
            elif mode == Gamry_modes.EIS:
#                Dtaqmode = "GamryCOM.GamryReadZ"
                Dtaqmode = "GamryCOM.GamryDtaqEis"
                Dtaqtype = None
                # this needs to be manualy extended, default are only I and V (I hope that this is Ewe_V)
                self.FIFO_column_headings = ['I_A', 'Ewe_V', 'Zreal', 'Zimag', 'Zsig', 'Zphz', 'Zfreq', 'Zmod']
                self.pstat.SetCtrlMode(self.GamryCOM.PstatMode)
            elif mode == Gamry_modes.OCV:
                Dtaqmode = "GamryCOM.GamryDtaqOcv"
                Dtaqtype = None
                self.FIFO_column_headings = ['t_s', 'Ewe_V', 'Vm', 'Vsig', 'Ach_V', 'Overload_HEX', 'StopTest', 'unknown1', 'unknown2', 'unknown3']
                self.pstat.SetCtrlMode(self.GamryCOM.GstatMode)
            else:
                return {"measurement_setup": f'mode_{mode}_not_supported'}


            try:
                self.dtaq=client.CreateObject(Dtaqmode)
                if Dtaqtype:
                    self.dtaq.Init(self.pstat, Dtaqtype, *argv)
                else:
                    self.dtaq.Init(self.pstat, *argv)
            except Exception as e:
                print(' ... Gamry Error:', gamry_error_decoder(e))

            # This method, when enabled, 
            # allows for longer experiments with fewer points, 
            # but still acquires data quickly around each step.
            if mode == Gamry_modes.CA:
                self.dtaq.SetDecimation(False)
            elif mode == Gamry_modes.CP:
                self.dtaq.SetDecimation(False)


            self.dtaqsink = GamryDtaqEvents(self.dtaq)
            return {"measurement_setup": f'setup_{mode}'}
        else:
            return {"measurement_setup": "not initialized"}


    ##########################################################################
    # performing a measurement with the Gamry
    # this is the main function for the instrument
    ##########################################################################
    async def measure(self): 
        await asyncio.sleep(0.001)
        if self.pstat:
            # TODO: 
                # - I/E range: auto, fixed
                # - IRcomp: None, PF, CI
                # - max current/voltage
                # - eq time
                # - init time delay
                # - conditioning
                # - sampling mode: fast, noise reject, surface
                


            self.FIFO_gamryheader += f'\n%ierangemode={self.IO_Irange.name}'

            # push the signal ramp over
            try:
                self.pstat.SetSignal(self.IO_sigramp)
            except Exception as e:
                print(' ... gamry error in signal')
                print(gamry_error_decoder(e))
                self.pstat.SetCell(self.GamryCOM.CellOff)
                return {"measure": 'signal_error'}
            
            
            # TODO:
            # send or wait for trigger
            # Sets the voltage of the auxiliary DAC output.
            # self.pstat.SetAnalogOut
            # Sets the digital output setting.
            # self.pstat.SetDigitalOut
            # self.pstat.DigitalIn
            
            print('.... DigiOut:', self.pstat.DigitalOut())
            print('.... DigiIn:', self.pstat.DigitalIn())
            # first, wait for trigger
            if self.IO_TTLwait >= 0:
                while self.IO_do_meas:
                    bits = self.pstat.DigitalIn()
                    print(' ... Gamry DIbits', bits)
                    if self.IO_TTLwait & bits:
                        break
                    # if self.IO_TTLwait == 0:
                    #     #0001
                    #     if (bits & 0x01):
                    #         break
                    # elif self.IO_TTLwait == 1:
                    #     #0010
                    #     if (bits & 0x02):
                    #         break
                    # elif self.IO_TTLwait == 2:
                    #     #0100
                    #     if (bits & 0x04):
                    #         break
                    # elif self.IO_TTLwait == 3:
                    #     #1000
                    #     if (bits & 0x08):
                    #         break
                    break # for testing, we don't want to wait forever
                    await asyncio.sleep(0.001)
                    
            # second, send a trigger
            # TODO: need to reset trigger first during init to high/low
            # if its in different state
            # and reset it after meas
            if self.IO_TTLsend >= 0:
#                self.pstat.SetDigitalOut(self.IO_TTLsend,self.IO_TTLsend)
                print(self.pstat.SetDigitalOut(self.IO_TTLsend,self.IO_TTLsend)) # bitmask on
#                print(self.pstat.SetDigitalOut(0,self.IO_TTLsend)) # bitmask off
                # if self.IO_TTLsend == 0:
                #     #0001
                #     self.pstat.SetDigitalOut(1,1)
                # elif self.IO_TTLsend == 1:
                #     #0010
                #     self.pstat.SetDigitalOut(2,2)
                # elif self.IO_TTLsend == 2:
                #     #0100
                #     self.pstat.SetDigitalOut(4,4)
                # elif self.IO_TTLsend == 3:
                #     #1000
                #     self.pstat.SetDigitalOut(8,8)

            
            # turn on the potentiostat output
            self.pstat.SetCell(self.GamryCOM.CellOn)
            
            
            # Use the following code to discover events:
            #client.ShowEvents(dtaqcpiv)
            connection = client.GetEvents(self.dtaq, self.dtaqsink)

            try:
                # get current time and start measurement
                self.FIFO_epoch =  time.time_ns()
                self.dtaq.Run(True)
            except Exception as e:
                print(' ... gamry error run')
                print(gamry_error_decoder(e))
                self.pstat.SetCell(self.GamryCOM.CellOff)
                del connection
                return {"measure": 'run_error'}
                

            # empty the data before new one is collected
            #self.data = collections.defaultdict(list)
            
            
            client.PumpEvents(0.001)
            sink_status = self.dtaqsink.status
            counter = 0

            # open new file and write header
            datafile = LocalDataHandler()
            datafile.filename = self.FIFO_name
            datafile.filepath = self.FIFO_dir
            # if header is != '' then it will be written when file is opened first time
            # not if the file already exists
            #datafile.fileheader = ''
            await datafile.open_file_async()
          

            # ANEC2 will also measure more then one sample at a time, so we need to have a list of samples
            await datafile.write_sampleinfo_async(self.action_params)
            
            # write Gamry specific data
            await datafile.write_data_async('%gamry='+str(self.FIFO_Gamryname))
            await datafile.write_data_async(self.FIFO_gamryheader)
            await datafile.write_data_async('%techniqueparamsname=')
            await datafile.write_data_async('%techniquename='+str(self.IO_meas_mode.name))
            await datafile.write_data_async('%epoch_ns='+str(self.FIFO_epoch))
            await datafile.write_data_async('%version=0.1')
            await datafile.write_data_async('%column_headings='+'\t'.join(self.FIFO_column_headings))

            while sink_status != "done" and self.IO_do_meas:
            #while sink_status == "measuring":
                # need some await points
                await asyncio.sleep(0.001)
                client.PumpEvents(0.001)
                # this is a temp data which gets the data point by point
                # write this to a file so we don't loose any data
                while counter < len(self.dtaqsink.acquired_points) and self.IO_do_meas:
                    # need some await points
                    await asyncio.sleep(0.001)
                    tmp_datapoints = self.dtaqsink.acquired_points[counter]
                    #print(tmp_datapoints)
                    #print(counter)
                    if self.wsdataq.full():
                        _ = await self.wsdataq.get()
                        self.wsdataq.task_done()
                    #print(' ... ',tmp_datapoints)
                    
                    # Need to get additional data for EIS
                    if self.IO_meas_mode == Gamry_modes.EIS:
                        test = list(tmp_datapoints)
                        test.append(self.dtaqsink.dtaq.Zreal())
                        test.append(self.dtaqsink.dtaq.Zimag())
                        test.append(self.dtaqsink.dtaq.Zsig())
                        test.append(self.dtaqsink.dtaq.Zphz())
                        test.append(self.dtaqsink.dtaq.Zfreq())
                        test.append(self.dtaqsink.dtaq.Zmod())
                        tmp_datapoints = tuple(test)

                    # TODO: add data quality control here



                    
                    # send data with asigned headings to wsqueue
                    # print(' ... gamry putting new data on dataq')
                    await self.wsdataq.put({k: [v] for k, v in zip(self.FIFO_column_headings, tmp_datapoints)})
                    
                    
                    # put new data in file
                    await datafile.write_data_async('\t'.join([str(num) for num in tmp_datapoints]))
                    counter += 1
    
                # this copies the complete chunk of data again and again
                # what we are going to do with this?
                #dtaqarr = self.dtaqsink.acquired_points
                #self.data = dtaqarr

                sink_status = self.dtaqsink.status


            self.pstat.SetCell(self.GamryCOM.CellOff)

            # close file
            await datafile.close_file_async()
            # not needed if we always use same file and have global header etc
            del datafile

            # delete this at the very last step
            del connection
            # connection will be closed in IOloop
            #self.close_connection()
            return {"measure": f'done_{self.IO_meas_mode}'}
        else:
            return {"measure": "not initialized"}


    ##########################################################################
    #  return status of data structure
    ##########################################################################
    async def status(self):
        await asyncio.sleep(0.001)
        return self.dtaqsink.status

    ##########################################################################
    #  stops measurement, writes all data and returns from meas loop
    ##########################################################################
    async def stop(self, runparams: action_runparams):
        # turn off cell and run before stopping meas loop
        if self.IO_do_meas:
            self.pstat.SetCell(self.GamryCOM.CellOff)
            self.dtaq.Run(False)
            # file and Gamry connection will be closed with the meas loop
            self.IO_do_meas = False
            # await self.stat.set_idle(runparams.statuid, runparams.statname)
        # else:
        #     #was already stopped so need to set to idle here
        await self.stat.set_idle(runparams.statuid, runparams.statname)


    ##########################################################################
    #  same as estop, but also sets flag
    ##########################################################################
    async def estop(self, switch, runparams: action_runparams):
        # should be the same as stop()

        if self.IO_do_meas:
            self.IO_estop = switch
            if switch:
                # if self.IO_do_meas:
                self.pstat.SetCell(self.GamryCOM.CellOff)
                self.dtaq.Run(False)
                # file and Gamry connection will be closed with the meas loop
                self.IO_do_meas = False
        else:
            #was already stopped so need to set to idle here
            if switch:
                await self.stat.set_estop()
            # else:
        await self.stat.set_idle(runparams.statuid, runparams.statname)


    ##########################################################################
    #  LSV definition
    ##########################################################################
    async def technique_LSV(self, 
        Vinit: float, 
        Vfinal: float, 
        ScanRate: float, 
        SampleRate: float,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()
                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.LSV
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalRamp")
    
                try:
                    self.IO_sigramp.Init(
                        self.pstat, Vinit, Vfinal, ScanRate, SampleRate, self.GamryCOM.PstatMode
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
    
                eta = abs(Vfinal - Vinit)/ScanRate #+delay
                
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Vinit={Vinit}\n'
                self.FIFO_gamryheader += f'%Vinit={Vfinal}\n'
                self.FIFO_gamryheader += f'%scanrate={ScanRate}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%eta={eta}'

                self.set_filedir()
                
                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Vinit": Vinit,
                "Vfinal": Vfinal,
                "ScanRate": ScanRate,
                "SampleRate": SampleRate,
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }


    ##########################################################################
    #  CA definition
    ##########################################################################
    async def technique_CA(self, 
        Vval: float, 
        Tval: float, 
        SampleRate: float,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        print('################################################################')
        print(runparams)
        print('################################################################')
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()

                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.CA
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalConst")
    
                try:
                    self.IO_sigramp.Init(
                        self.pstat, Vval, Tval, SampleRate, self.GamryCOM.PstatMode
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
                    print(' ... Gamry Error:', err_code)
    
                eta = Tval #+delay
    
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Vval={Vval}\n'
                self.FIFO_gamryheader += f'%Tval={Tval}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%eta={eta}'

                self.set_filedir()

                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Vval": Vval,
                "Tval": Tval,
                "SampleRate": SampleRate
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }


    ##########################################################################
    #  CP definition
    ##########################################################################
    async def technique_CP(self, 
        Ival: float, 
        Tval: float, 
        SampleRate: float,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()
                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.CP
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalConst")
    
                try:
                    self.IO_sigramp.Init(
                        self.pstat, Ival, Tval, SampleRate, self.GamryCOM.GstatMode
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
                    print(' ... Gamry Error:', err_code)
    
                eta = Tval  #+delay
    
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Ival={Ival}\n'
                self.FIFO_gamryheader += f'%Tval={Tval}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%eta={eta}'
    
                self.set_filedir()
    
                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')


            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Ival": Ival,
                "Tval": Tval,
                "SampleRate": SampleRate
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }


    async def technique_CV(self,
        Vinit: float,
        Vapex1: float,
        Vapex2: float,
        Vfinal: float,
        ScanInit: float,
        ScanApex: float,
        ScanFinal: float,
        HoldTime0: float,
        HoldTime1: float,
        HoldTime2: float,
        SampleRate: float,
        Cycles: int,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()
                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.CV
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalRupdn")
    
                try:
                    self.IO_sigramp.Init(
                        self.pstat,
                        Vinit,
                        Vapex1,
                        Vapex2,
                        Vfinal,
                        ScanInit,
                        ScanApex,
                        ScanFinal,
                        HoldTime0,
                        HoldTime1,
                        HoldTime2,
                        SampleRate,
                        Cycles,
                        self.GamryCOM.PstatMode,
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
    
                eta  = abs(Vapex1 - Vinit)/ScanInit
                eta += abs(Vfinal - Vapex2)/ScanFinal 
                eta += abs(Vapex2 - Vapex1)/ScanApex * Cycles
                eta += abs(Vapex2 - Vapex1)/ScanApex * 2.0 * (Cycles-1) #+delay
    
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Vinit={Vinit}\n'
                self.FIFO_gamryheader += f'%Vapex1={Vapex1}\n'
                self.FIFO_gamryheader += f'%Vapex2={Vapex2}\n'
                self.FIFO_gamryheader += f'%Vfinal={Vfinal}\n'
                self.FIFO_gamryheader += f'%scaninit={ScanInit}\n'
                self.FIFO_gamryheader += f'%scanapex={ScanApex}\n'
                self.FIFO_gamryheader += f'%scanfinal={ScanFinal}\n'
                self.FIFO_gamryheader += f'%holdtime0={HoldTime0}\n'
                self.FIFO_gamryheader += f'%holdtime1={HoldTime1}\n'
                self.FIFO_gamryheader += f'%holdtime2={HoldTime2}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%cycles={Cycles}\n'
                self.FIFO_gamryheader += f'%eta={eta}'
    
                self.set_filedir()

                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')

        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Vinit": Vinit,
                "Vapex1": Vapex1,
                "Vapex2": Vapex2,
                "Vfinal": Vfinal,
                "ScanInit": ScanInit,
                "ScanApex": ScanApex,
                "ScanFinal": ScanFinal,
                "HoldTime0": HoldTime0,
                "HoldTime1": HoldTime1,
                "HoldTime2": HoldTime2,
                "SampleRate": SampleRate,
                "Cycles": Cycles,
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }


    ##########################################################################
    #  EIS definition
    ##########################################################################
    async def technique_EIS(self, 
        Vval,
        Tval,
        Freq,
        RMS,
        Precision,
        SampleRate,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()
                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.EIS
                argv = (Freq, RMS, Precision)
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode, *argv)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalConst")
                try:
                    self.IO_sigramp.Init(
                        self.pstat, Vval, Tval, SampleRate, self.GamryCOM.PstatMode
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
    
                eta = Tval
                
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Vval={Vval}\n'
                self.FIFO_gamryheader += f'%Tval={Tval}\n'
                self.FIFO_gamryheader += f'%freq={Freq}\n'
                self.FIFO_gamryheader += f'%rms={RMS}\n'
                self.FIFO_gamryheader += f'%precision={Precision}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%eta={eta}'
                
                
                self.set_filedir()
                
                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                'Vval':Vval,
                'Tval':Tval,
                'freq':Freq,
                'RMS':RMS,
                'precision':Precision,
                'samplerate':SampleRate
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }


    ##########################################################################
    #  OCV definition
    ##########################################################################
    async def technique_OCV(self, 
        Tval: float, 
        SampleRate: float,
        runparams: action_runparams,
        TTLwait: int = -1,
        TTLsend: int = -1,
        Irange: Gamry_Irange = 'auto'
    ):
        """The OCV class manages data acquisition for a Controlled Voltage I-V curve. However, it is a special purpose curve
        designed for measuring the open circuit voltage over time. The measurement is made in the Potentiostatic mode but with the Cell
        Switch open. The operator may set a voltage stability limit. When this limit is met the Ocv terminates."""
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        retval = await self.open_connection()
        if retval["potentiostat_connection"] == "connected":
            if self.pstat and not self.IO_do_meas:
                try:
                    # use parsed version
                    self.action_params = json.loads(runparams.action_params)
                except Exception:
                    # use default
                    self.action_params = self.def_action_params.as_dict()
                self.IO_Irange = Irange
                self.IO_TTLwait = TTLwait
                self.IO_TTLsend = TTLsend
                # set parameters for IOloop meas
                self.IO_meas_mode = Gamry_modes.OCV
                await self.measurement_setup(1.0/SampleRate, self.IO_meas_mode)
                # setup the experiment specific signal ramp
                self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalConst")
    
                try:
                    self.IO_sigramp.Init(
                        self.pstat, 0.0, Tval, SampleRate, self.GamryCOM.GstatMode
                    )
                    err_code = "0"
                except Exception as e:
                    err_code = gamry_error_decoder(e)
                    print(' ... Gamry Error:', err_code)
    
                eta = Tval #+delay
    
                self.FIFO_gamryheader = ''
                self.FIFO_gamryheader += f'%Tval={Tval}\n'
                self.FIFO_gamryheader += f'%samplerate={SampleRate}\n'
                self.FIFO_gamryheader += f'%eta={eta}'
    
                self.set_filedir()
    
                # signal the IOloop to start the measrurement
                self.runparams = runparams
                self.IO_do_meas = True
                # idle will bet set in main function after meas is done
            elif self.IO_do_meas:
                err_code = "meas already in progress"            
                await self.stat.set_idle(runparams.statuid, runparams.statname)
            else:
                err_code = "not initialized"
                await self.stat.set_idle(runparams.statuid, runparams.statname)
        else:
            err_code = retval["potentiostat_connection"]
            await self.stat.set_idle(runparams.statuid, runparams.statname)
            print('###############################################################')
            print(retval)
            print('###############################################################')

        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Tval": Tval,
                "SampleRate": SampleRate
            },
            "err_code": err_code,
            "eta": eta,
            "datafile": os.path.join(self.FIFO_dir,self.FIFO_name)
        }

    def set_filedir(self):
        samplenostr = '_'.join([str(sample) for sample in self.action_params['sample_no']])
        self.FIFO_name = f'sampleno{samplenostr}__gamry__{self.IO_meas_mode.name}_{strftime("%Y%m%d_%H%M%S%z.txt")}'
        # self.FIFO_dir = self.local_data_dump
        # self.local_data_dump will be skipped if second param is absolute path
        self.FIFO_dir = os.path.join(self.local_data_dump,self.action_params['save_folder'])
        print(' ... saving to:',self.FIFO_dir)
