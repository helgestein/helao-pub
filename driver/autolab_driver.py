import os
import sys
import clr
from time import sleep
import json

class Autolab:
    def __init__(self,autolab_conf):
        self.basep = autolab_conf["basep"]
        sys.path.append(self.basep)
        self.procp = autolab_conf["procp"]
        self.hwsetupf = autolab_conf["hwsetupf"]
        self.micsetupf = autolab_conf["micsetupf"]
        self.proceduresd = autolab_conf["proceuduresd"]
        clr.AddReference("EcoChemie.Autolab.Sdk")
        #this is a hacky way of trying again
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
            # to be sure that the procedure is stopped we try to abort it
            self.proc.Abort()
        except:
            print('Procedure abort failed. Disconnecting anyhow.')
        self.inst.Disconnect()

    def ismeasuring(self):
        try:
            return self.proc.IsMeasuring()
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

    def time(self):
        return 'TODO'

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
            for param, value in params.items():
                self.proc.Commands[comm].CommandParameters[param].Value = value

    def whileMeasuring(self, type_):
        import time
        from copy import copy
        then = copy(time.monotonic())
        while self.proc.IsMeasuring:
            freq = 100  # not to cause an exception
            sleep(0.5)
            if type_ == 'impedance':
                try:
                    freq = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().get_Frequency()
                    hreal = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().get_H_Real()
                    imag = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().get_H_Imaginary()
                    phase = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().get_H_Phase()
                    modulus = self.proc.FraCommands['FIAScan'].get_FIAMeasurement().get_H_Modulus()
                    print('_freq:{}_real:{}_imag:{}_phase:{}_modulus:{}'.format(freq, hreal, imag, phase, modulus))
                except:
                    pass
                sleep(0.5)
            elif type_ == 'tCV':
                now = copy(time.monotonic())
                print('_time:{}_potential:{}_current: {}'.format(now-then, self.potential(), self.current()))
                sleep(0.1)

    def CellOnOff(self, onoff):
        if onoff == 'on':
            self.inst.Ei.CellOnOff = 1
        elif onoff == 'off':
            self.inst.Ei.CellOnOff = 0
        elif onoff == 'na':
            pass

    def parseNox(self, conf):
        # this function will read in a .nox and eport the data as a json
        path = os.path.join(conf['safepath'],conf['filename'])
        self.finishedProc = self.inst.LoadProcedure(path)
        self.data = {}
        for comm in conf['parseinstructions']:
            names = [str(n) for n in self.finishedProc.Commands[comm].Signals.Names]
            self.data[comm] = {n: [float(f) for f in self.finishedProc.Commands[comm].Signals.get_Item(n).Value] for n in names}
        with open(path.replace('.nox', '_data.json'), 'w') as f:
            json.dump(self.data, f)

    def performMeasurement(self, procedure,setpoint_keys,setpoint_values,plot,onoffafter,safepath,filename):
        conf = dict(procedure=procedure,setpoints={k:v for k,v in zip(setpoint_keys,setpoint_values)},
                     plot=plot,onoffafter=onoffafter,safepath=safepath,filename=filename)
        #LOAD PROCEDURE
        self.loadProcedure(conf['procedure'])
        #SET SETPOINTS
        self.setSetpoints(conf['setpoints'])
        #MEASURE
        self.proc.Measure()
        #PLOT LIVE
        self.whileMeasuring(conf['plot'])
        #CELL ON/OFF
        self.CellOnOff(conf['onoffafter'])
        #SAVE
        sleep(0.1) #give the potentiostat some time to stwich everything off and save the data
        json.dump(conf,open(os.path.join(conf['safepath'],conf['filename'].replace('.nox','_conf.json')),'w'))
        self.proc.SaveAs(os.path.join(conf['safepath'],conf['filename']))
        self.parseNox(conf)
