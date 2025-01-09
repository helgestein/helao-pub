""" A device class for the Gamry USB potentiostat, used by a FastAPI server instance.

The 'gamry' device class exposes potentiostat measurement functions provided by the
GamryCOM comtypes Win32 module. Class methods are specific to Gamry devices. Device 
configuration is read from config/config.py. 
"""

import comtypes
import comtypes.client as client
import pickle
import os
import collections
import numpy as np
import sys
import asyncio
import aiofiles
import time

# =============================================================================
# # for testing driver only:
# config_dict = {
#     "path_to_gamrycom": r"C:\Program Files (x86)\Gamry Instruments\Framework\GamryCOM.exe",
#     "temp_dump": r"C:\Users\hte\Documents\lab_automation\temp",
# }
# =============================================================================


# definition of error handling things from gamry
class GamryCOMError(Exception):
    pass


def gamry_error_decoder(e):
    if isinstance(e, comtypes.COMError):
        hresult = 2 ** 32 + e.args[0]
        if hresult & 0x20000000:
            return GamryCOMError(
                "0x{0:08x}: {1}".format(2 ** 32 + e.args[0], e.args[1])
            )
    return e


class GamryDtaqEvents(object):
    def __init__(self, dtaq, q):
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
        # TODO:  indicate completion to enclosing code?


class gamry:
    # since the gamry connection uses one class and it can be switched on or off with handoff and everythong
    # I decided to put the gamry in a class ... this puts the logic into this class and not like in the motion server
    # where the logic is spread across the functions. TODO: Decide which way to implement this and streamline everywhere
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.GamryCOM = client.GetModule(self.config_dict["path_to_gamrycom"])

        self.devices = client.CreateObject("GamryCOM.GamryDeviceList")
        # print(devices.EnumSections())

        self.pstat = client.CreateObject("GamryCOM.GamryPC6Pstat")

        # print(devices.EnumSections())
        try:
            self.pstat.Init(self.devices.EnumSections()[0])  # grab first pstat
        except IndexError:
            print("No potentiostat is connected! Have you turned it on?")
        self.temp = []
        self.buffer = dict()
        self.buffer_size = 0
        self.q = asyncio.Queue()

    def open_connection(self):
        # this just tries to open a connection with try/catch
        try:
            self.pstat.Open()
            return {"potentiostat_connection": "connected"}
        except:
            return {"potentiostat_connection": "error"}

    def close_connection(self):
        # this just tries to close a connection with try/catch
        try:
            self.pstat.Close()
            return {"potentiostat_connection": "closed"}
        except:
            return {"potentiostat_connection": "error"}

    def measurement_setup(self, gsetup="sweep"):
        self.open_connection()
        if gsetup == "sweep":
            g = "GamryCOM.GamryDtaqCpiv"
        if gsetup == "cv":
            g = "GamryCOM.GamryDtaqRcv"
        if gsetup == "CA" or gsetup == "CP":
            g = "GamryCOM.GamryDtaqChrono"
        self.dtaqcpiv = client.CreateObject(g)
        if gsetup == "sweep" or gsetup == "cv":
            self.dtaqcpiv.Init(self.pstat)
        if gsetup == "CA":
            self.dtaqcpiv.Init(self.pstat, self.GamryCOM.ChronoAmp)
        if gsetup == "CP":
            self.dtaqcpiv.Init(self.pstat, self.GamryCOM.ChronoPot)
        self.dtaqsink = GamryDtaqEvents(self.dtaqcpiv, self.q)

        
    async def asyncTest(self): # ADDED to test async (not needed)
        while True:
            print("here")
            await asyncio.sleep(.25)

    # def get_buffer(self):
    #     for key in self.buffer:
    #         print("key:" + str(key))
    #         print("value:" + str(self.buffer.get(key)))
    #     return self.buffer

    # def get_buffer_from_index(self, i):
    #     for index in range(len(list(self.buffer)) - i):
    #         print("key:" + str(list(self.buffer.keys())[i + index]))
    #         print("value:" + str(self.buffer.get(list(self.buffer.keys())[i + index])))

    async def measure(self, sigramp, gsetup=None): 
        print("Opening Connection")
        ret = self.open_connection()
        #self.pstat.SetIERange(10)
        self.pstat.SetIERangeMode(1)
        if gsetup=='CP':
            self.pstat.SetCtrlMode(0)
        else:
            self.pstat.SetCtrlMode(1)
        print(self.pstat.CtrlMode())
        print(self.pstat.IERange())
        print(ret)
        # push the signal ramp over
        print("Pushing")
        self.pstat.SetSignal(sigramp)

        self.pstat.SetCell(self.GamryCOM.CellOn)
        if gsetup==None:
            self.measurement_setup()
        else:
            self.measurement_setup(gsetup) #TODO: good to add gsetup?
        self.connection = client.GetEvents(self.dtaqcpiv, self.dtaqsink)
        try:
            self.dtaqcpiv.Run(True)
        except Exception as e:
            raise gamry_error_decoder(e)
        self.data = collections.defaultdict(list)
        client.PumpEvents(0.001)
        sink_status = self.dtaqsink.status
        # f = open("data.txt", "w")
        # f.write("")
        # f.close()
        counter = 0
        # f = open("data.txt", "a")

        async with aiofiles.open('data', 'w') as f:
            await f.write("")

        while sink_status != "done":
            client.PumpEvents(0.001)
            while counter < len(self.dtaqsink.acquired_points):
                await self.q.put(self.dtaqsink.acquired_points[counter])
                async with aiofiles.open('data', 'a') as f:
                    await f.write(str(self.dtaqsink.acquired_points[counter])+"\n")
                counter += 1
# =============================================================================
#                 print(counter)
#                 await asyncio.sleep(.25) #CHANGE SLEEP TIME
# =============================================================================
            sink_status = self.dtaqsink.status
            dtaqarr = self.dtaqsink.acquired_points
            self.data = dtaqarr
            # self.buffer_size = self.dtaqsink.buffer_size
            # if self.buffer_size > 5_000_000_000: #5gb #keep the memory size of the buffer under a certain amount
            #     while self.buffer_size > 5_000_000_000:
            #         self.buffer_size -= sys.getsizeof(self.buffer[list(self.buffer.keys())[0]])
        f.close()
        self.pstat.SetCell(self.GamryCOM.CellOff)
        self.close_connection()

    def status(self):
        try:
            return self.dtaqsink.status
        except:
            return "other"

    def dump_data(self):
        pickle.dump(
            self.data, open(os.path.join(self.config_dict["temp_dump"], self.instance_id))
        )

    def signal_array(self, Cycles: int, SampleRate: float, arr):
        arr = np.array(arr).tolist()
        # setup the experiment specific signal ramp
        if len(arr) > 262143:
            raise tooLongMeasurementError

        sigramp = client.CreateObject("GamryCOM.GamrySignalArray")
        sigramp.Init(
            self.pstat, Cycles, SampleRate, len(arr), arr, self.GamryCOM.PstatMode
        )
        # measure ... this will do the setup as well
        self.measure(sigramp)
        return {
            "measurement_type": "potential_ramp",
            "parameters": {
                "Vinit": Cycles,
                "Vfinal": SampleRate,
                "SampleRate": SampleRate,
                "Profile": arr,
            },
            "data": np.array(self.data).tolist(),
        }

    async def potential_ramp(
        self, Vinit: float, Vfinal: float, ScanRate: float, SampleRate: float
    ):
        # setup the experiment specific signal ramp
        sigramp = client.CreateObject("GamryCOM.GamrySignalRamp")
        sigramp.Init(
            self.pstat, Vinit, Vfinal, ScanRate, SampleRate, self.GamryCOM.PstatMode
        )
        # measure ... this will do the setup as well
        await self.measure(sigramp)
        return {
            "measurement_type": "potential_ramp",
            "parameters": {
                "Vinit": Vinit,
                "Vfinal": Vfinal,
                "ScanRate": ScanRate,
                "SampleRate": SampleRate,
            },
            "data": self.data,
        }

#driver for CA tests
    async def chrono_amp(
        self, Vinit: float, Tinit: float, Vstep1: float, Tstep1: float, Vstep2: float, Tstep2: float, SampleRate: float
    ):
        # setup the experiment specific signal ramp
        sigramp = client.CreateObject("GamryCOM.GamrySignalDstep")
        sigramp.Init(
            self.pstat, Vinit, Tinit, Vstep1, Tstep1, Vstep2, Tstep2, SampleRate, self.GamryCOM.PstatMode
        )
        # measure ... this will do the setup as well
        gsetup='CA'
        await self.measure(sigramp, gsetup)
        return {
            "measurement_type": "chrono_amp",
            "parameters": {
                "Vinit": Vinit,
                "Tinit": Tinit,
                "Vstep1": Vstep1,
                "Tstep1": Tstep1,
                "Vstep2": Vstep2,
                "Tstep2": Tstep2,
                "SampleRate": SampleRate
            },
            "data": self.data,
        }

#driver for CP tests
    async def chrono_pot(
        self, Iinit: float, Tinit: float, Istep1: float, Tstep1: float, Istep2: float, Tstep2: float, SampleRate: float
    ):
        # setup the experiment specific signal ramp
        sigramp = client.CreateObject("GamryCOM.GamrySignalDstep")
        sigramp.Init(
            self.pstat, Iinit, Tinit, Istep1, Tstep1, Istep2, Tstep2, SampleRate, self.GamryCOM.GstatMode
        )
        # measure ... this will do the setup as well
        gsetup='CP'
        await self.measure(sigramp, gsetup)
        return {
            "measurement_type": "chrono_pot",
            "parameters": {
                "Iinit": Iinit,
                "Tinit": Tinit,
                "Istep1": Istep1,
                "Tstep1": Tstep1,
                "Istep2": Istep2,
                "Tstep2": Tstep2,
                "SampleRate": SampleRate
            },
            "data": self.data,
        }

    async def potential_cycle(
        self,
        Vinit: float,
        Vfinal: float,
        Vapex1: float,
        Vapex2: float,
        ScanInit: float,
        ScanApex: float,
        ScanFinal: float,
        HoldTime0: float,
        HoldTime1: float,
        HoldTime2: float,
        Cycles: int,
        SampleRate: float,
        control_mode: str,
    ):
        if control_mode == "galvanostatic":
            # do something
            pass
        else:
            # do something else
            pass
        # setup the experiment specific signal ramp
        sigramp = client.CreateObject("GamryCOM.GamrySignalRupdn")
        sigramp.Init(
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
        # measure ... this will do the setup as well
        await self.measure(sigramp)
        return {
            "measurement_type": "potential_ramp",
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
            "data": self.data,
        }

    def eis(self, start_freq, end_freq, points, pot_offset=0):
        Zreal, Zimag, Zsig, Zphz, Zfreq = [], [], [], [], []
        is_on = False
        self.pstat.Open()
        for f in np.logspace(np.log10(start_freq), np.log10(end_freq), points):

            self.dtaqcpiv = client.CreateObject("GamryCOM.GamryDtaqEis")
            self.dtaqcpiv.Init(self.pstat, f, 0.05, 0.5, 20)
            self.dtaqcpiv.SetCycleMin(100)
            self.dtaqcpiv.SetCycleMax(50000)

            if not is_on:
                self.pstat.SetCell(self.GamryCOM.CellOn)
                is_on = True
            self.dtaqsink = GamryDtaqEvents(self.dtaqcpiv, self.q)

            connection = client.GetEvents(self.dtaqcpiv, self.dtaqsink)

            try:
                self.dtaqcpiv.Run(True)
            except Exception as e:
                raise gamry_error_decoder(e)
            if f < 10:
                client.PumpEvents(10)
            if f > 1000:
                client.PumpEvents(0.1)
            if f < 1000:
                client.PumpEvents(1)

            Zreal.append(self.dtaqsink.dtaq.Zreal())
            Zimag.append(self.dtaqsink.dtaq.Zimag())
            Zsig.append(self.dtaqsink.dtaq.Zsig())
            Zphz.append(self.dtaqsink.dtaq.Zphz())
            Zfreq.append(self.dtaqsink.dtaq.Zfreq())
            print(self.dtaqsink.dtaq.Zfreq())
            del connection
        self.pstat.SetCell(self.GamryCOM.CellOff)
        self.pstat.Close()
        return {
            "measurement_type": "eis",
            "parameters": {
                "tart_freq": start_freq,
                "end_freq": end_freq,
                "points": points,
                "pot_offset": pot_offset,
            },
            "data": [Zreal, Zimag, Zfreq],
        }

    def ocv(self, start_freq, end_freq, points, pot_offset=0):
        Zreal, Zimag, Zsig, Zphz, Zfreq = [], [], [], [], []
        is_on = False
        self.pstat.Open()
        if offset != 0:
            self.pstat.SetVchOffsetEnable(True)
            if self.pstat.VchOffsetEnable():
                self.poti.pstat.SetVchOffset(pot_offset)
            else:
                print("Have offset but could not enable")
        for f in np.logspace(np.log10(start_freq), np.log10(end_freq), points):

            self.dtaqcpiv = client.CreateObject("GamryCOM.GamryDtaqEis")
            self.dtaqcpiv.Init(self.pstat, f, 0.1, 0.5, 20)
            self.dtaqcpiv.SetCycleMin(100)
            self.dtaqcpiv.SetCycleMax(50000)

            if not is_on:
                self.pstat.SetCell(self.GamryCOM.CellOn)
                is_on = True
            self.dtaqsink = GamryDtaqEvents(self.dtaqcpiv, self.q)

            connection = client.GetEvents(self.dtaqcpiv, self.dtaqsink)

            try:
                self.dtaqcpiv.Run(True)
            except Exception as e:
                raise gamry_error_decoder(e)
            if f < 10:
                client.PumpEvents(10)
            else:
                client.PumpEvents(1)

            Zreal.append(self.dtaqsink.dtaq.Zreal())
            Zimag.append(self.dtaqsink.dtaq.Zimag())
            Zsig.append(self.dtaqsink.dtaq.Zsig())
            Zphz.append(self.dtaqsink.dtaq.Zphz())
            Zfreq.append(self.dtaqsink.dtaq.Zfreq())
            print(self.dtaqsink.dtaq.Zfreq())
            del connection
        self.pstat.SetCell(self.GamryCOM.CellOff)
        self.pstat.Close()
        return {
            "measurement_type": "eis",
            "parameters": {
                "tart_freq": start_freq,
                "end_freq": end_freq,
                "points": points,
                "pot_offset": pot_offset,
            },
            "data": [Zreal, Zimag, Zfreq],
        }


# =============================================================================
# if __name__ == "__main__":
# =============================================================================

# potential ramp exaple:
# g = gamry(config_dict)
# loop = asyncio.get_event_loop() 
# task1 = loop.create_task(g.potential_ramp(-0.2,-0.6,0.1,1))
#task2 = loop.create_task(g.asyncTest())
#final_task = asyncio.gather(task1, task2) 
# final_task = asyncio.gather(task1)
# result = loop.run_until_complete(final_task)
# print(result)
# print('time: ', [result[0]['data'][v][0] for v in range(len(result[0]['data']))])
# print('potential: ',[result[0]['data'][v][1] for v in range(len(result[0]['data']))])
# print([result[0]['data'][v][2] for v in range(len(result[0]['data']))])
# print('current: ', [result[0]['data'][v][3] for v in range(len(result[0]['data']))])


# CA exaple:
# =============================================================================
# g = gamry()
# loop = asyncio.get_event_loop() 
# task1 = loop.create_task(g.chrono_amp(-1.8,1,-1.8,3, -1.8,3,1 ))
# #task2 = loop.create_task(g.asyncTest())
# #final_task = asyncio.gather(task1, task2) 
# final_task = asyncio.gather(task1)
# result = loop.run_until_complete(final_task)
# print(result)
# print('time: ', [result[0]['data'][v][0] for v in range(len(result[0]['data']))])
# print('potential: ',[result[0]['data'][v][1] for v in range(len(result[0]['data']))])
# print([result[0]['data'][v][2] for v in range(len(result[0]['data']))])
# print('current: ', [result[0]['data'][v][3] for v in range(len(result[0]['data']))])
# 
# =============================================================================

# =============================================================================
# # CP exaple:
# g = gamry()
# loop = asyncio.get_event_loop() 
# task1 = loop.create_task(g.chrono_pot(-0.00006,1,-0.00006,3, -0.00006,3,1 ))
# #task2 = loop.create_task(g.asyncTest())
# #final_task = asyncio.gather(task1, task2) 
# final_task = asyncio.gather(task1)
# result = loop.run_until_complete(final_task)
# print(result)
# print('time: ', [result[0]['data'][v][0] for v in range(len(result[0]['data']))])
# print('potential: ',[result[0]['data'][v][1] for v in range(len(result[0]['data']))])
# print([result[0]['data'][v][2] for v in range(len(result[0]['data']))])
# print('current: ', [result[0]['data'][v][3] for v in range(len(result[0]['data']))])
# =============================================================================
# =============================================================================
# print('t', result[1])
# print('t', result[2])
# print('t', result[3])
# =============================================================================





#mdata = g.potential_ramp(-1,1,0.4,0.05)
#marray = np.array(mdata['data'])

"""
import numpy as np
poti = gamry()
ret = poti.signal_array(1,0.0001,np.sin(np.linspace(0,np.pi*5,1000)).tolist())
plt.plot(np.array(ret['data'])[:,1],np.array(ret['data'])[:,3])
plt.show()
#crazyspike
arr = [0 if not 400<i<500 else 1 for i in range(1000)]
ret_75 = poti.signal_array(1,7.5*10**-6,arr)
ret_5 = poti.signal_array(1,5*10**-6,arr)
ret_2 = poti.signal_array(1,2*10**-6,arr)
ret_18 = poti.signal_array(1,1.8*10**-6,arr)
ret_17 = poti.signal_array(1,1.7*10**-6,arr)

plt.plot(np.array(ret_75['data'])[:,3],'o',label='7.5mus',alpha=0.2)
plt.plot(np.array(ret_5['data'])[:,3],'o',label='5mus',alpha=0.2)
plt.plot(np.array(ret_2['data'])[:,3],'o',label='2mus',alpha=0.2)
plt.plot(np.array(ret_18['data'])[:,3],'o',label='1.8mus',alpha=0.2)
plt.plot(np.array(ret_17['data'])[:,3],'o',label='1.7mus',alpha=0.2)

plt.legend()
plt.xlabel('step')
plt.ylabel('Current [A]')
plt.show()

"""
