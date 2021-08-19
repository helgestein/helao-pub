import os
import sys
import clr
from time import sleep
import json
import asyncio
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import json
from config.sdc_4 import config
autolab_conf = config['autolabDriver']

q = asyncio.Queue(loop=asyncio.get_event_loop())
basep = autolab_conf["basep"]
sys.path.append(basep)
procp = autolab_conf["procp"]
hwsetupf = autolab_conf["hwsetupf"]
micsetupf = autolab_conf["micsetupf"]
proceduresd = autolab_conf["proceuduresd"]
clr.AddReference("EcoChemie.Autolab.Sdk")
try:
    from EcoChemie.Autolab import Sdk as sdk
except:
    from EcoChemie.Autolab import Sdk as sdk
inst = sdk.Instrument()
inst.HardwareSetupFile = hwsetupf
inst.AutolabConnection.EmbeddedExeFileToStart = micsetupf
inst.Connect()
proc = None
name = "cccv"
#name2= "cv"
proc = inst.LoadProcedure(proceduresd[name])

# how to get the setpoints
init_setpoint = [i for i in proc.Commands.IdNames]

## use the setpoint that you want to change 
# eg . init_setpoint[3]

## get the parameters that exist in that point
param_of_that_setpoint = [i for i in proc.Commands[init_setpoint[3]].CommandParameters.IdNames]

## what is the default value and how i chagne it
#e.g
# you can see the default value like this: 
proc.Commands[init_setpoint[3]].CommandParameters[param_of_that_setpoint[0]].Value

# disconnetct nova , always !
inst.Disconnect()