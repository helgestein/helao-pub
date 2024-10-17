#This is a HELAO driver for the Hamilton MicroLab 600 Series Dual Syringe Pump
#prerequisites:
#Install the ML600 Programming Helper tool
#Connect directly to the ML600 without the touchscreen
#Chnage your IP of the wired network to 192.168.100.50
# if this is not causing any trouble with any of your other instruments keep it
#otherwise you may need to change the static IP adress through the
#programming helper tool
#turn the pump on.
#!!!!I'm expecting the syringes to be empty at initialization!!!!
#if they are not this might cause errors and unintended pumping of liquid
#make sure to diable PoE by pressing the on button for a long time like 5s+!
import os
import sys
import clr
import numpy as np





#units of the hamilton are in nL
class Hamilton:
    def __init__(self,hamilton_conf):
        self.dlls = ['Hamilton.Components.TransportLayer.ComLink',
 		            'Hamilton.Components.TransportLayer.Discovery',
 		            'Hamilton.Components.TransportLayer.HamCli',
 		            'Hamilton.Components.TransportLayer.Protocols',
 		            'Hamilton.MicroLab.MicroLabDaisyChain',
 		            'Hamilton.Module.ML600']
        self.conf = hamilton_conf
        sys.path.append(self.conf['dllpath'])
        for dll in self.dlls:
            print(f'Adding {dll}')
            clr.AddReference(dll)
        from Hamilton.Components.TransportLayer import Protocols
        from Hamilton import MicroLab
        from Hamilton.MicroLab import Components
        self.ml600Chain = MicroLab.DaisyChain()
        self.discovered = self.ml600Chain.Discover(5)
        self.ml600Chain.Connect(self.discovered[0].Address,self.discovered[0].Port)
        #self.ml600Chain.Connect("192.168.100.100")
        if self.ml600Chain.get_IsConnected():
            print("Made a connection to Microlab 600")

        self.InstrumentOnChain = self.ml600Chain.get_ML600s()[0].get_ChainPosition()

        #setup
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.LeftPump.Syringe.SetSize(np.uint32(self.conf['left']['syringe']['volume']))
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.RightPump.Syringe.SetSize(np.uint32(self.conf['right']['syringe']['volume']))
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.LeftPump.Syringe.SetFlowRate(np.uint32(self.conf['left']['syringe']['flowRate']))
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.RightPump.Syringe.SetFlowRate(np.uint32(self.conf['right']['syringe']['flowRate']))
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.LeftPump.Syringe.SetInitFlowRate(np.uint32(self.conf['left']['syringe']['initFlowRate']))
        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.RightPump.Syringe.SetInitFlowRate(np.uint32(self.conf['right']['syringe']['initFlowRate']))


        self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.Pumps.InitializeDefault()
        if self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.Pumps.AreInitialized():
            print("Pumps are initialized")


    def pump(self,leftVol=0,rightVol=0,leftPort=0,rightPort=0,delayLeft=0,delayRight=0):
        lv = np.int32(leftVol) #in nL
        rv = np.int32(rightVol)
        lp = np.byte(leftPort) #1,2 or 9,10
        rp = np.byte(rightPort)
        dr = np.uint(delayRight) # ms
        dl = np.uint32(delayLeft)
        ret = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.Pumps.AspirateFromPortsWithDelay(lv, rv, lp, rp, dr, dl)
        return ret

    def getStatus(self):
        vl = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.LeftPump.Syringe.GetRemainingVolume()
        vr = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.RightPump.Syringe.GetRemainingVolume()
        vpl = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.LeftPump.Valve.GetNumberedPos()
        vpr = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.RightPump.Valve.GetNumberedPos()
        return dict(vl=vl,vr=vr,vpl=vpl,vpr=vpr)

    def moveAbs(self,leftSteps=0,rightSteps=0,leftPort=0,rightPort=0,delayLeft=0,delayRight=0):
        lv = np.int32(leftSteps) #in nL
        rv = np.int32(rightSteps)
        lp = np.byte(leftPort) #1,2 or 9,10
        rp = np.byte(rightPort)
        dr = np.uint(delayRight) # ms
        dl = np.uint32(delayLeft)
        ret = self.ml600Chain.ML600s[self.InstrumentOnChain].Instrument.Pumps.MoveAbsoluteInStepsWithDelay(lv, rv, lp, rp, dr, dl)
        return ret

    def disconnect(self):
        status = self.getStatus()
        self.pump(leftVol=-status['vl'],rightVol=-status['vr'],leftPort=2,rightPort=2)
        self.ml600Chain.Disconnect()

