import os
import sys
import clr
from time import sleep
import json
import asyncio

class Autolab:
    def __init__(self,autolab_conf):
        #init a Queue for the visualizer
        self.q = asyncio.Queue(loop=asyncio.get_event_loop())
        self.basep = autolab_conf["basep"]
        sys.path.append(self.basep)
        self.procp = autolab_conf["procp"]
        self.hwsetupf = autolab_conf["hwsetupf"]
        self.micsetupf = autolab_conf["micsetupf"]
        self.proceduresd = autolab_conf["proceuduresd"]
        clr.AddReference("EcoChemie.Autolab.Sdk")
        try:
            from EcoChemie.Autolab import Sdk as sdk
        except:
            from EcoChemie.Autolab import Sdk as sdk
        self.inst = sdk.Instrument()
        self.connect()
        self.proc = None

    def connect(self):
        self.inst.HardwareSetupFile = self.hwsetupf
        self.inst.AutolabConnection.EmbeddedExeFileToStart = self.micsetupf
        self.inst.Connect()

    def disconnect(self):
        try:
            self.proc.Abort()
        except:
            print('Procedure abort failed. Disconnecting anyhow.')
        self.inst.Disconnect()

    def ismeasuring(self):
        try:
            return self.proc.IsMeasuring
        except:
            # likely no procedure set
            return False

    def potential(self):
        # just gives the currently applied raw potential vs. ref
        return float(self.inst.Ei.get_Potential())

    def current(self):
        # just gives the currently applied raw potential
        return float(self.inst.Ei.Current)

    def setCurrentRange(self,range):
        if range == "10A":
            self.inst.Ei.CurrentRange = 1
        elif range == "1A":
            self.inst.Ei.CurrentRange = 0
        elif range == "100A":
            self.inst.Ei.CurrentRange = -1
        elif range == "10mA":
            self.inst.Ei.CurrentRange = -2
        elif range == "1mA":
            self.inst.Ei.CurrentRange = -3
        elif range == "100uA":
            self.inst.Ei.CurrentRange = -4
        elif range == "10uA":
            self.inst.Ei.CurrentRange = -5
        elif range == "1uA":
            self.inst.Ei.CurrentRange = -6
        elif range == "100nA":
            self.inst.Ei.CurrentRange = -7
        elif range == "10nA":
            self.inst.Ei.CurrentRange = -8

    def setStability(self,stability):
        if stability=="high":
            self.inst.Ei.Bandwith = 2
        else:
            self.inst.Ei.Bandwith = 1


    def appliedPotential(self):
        return float(self.inst.Ei.PotentialApplied)

    def abort(self):
        try:
            self.proc.Abort()
        except:
            print('Failed to abort. Likely nothing to abort.')

    def loadProcedure(self, name):
        self.proc = self.inst.LoadProcedure(self.proceduresd[name])

    def setSetpoints(self, setpoints):
        for comm, params in setpoints.items():
            if  params == None:
                print("comm:{}, params: {}".format(comm, params))
                continue
            #print("comm:{}, params: {}".format(comm, params))
            for param, value in params.items():
                #print("params:{}, values: {}".format(param, value))
                self.proc.Commands[comm].CommandParameters[param].Value = value
                #print(f"value is : {self.proc.Commands[comm].CommandParameters[param].Value}")

    async def whileMeasuring(self, type_):
        import time
        from copy import copy
        then = copy(time.monotonic())
        while self.proc.IsMeasuring:
            freq = 100  # not to cause an exception
            sleep(0.5)
            now = copy(time.monotonic())
            t = now-then
            if type_ == 'impedance':
                try:
                    freq = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().Frequency
                    hreal = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().H_Real
                    imag = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().H_Imaginary
                    phase = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().H_Phase
                    modulus = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().H_Modulus
                    print('_freq:{}_real:{}_imag:{}_phase:{}_modulus:{}'.format(freq, hreal, imag, phase, modulus))
                    await self.q.put([t, freq, 0.0, 0.0, hreal, imag, phase, modulus, 0.0])
                except:
                    pass
                await asyncio.sleep(0.6)
            elif type_ == 'tCV':
                
                j = self.current()
                v = self.potential()
                print('_time:{}_potential:{}_current: {}'.format(t,j,v))
                await self.q.put([t, 0.0, v, 0.0, 0.0, 0.0, 0.0, 0.0, j])
                await asyncio.sleep(0.4)

    def CellOnOff(self, onoff):
        if onoff == 'on':
            self.inst.Ei.CellOnOff = 1
        elif onoff == 'off':
            self.inst.Ei.CellOnOff = 0
        elif onoff == 'na':
            pass

    def parseNox(self, conf):
        # this function will read in a .nox and report the data as a json
        path = os.path.join(conf['safepath'],conf['filename'])
        self.finishedProc = self.inst.LoadProcedure(path)
        self.data = {}
        for comm in conf['parseinstructions']:
            names = [str(n) for n in self.finishedProc.Commands[comm].Signals.Names]
            self.data[comm] = {n: [float(f) for f in self.finishedProc.Commands[comm].Signals.get_Item(n).Value] for n in names}
        with open(path.replace('.nox', '_data.json'), 'w') as f:
            json.dump(self.data, f)
         
        return self.data

    def parseFRA(self,conf):
        path = os.path.join(conf['safepath'],conf['filename'])
        self.finishedProc = self.inst.LoadProcedure(path)

        self.data = {} 
        comm = 'FHLevel'   
        names = [str(n) for n in self.finishedProc.Commands[comm].Signals.Names]
        self.data[comm] = {n: [float(f) for f in self.finishedProc.Commands[comm].Signals.get_Item(n).Value] for n in names}
        
        self.fradata = {i:[] for i in range(578)} #2537 #7337
        for o in range(578):
            myComm = self.finishedProc.FraCommands.get_Item(o)
            sig_names = [n for n in myComm.Signals.Names]    
            for n in sig_names:
                if not type(myComm.Signals.get_Item(n).Value) == None:
                    try:
                        if type(myComm.Signals.get_Item(n).Value)==float:
                            self.fradata[o].append({n:myComm.Signals.get_Item(n).Value})
                        else:
                            self.fradata[o].append({n:[float(f) for f in myComm.Signals.get_Item(n).Value]})
                    except:
                        print('.')
        self.analyse_data = {i: [] for i in range(220)}
        j = 0
        for i in range(578):
            if len(self.fradata[i]) > 7:
                #if len(data[i][1]['Frequency']) == 1: 
                self.analyse_data[j].append(self.fradata[i])
                j += 1

        self.final_result = self.analyse_data.copy()
        self.final_result.update(self.data)

        with open(path.replace('.nox', '_data.json'), 'w') as f:
            json.dump(self.final_result, f)

        return self.final_result


    async def performMeasurement(self, procedure,setpoints,plot,onoffafter,safepath,filename, parseinstruction):
        conf = dict(procedure=procedure,setpoints=setpoints,
                     plot=plot,onoffafter=onoffafter,safepath=safepath,filename=filename,parseinstructions=parseinstruction)
        #LOAD PROCEDURE
        self.loadProcedure(conf['procedure'])
        #SET SETPOINTS
        self.setSetpoints(conf['setpoints'])
        #MEASURE
        self.proc.Measure()
        #PLOT LIVE
        await self.whileMeasuring(conf['plot'])
        #CELL ON/OFF
        self.CellOnOff(conf['onoffafter'])
        #SAVE
        sleep(0.1) #give the potentiostat some time to stwich everything off and save the data
        self.proc.SaveAs(os.path.join(conf['safepath'],conf['filename']))
        json.dump(conf,open(os.path.join(conf['safepath'],conf['filename'].replace('.nox','_conf.json')),'w'))
        
        if conf['procedure'] == 'ms':
            data = self.parseFRA(conf)    
        else: 
            data = self.parseNox(conf)

        return data
