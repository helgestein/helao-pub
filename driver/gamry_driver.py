""" A device class for the Gamry USB potentiostat, used by a FastAPI server instance.

The 'gamry' device class exposes potentiostat measurement functions provided by the
GamryCOM comtypes Win32 module. Class methods are specific to Gamry devices. Device 
configuration is read from config/config.py. 
"""

import comtypes
import comtypes.client as client
import collections
import asyncio
import time
from enum import Enum
import psutil
from time import strftime
from classes import LocalDataHandler



class Gamry_modes(str, Enum):
    CA = "CA"
    CP = "CP"
    CV = "CV"
    LSV = "LSV"
    EIS = "EIS"
    OCV = "OCV"

class Gamry_Irange(str, Enum):
    #NOTE: The ranges listed below are for 300 mA or 30 mA models. For 750 mA models, multiply the ranges by 2.5. For 600 mA models, multiply the ranges by 2.0.
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
    def __init__(self, config_dict):
        # save instrument config
        self.config_dict = config_dict
        # get Gamry object (Garmry.com)
       
        # TODO: a busy gamrycom can lock up the server
        self.kill_GamryCom()
        self.GamryCOM = client.GetModule(['{BD962F0D-A990-4823-9CF5-284D1CDD9C6D}', 1, 0])
        #self.GamryCOM = client.GetModule(self.config_dict["path_to_gamrycom"])


        self.pstat = None

        if not 'dev_id' in self.config_dict:
            self.config_dict['dev_id'] = 0
        if not 'dev_family' in self.config_dict:
            self.config_dict['dev_family'] = 'Reference'
        
        self.Gamry_devid = self.config_dict['dev_id']
        self.Gamry_family = self.config_dict['dev_family']

        asyncio.gather(self.init_Gamry(self.Gamry_devid))

        self.temp = []
        self.buffer = dict()
        self.buffer_size = 0
        
        self.wsdataq = asyncio.Queue()
        self.dtaqsink = dummy_sink()
        self.dtaq = None
        
        self.area = 1.0
        self.output = ''
        self.notes = ''
        self.title = ''
  
        # empty the data before new one is collected
        self.data = collections.defaultdict(list)
        
        # for global IOloop
        self.IO_do_meas = False
        self.IO_meas_mode = None
        self.IO_sigramp = None

        myloop = asyncio.get_event_loop()
        #add meas IOloop
        myloop.create_task(self.IOloop())


        # for saving data localy
        self.FIFO_header = ''
        self.FIFO_name = ''
        self.FIFO_dir = ''
        self.datasubheader = ''


    ##########################################################################
    # This is main Gamry measurement loop which always needs to run
    # else if measurement is done in FastAPI calls we will get timeouts
    ##########################################################################
    async def IOloop(self):
        while True:
            await asyncio.sleep(0.5)
            if self.IO_do_meas:
                print(' ... Gramry got measurement request')
                await self.measure()
                # we need to close the connection else the Gamry is still is use 
                # which can cause trouble if the script ends witout closing the connection
                await self.close_connection()
                self.IO_do_meas = False
                print(' ... Gramry measurement is done')


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
                if self.Gamry_family == 'Interface':
                    self.pstat = client.CreateObject('GamryCOM.GamryPC6Pstat')                    
                    print(' ... Gamry, using Interface', self.pstat)
                elif self.Gamry_family == 'Reference':
                    self.pstat = client.CreateObject('GamryCOM.GamryPC5Pstat')            
                    print(' ... Gamry, using Reference', self.pstat)
                else: # old version before Framework 7.06
                    self.pstat = client.CreateObject('GamryCOM.GamryPstat')
                    print(' ... Gamry, using Farmework , 7.06?', self.pstat)

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
    async def measurement_setup(self, mode: Gamry_modes = None):
        await asyncio.sleep(0.001)
        if self.pstat:
                        
            if mode == Gamry_modes.CA:
                Dtaqmode = "GamryCOM.GamryDtaqChrono"
                Dtaqtype = self.GamryCOM.ChronoAmp
                self.datasubheader = "\t".join(['Time', 'Vf', 'Vu', 'Im', 'Q', 'Vsig', 'Ach', 'IERange', 'Overload', 'StopTest'])
            elif mode == Gamry_modes.CP:
                Dtaqmode = "GamryCOM.GamryDtaqChrono"
                Dtaqtype = self.GamryCOM.ChronoPot
                self.datasubheader = "\t".join(['Time', 'Vf', 'Vu', 'Im', 'Q', 'Vsig', 'Ach', 'IERange', 'Overload', 'StopTest'])
            elif mode == Gamry_modes.CV:
                Dtaqmode = "GamryCOM.GamryDtaqRcv"
                Dtaqtype = None
                self.datasubheader = "\t".join(['Time', 'Vf', 'Vu', 'Im', 'Vsig', 'Ach', 'IERange', 'Overload', 'StopTest', 'Cycle'])
            elif mode == Gamry_modes.LSV:
                Dtaqmode = "GamryCOM.GamryDtaqCpiv"
                Dtaqtype = None
                self.datasubheader = "\t".join(['Time', 'Vf', 'Vu', 'Im', 'Vsig', 'Ach', 'IERange', 'Overload', 'StopTest'])
            elif mode == Gamry_modes.EIS:
                # TODO change that
                print(' ... will be currently done in meas function')
            #     Dtaqmode = "GamryCOM.GamryDtaqEis"
            #     Dtaqtype = None
            # elif mode == Gamry_modes.OCV:
            else:
                return {"measurement_setup": f'mode_{mode}_not_supported'}


            try:
                self.dtaq=client.CreateObject(Dtaqmode)
                if Dtaqtype:
                    self.dtaq.Init(self.pstat,Dtaqtype)
                else:
                    self.dtaq.Init(self.pstat)
            except Exception as e:
                print(' ... Gamry Error:', gamry_error_decoder(e))


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
                

            # set IE range and mode
            # mode
            # autorange
            self.pstat.SetIERangeMode(True)
            # set to false and change range below
            # range (check manual for max range):
            #self.pstat.SetIERange(10)


            # push the signal ramp over
            self.pstat.SetSignal(self.IO_sigramp)
            # turn on the potentiostat output
            self.pstat.SetCell(self.GamryCOM.CellOn)
            
            
            # Use the following code to discover events:
            #client.ShowEvents(dtaqcpiv)
            connection = client.GetEvents(self.dtaq, self.dtaqsink)

            try:
                self.dtaq.Run(True)
            except Exception as e:
                raise gamry_error_decoder(e)

            # empty the data before new one is collected
            self.data = collections.defaultdict(list)
            
            
            client.PumpEvents(0.001)
            sink_status = self.dtaqsink.status
            counter = 0

            # TODO: open new file and write header
            datafile = LocalDataHandler()
            datafile.filename = f'{strftime("%Y%m%d_%H%M%S%z")}'
            await datafile.open_file()
            # TODO: can also just use write_data to write header
            # or header will automatically added in filehandler??
            datafile.fileheader = '%testheader'
            await datafile.write_header()
            await datafile.write_data('%Column_headings='+self.datasubheader)
            
            

            while sink_status != "done":
            #while sink_status == "measuring":
                # need some await points
                await asyncio.sleep(0.001)
                client.PumpEvents(0.001)
                # this is a temp data which gets the data point by point
                # write this to a file so we don't loose any data
                while counter < len(self.dtaqsink.acquired_points):
                    # need some await points
                    await asyncio.sleep(0.001)
                    tmp_datapoints = self.dtaqsink.acquired_points[counter]
                    #print(tmp_datapoints)
                    #print(counter)
                    if self.wsdataq.full():
                        _ = await self.wsdataq.get()
                        self.wsdataq.task_done()
                    await self.wsdataq.put(tmp_datapoints)
                    # TODO: put new data in file
                    await datafile.write_data("\t".join([str(num) for num in tmp_datapoints]))
                    counter += 1
    
                # this copies the complete chunk of data again and again
                # what we are going to do with this?
                dtaqarr = self.dtaqsink.acquired_points
                self.data = dtaqarr

                sink_status = self.dtaqsink.status
                #print(sink_status)


            self.pstat.SetCell(self.GamryCOM.CellOff)

            # TODO: close file
            await datafile.close_file()
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
    #  LSV definition
    ##########################################################################
    async def technique_LSV(self, 
        Vinit: float, 
        Vfinal: float, 
        ScanRate: float, 
        SampleRate: float
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        await self.open_connection()
        if self.pstat and not self.IO_do_meas:
            # set parameters for IOloop meas
            self.IO_meas_mode = Gamry_modes.LSV
            await self.measurement_setup(self.IO_meas_mode)
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
            # signal the IOloop to start the measrurement
            self.IO_do_meas = True
        elif self.IO_do_meas:
            err_code = "meas already in progress"            
        else:
            err_code = "not initialized"
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Vinit": Vinit,
                "Vfinal": Vfinal,
                "ScanRate": ScanRate,
                "SampleRate": SampleRate,
            },
            "err_code": err_code,
            "eta": eta
        }


    ##########################################################################
    #  CA definition
    ##########################################################################
    async def technique_CA(self, 
        Vinit: float, 
        Tinit: float, 
        Vstep1: float, 
        Tstep1: float, 
        Vstep2: float, 
        Tstep2: float, 
        SampleRate: float
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        await self.open_connection()
        if self.pstat and not self.IO_do_meas:
            # set parameters for IOloop meas
            self.IO_meas_mode = Gamry_modes.CA
            await self.measurement_setup(self.IO_meas_mode)
            # setup the experiment specific signal ramp
            self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalDstep")

            try:
                self.IO_sigramp.Init(
                    self.pstat, Vinit, Tinit, Vstep1, Tstep1, Vstep2, Tstep2, SampleRate, self.GamryCOM.PstatMode
                )
                err_code = "0"
            except Exception as e:
                err_code = gamry_error_decoder(e)
                print(' ... Gamry Error:', err_code)

            eta = Tinit + Tstep1 + Tstep2 #+delay
            # signal the IOloop to start the measrurement
            self.IO_do_meas = True
        elif self.IO_do_meas:
            err_code = "meas already in progress"
        else:
            err_code = "not initialized"
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Vinit": Vinit,
                "Tinit": Tinit,
                "Vstep1": Vstep1,
                "Tstep1": Tstep1,
                "Vstep2": Vstep2,
                "Tstep2": Tstep2,
                "SampleRate": SampleRate
            },
            "err_code": err_code,
            "eta": eta
        }


    ##########################################################################
    #  CP definition
    ##########################################################################
    async def technique_CP(self, 
        Iinit: float, 
        Tinit: float, 
        Istep1: float, 
        Tstep1: float, 
        Istep2: float, 
        Tstep2: float, 
        SampleRate: float
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        await self.open_connection()
        if self.pstat and not self.IO_do_meas:
            # set parameters for IOloop meas
            self.IO_meas_mode = Gamry_modes.CP
            await self.measurement_setup(self.IO_meas_mode)
            # setup the experiment specific signal ramp
            self.IO_sigramp = client.CreateObject("GamryCOM.GamrySignalDstep")

            try:
                self.IO_sigramp.Init(
                    self.pstat, Iinit, Tinit, Istep1, Tstep1, Istep2, Tstep2, SampleRate, self.GamryCOM.GstatMode
                )
                err_code = "0"
            except Exception as e:
                err_code = gamry_error_decoder(e)
                print(' ... Gamry Error:', err_code)

            eta = Tinit + Tstep1 + Tstep2 #+delay
            # signal the IOloop to start the measrurement
            self.IO_do_meas = True
        elif self.IO_do_meas:
            err_code = "meas already in progress"
        else:
            err_code = "not initialized"
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "Iinit": Iinit,
                "Tinit": Tinit,
                "Istep1": Istep1,
                "Tstep1": Tstep1,
                "Istep2": Istep2,
                "Tstep2": Tstep2,
                "SampleRate": SampleRate
            },
            "err_code": err_code,
            "eta": eta
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
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        await self.open_connection()
        if self.pstat and not self.IO_do_meas:
            # set parameters for IOloop meas
            self.IO_meas_mode = Gamry_modes.CV
            await self.measurement_setup(self.IO_meas_mode)
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

            # signal the IOloop to start the measrurement
            self.IO_do_meas = True
        elif self.IO_do_meas:
            err_code = "meas already in progress"
        else:
            err_code = "not initialized"


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
            "eta": eta
        }


    ##########################################################################
    #  EIS definition
    ##########################################################################
    async def technique_EIS(self, 
        start_freq,
        end_freq, 
        points, 
        pot_offset=0
    ):
        # time expected for measurement to be completed
        eta = 0.0
        # open connection, will be closed after measurement in IOloop
        await self.open_connection()
        if self.pstat and not self.IO_do_meas:
            
            
#            for f in np.logspace(np.log10(start_freq), np.log10(end_freq), points):
            
            # set parameters for IOloop meas
            self.IO_meas_mode = Gamry_modes.EIS
            await self.measurement_setup(self.IO_meas_mode)
            self.IO_sigramp = None
#                self.IO_sigramp.Init(
#                )
            # starts the mesurement in the IOloop
            # will be reset in that loop once meas is done
            self.IO_do_meas = True
                

            # Zreal, Zimag, Zsig, Zphz, Zfreq = [], [], [], [], []
            # is_on = False
            # self.pstat.Open()
            # for f in np.logspace(np.log10(start_freq), np.log10(end_freq), points):
    
            #     self.dtaq = client.CreateObject("GamryCOM.GamryDtaqEis")
            #     self.dtaq.Init(self.pstat, f, 0.05, 0.5, 20)
            #     self.dtaq.SetCycleMin(100)
            #     self.dtaq.SetCycleMax(50000)
    
            #     if not is_on:
            #         self.pstat.SetCell(self.GamryCOM.CellOn)
            #         is_on = True
            #     self.dtaqsink = GamryDtaqEvents(self.dtaq, self.q)
    
            #     connection = client.GetEvents(self.dtaq, self.dtaqsink)
    
            #     try:
            #         self.dtaq.Run(True)
            #     except Exception as e:
            #         raise gamry_error_decoder(e)
            #     if f < 10:
            #         client.PumpEvents(10)
            #     if f > 1000:
            #         client.PumpEvents(0.1)
            #     if f < 1000:
            #         client.PumpEvents(1)
    
            #     Zreal.append(self.dtaqsink.dtaq.Zreal())
            #     Zimag.append(self.dtaqsink.dtaq.Zimag())
            #     Zsig.append(self.dtaqsink.dtaq.Zsig())
            #     Zphz.append(self.dtaqsink.dtaq.Zphz())
            #     Zfreq.append(self.dtaqsink.dtaq.Zfreq())
            #     print(self.dtaqsink.dtaq.Zfreq())
            #     del connection
            # self.pstat.SetCell(self.GamryCOM.CellOff)
            # self.pstat.Close()
            err_code = "0"
        elif self.IO_do_meas:
            err_code = "meas already in progress"
        else:
            err_code = "not initialized"
            
            
        return {
            "measurement_type": self.IO_meas_mode,
            "parameters": {
                "tart_freq": start_freq,
                "end_freq": end_freq,
                "points": points,
                "pot_offset": pot_offset,
            },
            "err_code": err_code
            ,
            "eta": eta
        }


    ##########################################################################
    #  OCV definition
    ##########################################################################
    # def technique_OCV(self):

