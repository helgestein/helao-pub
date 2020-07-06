
""" A device class for the Gamry USB potentiostat, used by a FastAPI server instance.

The 'gamry' device class simulates potentiostat measurement functions provided by the
'GamryCOM' 'comtypes' Win32 module. The simulation class does not depend on 'comtypes'. 
Class methods are specific to Gamry devices. Device configuration is read from 
config/config.py. 
"""

# import comtypes
# import comtypes.client as client
import pickle
import os
import collections
import numpy as np
import sys
from numba import jit
import time
import asyncio
import aiofiles


if __package__:
    # can import directly in package mode
    print("importing config vars from package path")
else:
    # interactive kernel mode requires path manipulation
    cwd = os.getcwd()
    pwd = os.path.dirname(cwd)
    if os.path.basename(pwd) == "helao-dev":
        sys.path.insert(0, pwd)
    if pwd in sys.path or os.path.basename(cwd) == "helao-dev":
        print("importing config vars from sys.path")
    else:
        raise ModuleNotFoundError(
            "unable to find config vars, current working directory is {}".format(cwd)
        )

from config.config import *

setupd = GAMRY_SETUPD


# potential signal generator
def egen(vi, v0, v1, vf, vrate, ncycles, daq):
    segi0 = lambda t: vi + t * vrate if vi < v0 else vi - t * vrate
    seg01 = lambda t: v0 + t * vrate if v0 < v1 else v0 - t * vrate
    seg10 = lambda t: v1 + t * vrate if v1 < v0 else v1 - t * vrate
    seg1f = lambda t: v1 + t * vrate if v1 < vf else v1 - t * vrate

    total = (
        np.abs(v0 - vi) + (2 * ncycles - 1) * np.abs(v1 - v0) + np.abs(vf - v1)
    ) / (vrate)
    pps = vrate / daq
    total_pts = np.int(total * pps)
    tspace = np.linspace(0, total, total_pts)
    vlist = []
    for t in tspace:
        if t < np.abs(v0 - vi) / vrate:
            vlist.append(segi0(t))
        elif t < (np.abs(v0 - vi) + (2 * (ncycles - 1)) * np.abs(v1 - v0)) / vrate:
            subt = t - np.abs(v0 - vi) / vrate
            while subt > 2 * np.abs(v1 - v0) / vrate:
                subt -= 2 * np.abs(v1 - v0) / vrate
            if subt < np.abs(v1 - v0) / vrate:
                vlist.append(seg01(subt))
            else:
                subt -= np.abs(v1 - v0) / vrate
                vlist.append(seg10(subt))
        elif t < (np.abs(v0 - vi) + (2 * ncycles - 1) * np.abs(v1 - v0)) / vrate:
            subt = t - np.abs(v0 - vi) / vrate
            while subt > 2 * np.abs(v1 - v0) / vrate:
                subt -= 2 * np.abs(v1 - v0) / vrate
            vlist.append(seg01(subt))
        else:
            subt = t - (np.abs(v0 - vi) + (2 * ncycles - 1) * np.abs(v1 - v0)) / vrate
            vlist.append(seg1f(subt))
    vspace = np.array(vlist)
    return (tspace, vspace)


# CV simulator
def cvsim(vard, DM):
    ts, eta = egen(
        vard["etai"],
        vard["eta0"],
        vard["eta1"],
        vard["etaf"],
        vard["v"],
        vard["cyc"],
        vard["daq"],
    )
    L = len(eta) - 1
    F = 96485  # [=] C/mol, Faraday's constant
    R = 8.3145  # [=] J/mol-K, ideal gas constant
    f = F / (
        R * vard["T"]
    )  # [=] 1/V, normalized Faraday's constant at room temperature
    tk = (
        (
            np.abs(vard["etai"] - vard["eta0"])
            + np.abs(vard["eta0"] - vard["eta1"])
            + np.abs(vard["eta1"] - vard["etaf"])
        )
        / vard["v"]
    )  # [=] s, characteristic exp. time (pg 790). In this case, total time of fwd and rev scans
    Dt = tk / L  # [=] s, delta time (Eqn B.1.10, pg 790)
    Dx = np.sqrt(vard["D"] * Dt / DM)  # [=] cm, delta x (Eqn B.1.13, pg 791)
    j = np.int(
        np.ceil(4.2 * L ** 0.5) + 5
    )  # number of boxes (pg 792-793). If L~200, j=65
    ktk = vard["kc"] * tk  # dimensionless kinetic parameter (Eqn B.3.7, pg 797)
    km = ktk / L  # normalized dimensionless kinetic parameter (see bottom of pg 797)
    Lambda = (
        vard["k0"] / (vard["D"] * f * vard["v"]) ** 0.5
    )  # dimensionless reversibility parameter (Eqn 6.4.4, pg. 236-239)
    if km > 0.1:
        print(f"kc * tk / L is {km}, which exceeds the upper limit of 0.1")

    k = np.arange(L)  # time index vector
    t = Dt * k  # time vector
    Enorm = eta * f  # normalized overpotential
    kf = vard["k0"] * np.exp(
        0 - vard["alpha"] * vard["n"] * Enorm
    )  # [=] cm/s, fwd rate constant (pg 799)
    kb = vard["k0"] * np.exp(
        (1 - vard["alpha"]) * vard["n"] * Enorm
    )  # [=] cm/s, rev rate constant (pg 799)
    vD = vard["D"]
    vn = vard["n"]

    @jit(nopython=True)
    def Rfirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn):

        for i1 in range(1, L):
            for i2 in range(2, np.int(j) - 1):
                O[i1 + 1, i2] = O[i1, i2] + DM * (
                    O[i1, i2 + 1] + O[i1, i2 - 1] - 2 * O[i1, i2]
                )
                R[i1 + 1, i2] = (
                    R[i1, i2]
                    + DM * (R[i1, i2 + 1] + R[i1, i2 - 1] - 2 * R[i1, i2])
                    - km * R[i1, i2]
                )

            # Update flux
            JO[i1 + 1] = (kf[i1 + 1] * O[i1 + 1, 2] - kb[i1 + 1] * R[i1 + 1, 2]) / (
                1 + Dx / vD * (kf[i1 + 1] + kb[i1 + 1])
            )

            # Update surface concentrations
            O[i1 + 1, 1] = O[i1 + 1, 2] - JO[i1 + 1] * (Dx / vD)
            R[i1 + 1, 1] = R[i1 + 1, 2] + JO[i1 + 1] * (Dx / vD) - km * R[i1 + 1, 1]

        # Calculate current density, Z, from flux of O
        Z = -vn * F * JO / 10  # [=] A/m^2 -> mA/cm^2, current density
        return Z

    @jit(nopython=True)
    def Ofirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn):

        for i1 in range(1, L):
            for i2 in range(2, np.int(j) - 1):
                R[i1 + 1, i2] = R[i1, i2] + DM * (
                    R[i1, i2 + 1] + R[i1, i2 - 1] - 2 * R[i1, i2]
                )
                O[i1 + 1, i2] = (
                    O[i1, i2]
                    + DM * (O[i1, i2 + 1] + O[i1, i2 - 1] - 2 * O[i1, i2])
                    - km * O[i1, i2]
                )

            # Update flux
            JO[i1 + 1] = (kf[i1 + 1] * O[i1 + 1, 2] - kb[i1 + 1] * R[i1 + 1, 2]) / (
                1 + Dx / vD * (kf[i1 + 1] + kb[i1 + 1])
            )

            # Update surface concentrations
            O[i1 + 1, 1] = O[i1 + 1, 2] - JO[i1 + 1] * (Dx / vD)
            R[i1 + 1, 1] = R[i1 + 1, 2] + JO[i1 + 1] * (Dx / vD) - km * R[i1 + 1, 1]

        # Calculate current density, Z, from flux of O
        Z = -vn * F * JO / 10  # [=] A/m^2 -> mA/cm^2, current density
        return Z

    if vard["etai"] > vard["eta0"]:
        O = vard["C"] * np.ones((L + 1, j))  # [=] mol/cm^3, concentration of O
        R = np.zeros((L + 1, j))  # [=] mol/cm^3, concentration of R
        JO = np.zeros((L + 1)).squeeze()  # [=] mol/cm^2-s, flux of O at the surface
        Z = Rfirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn)
    else:
        R = vard["C"] * np.ones((L + 1, j))  # [=] mol/cm^3, concentration of O
        O = np.zeros((L + 1, j))  # [=] mol/cm^3, concentration of R
        JO = np.zeros((L + 1)).squeeze()  # [=] mol/cm^2-s, flux of O at the surface
        Z = Ofirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn)

    return ts, eta, Z


def lssim(vard, DM):
    ts, eta = egen(
        vard["etai"],
        vard["etaf"],
        vard["etaf"],
        vard["etaf"],
        vard["v"],
        0.5,
        vard["daq"],
    )
    L = len(eta) - 1
    F = 96485  # [=] C/mol, Faraday's constant
    R = 8.3145  # [=] J/mol-K, ideal gas constant
    f = F / (
        R * vard["T"]
    )  # [=] 1/V, normalized Faraday's constant at room temperature
    tk = (np.abs(vard["etai"] - vard["etaf"])) / vard[
        "v"
    ]  # [=] s, characteristic exp. time (pg 790). In this case, total time of fwd and rev scans
    Dt = tk / L  # [=] s, delta time (Eqn B.1.10, pg 790)
    Dx = np.sqrt(vard["D"] * Dt / DM)  # [=] cm, delta x (Eqn B.1.13, pg 791)
    j = np.int(
        np.ceil(4.2 * L ** 0.5) + 5
    )  # number of boxes (pg 792-793). If L~200, j=65
    ktk = vard["kc"] * tk  # dimensionless kinetic parameter (Eqn B.3.7, pg 797)
    km = ktk / L  # normalized dimensionless kinetic parameter (see bottom of pg 797)
    Lambda = (
        vard["k0"] / (vard["D"] * f * vard["v"]) ** 0.5
    )  # dimensionless reversibility parameter (Eqn 6.4.4, pg. 236-239)
    if km > 0.1:
        print(f"kc * tk / L is {km}, which exceeds the upper limit of 0.1")

    k = np.arange(L)  # time index vector
    t = Dt * k  # time vector
    Enorm = eta * f  # normalized overpotential
    kf = vard["k0"] * np.exp(
        0 - vard["alpha"] * vard["n"] * Enorm
    )  # [=] cm/s, fwd rate constant (pg 799)
    kb = vard["k0"] * np.exp(
        (1 - vard["alpha"]) * vard["n"] * Enorm
    )  # [=] cm/s, rev rate constant (pg 799)
    vD = vard["D"]
    vn = vard["n"]

    @jit(nopython=True)
    def Rfirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn):

        for i1 in range(1, L):
            for i2 in range(2, np.int(j) - 1):
                O[i1 + 1, i2] = O[i1, i2] + DM * (
                    O[i1, i2 + 1] + O[i1, i2 - 1] - 2 * O[i1, i2]
                )
                R[i1 + 1, i2] = (
                    R[i1, i2]
                    + DM * (R[i1, i2 + 1] + R[i1, i2 - 1] - 2 * R[i1, i2])
                    - km * R[i1, i2]
                )

            # Update flux
            JO[i1 + 1] = (kf[i1 + 1] * O[i1 + 1, 2] - kb[i1 + 1] * R[i1 + 1, 2]) / (
                1 + Dx / vD * (kf[i1 + 1] + kb[i1 + 1])
            )

            # Update surface concentrations
            O[i1 + 1, 1] = O[i1 + 1, 2] - JO[i1 + 1] * (Dx / vD)
            R[i1 + 1, 1] = R[i1 + 1, 2] + JO[i1 + 1] * (Dx / vD) - km * R[i1 + 1, 1]

        # Calculate current density, Z, from flux of O
        Z = -vn * F * JO / 10  # [=] A/m^2 -> mA/cm^2, current density
        return Z

    @jit(nopython=True)
    def Ofirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn):

        for i1 in range(1, L):
            for i2 in range(2, np.int(j) - 1):
                R[i1 + 1, i2] = R[i1, i2] + DM * (
                    R[i1, i2 + 1] + R[i1, i2 - 1] - 2 * R[i1, i2]
                )
                O[i1 + 1, i2] = (
                    O[i1, i2]
                    + DM * (O[i1, i2 + 1] + O[i1, i2 - 1] - 2 * O[i1, i2])
                    - km * O[i1, i2]
                )

            # Update flux
            JO[i1 + 1] = (kf[i1 + 1] * O[i1 + 1, 2] - kb[i1 + 1] * R[i1 + 1, 2]) / (
                1 + Dx / vD * (kf[i1 + 1] + kb[i1 + 1])
            )

            # Update surface concentrations
            O[i1 + 1, 1] = O[i1 + 1, 2] - JO[i1 + 1] * (Dx / vD)
            R[i1 + 1, 1] = R[i1 + 1, 2] + JO[i1 + 1] * (Dx / vD) - km * R[i1 + 1, 1]

        # Calculate current density, Z, from flux of O
        Z = -vn * F * JO / 10  # [=] A/m^2 -> mA/cm^2, current density
        return Z

    if vard["etaf"] < vard["etai"]:
        O = vard["C"] * np.ones((L + 1, j))  # [=] mol/cm^3, concentration of O
        R = np.zeros((L + 1, j))  # [=] mol/cm^3, concentration of R
        JO = np.zeros((L + 1)).squeeze()  # [=] mol/cm^2-s, flux of O at the surface
        Z = Rfirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn)
    else:
        R = vard["C"] * np.ones((L + 1, j))  # [=] mol/cm^3, concentration of O
        O = np.zeros((L + 1, j))  # [=] mol/cm^3, concentration of R
        JO = np.zeros((L + 1)).squeeze()  # [=] mol/cm^2-s, flux of O at the surface
        Z = Ofirst(O, R, DM, km, JO, j, L, kf, kb, Dx, vD, vn)

    return ts, eta, Z


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
    "Handles transfer of dtaq events from instrument buffer."

    def __init__(self, meas_type):
        "Takes gamry dtaq object with .cook() method, stores points"
        self.dtaq = "simulate"
        self.acquired_points = []
        self.acquired_points_queue = asyncio.Queue() 
        self.status = "idle"
        self.start_time = time.time()
        self.stop_time = time.time()
        self.meas_type = meas_type

    def simulate(self, sigramp, SampleRate, ScanRate): #ASYNCABLE WITHIN THE WHILE LOOP
        # set_status_aquire_points needs async sleep to work properly 
        # test_async does not need async sleep to work properly 

        loop = asyncio.get_event_loop() # this line might need to be moved to main later
        # import asyncio (completed)
        # make the method async (completed)
        # initialize the loop with: loop = asyncio.get_event_loop() (completed)
        # set tasks: task1 = whatever we want to do with our queue (completed)
        # if there are multiple tasks gather them: final_task = asyncio.gather(task1, task2, task3) (completed)
        # complete tasks: loop.run_until_complete(final_task) (completed)
        # await data being added to the queue: await name_of_queueu.put(whatever we want to add)
        # might need to await async sleep

        if self.meas_type == "IGamryDtaqRcv":
            fullt, fullv, fullj = cvsim(sigramp, 0.45)
        else:
            fullt, fullv, fullj = lssim(sigramp, 0.45)
        self.start_time = time.time()
        self.stop_time = self.start_time + fullt[-1]

        task0 = self.clear_aiofile()
        loop.run_until_complete(task0)

        t0 = time.time()
        task1 = loop.create_task(self.set_status_aquire_points(fullt, fullv, fullj, SampleRate, ScanRate)) 
        task2 = loop.create_task(self.test_async(SampleRate, ScanRate))
        final_task = asyncio.gather(task1, task2) 
        loop.run_until_complete(final_task)
        dt = time.time() - t0
        print(dt)

        # self.acquired_points = [[t, v, 0.0, j] for t, v, j in zip(fullt, fullv, fullj)]
        self.status = "idle"

    async def test_async(self, SampleRate, ScanRate):
        processed = 0
        while processed < 20:
            #item = await self.acquired_points.get() #this will not work if there is another call to .get() which is emptying our acquire_points queue
            processed += 1
            print("here")
            print(SampleRate/ScanRate)
            await asyncio.sleep(SampleRate/ScanRate)

    # I AM NOT YET SURE IF THIS WILL BE HELPFUL TO AWAIT
    async def get_value_for_aquire_points(self, fullt, fullv, fullj):
        return [ 
            [t, v, 0.0, j]
            for t, v, j in zip(fullt, fullv, fullj)
            if t < (time.time() - self.start_time)
        ]

    async def clear_aiofile(self): # clears file
        data = ""
        async with aiofiles.open('acquired_points', 'w') as f:
            await f.write(data)

    async def write_to_aiofile(self, data): # acquire_points queue is converted to a string to be written
        # data = await data.get()
        self.acquired_points.append(data)
        data = ''.join(str(e) for e in data)
        data = data.replace(']', ']\n')
        async with aiofiles.open('acquired_points', 'a') as f:
            await f.write(data)

    async def set_status_aquire_points(self, fullt, fullv, fullj, SampleRate, ScanRate): # THIS CODE USE TO BE IN THE SIMULATE METHOD
        
        # ----OLD CODE----

        # counter = 0
        # while time.time() < self.stop_time:
        #     print(fullt[counter])
        #     print("there")
        #     self.status = "measuring"
        #     self.acquired_points = await self.get_value_for_aquire_points(fullt, fullv, fullj) 
        #     await self.write_to_aiofile([ # only need to get the last t v j in the for loop with each while iteration
        #         [t, v, 0.0, j]
        #         for t, v, j in zip(fullt, fullv, fullj)
        #         if t < (time.time() - self.start_time)
        #     ])
        #     # await self.acquired_points.put([ 
        #     #     [t, v, 0.0, j]
        #     #     for t, v, j in zip(fullt, fullv, fullj)
        #     #     if t < (time.time() - self.start_time)
        #     # ])
        #     counter += 1
        #     await asyncio.sleep(.5)

        # ----OLD CODE----

        fullt_copy = np.copy(fullt)
        fullv_copy = np.copy(fullv)
        fullj_copy = np.copy(fullj)
        while time.time() < self.stop_time: 
            print("there")
            self.status = "measuring" 
            for t, v, j in zip(fullt_copy, fullv_copy, fullj_copy):
                if t < (time.time() - self.start_time):
                    await self.write_to_aiofile([[t, v, 0.0, j]])
                    await self.acquired_points_queue.put([[t, v, 0.0, j]])
                    fullt_copy = np.delete(fullt_copy, [0]) # by deleting the elements we do not get repeat data but fullt fullv fullj cannot be used after
                    fullv_copy = np.delete(fullv_copy, [0])
                    fullj_copy = np.delete(fullj_copy, [0])
            if(len(fullt_copy) == 1):
                await self.write_to_aiofile([[fullt_copy[0], fullv_copy[0], 0.0, fullj_copy[0]]])
                await self.acquired_points_queue.put([[fullt_copy[0], fullv_copy[0], 0.0, fullj_copy[0]]])
                fullt_copy = np.delete(fullt_copy, [0]) 
                fullv_copy = np.delete(fullv_copy, [0])
                fullj_copy = np.delete(fullj_copy, [0])
            await asyncio.sleep(SampleRate/ScanRate)


class gamry:
    def __init__(self): #MIGHT NEED TO INITIALIZE self.data AS AN ASYNC QUEUE
        self.pstat = {"connected": 0}
        self.temp = []

    def open_connection(self, force_err=False):
        # seet connection status to open
        if not force_err:
            self.pstat["connected"] = 1
            return {"potentiostat_connection": "connected"}
        else:
            return {"potentiostat_connection": "error"}

    def close_connection(self, force_err=False):
        # set connection status to closed
        if not force_err:
            self.pstat["connected"] = 0
            return {"potentiostat_connection": "closed"}
        else:
            return {"potentiostat_connection": "error"}

    def measurement_setup(self, gsetup="sweep"):
        # sets dtaq mode
        self.open_connection()
        if gsetup == "sweep":
            g = "GamryCOM.GamryDtaqCpiv"
        if gsetup == "cv":
            g = "IGamryDtaqRcv"
        self.dtaqsink = GamryDtaqEvents(g)

    def measure(self, sigramp, SampleRate, ScanRate): #ASYNCABLE 
        # starts measurement, init signal ramp and acquire data; loops until sink_status == "done"
        print("Opening Connection")
        ret = self.open_connection()
        print(ret)
        # push the signal ramp over
        print("Pushing")
        # self.measurement_setup()
        self.data = collections.defaultdict(list)
        self.dtaqsink.simulate(sigramp, SampleRate, ScanRate)
        # sink_status = self.dtaqsink.status
        # while sink_status != "idle":
        #     sink_status = self.dtaqsink.status
        #     dtaqarr = self.dtaqsink.acquired_points
        #     self.data = dtaqarr # keep updating self.data
        self.data = self.dtaqsink.acquired_points
        self.close_connection()

    def status(self):
        try:
            return self.dtaqsink.status
        except:
            return "other"

    def dump_data(self):
        pickle.dump(
            self.data, open(os.path.join(setupd["temp_dump"], self.instance_id))
        )

    def potential_ramp(
        self, Vinit: float, Vfinal: float, ScanRate: float, SampleRate: float
    ):
        # setup the experiment specific signal ramp
        sigramp = {
            "C": 1.0,  # initial conc of redox species
            "D": 1e-5,  # redox diffusion coefficient
            "etai": Vinit,  # initial overpotential
            "etaf": Vfinal,  # final overpotential
            "v": ScanRate,  # sweep rate
            "n": 1.0,  # number of electrons transferred
            "alpha": 0.5,  # charge-transfer coefficient
            "k0": 1e-2,  # electrochemical rate constant
            "kc": 1e-3,  # chemical rate constant
            "T": 298.15,  # temperature
            "cyc": 1,
            "daq": SampleRate,
        }
        # measure ... this will do the setup as well
        self.measurement_setup("sweep")
        self.measure(sigramp, SampleRate, ScanRate)
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

    def potential_cycle(
        self,
        Vinit: float,
        Vfinal: float,
        Vapex1: float,
        Vapex2: float,
        ScanRate: float,
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
        sigramp = {
            "C": 1.0,  # initial conc of redox species
            "D": 1e-5,  # redox diffusion coefficient
            "etai": Vinit,  # initial overpotential
            "eta0": Vapex1,
            "eta1": Vapex2,
            "etaf": Vfinal,  # final overpotential
            "v": ScanRate,  # sweep rate
            "n": 1.0,  # number of electrons transferred
            "alpha": 0.5,  # charge-transfer coefficient
            "k0": 1e-2,  # electrochemical rate constant
            "kc": 1e-3,  # chemical rate constant
            "T": 298.15,  # temperature
            "cyc": Cycles,  # number of cycles
            "daq": SampleRate,
        }
        # measure ... this will do the setup as well
        self.measurement_setup(gsetup="cv")
        self.measure(sigramp, SampleRate, ScanRate)
        return {
            "measurement_type": "potential_ramp",
            "parameters": {
                "Vinit": Vinit,
                "Vapex1": Vapex1,
                "Vapex2": Vapex2,
                "Vfinal": Vfinal,
                "ScanRate": ScanRate,
                "SampleRate": SampleRate,
                "Cycles": Cycles,
            },
            "data": self.data,
        }


g = gamry()
g.potential_ramp(-1,1,0.2,0.05)

g.potential_cycle(-1, -1, 1, 1, 0.2, 1, 0.05, "galvanostatic")

egen(0, 1.0, 1.0, 1.0, 0.2, 0.5, 0.05)
