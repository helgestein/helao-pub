#this is the server
import sys
sys.path.append(r"./config")
from autolab_driver import Autolab
import mischbares_small
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Autolab server V1",
    description="This is a very fancy autolab server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/potentiostat/disconnect")
def disconnect():
    a.disconnect()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'disconnect',
                                    'parameters':None},
                        data = {'data':None})
    return retc

@app.get("/potentiostat/ismeasuring")
def ismeasuring():
    ret = a.ismeasuring()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'ismeasuring',
                                    'parameters':None},
                        data = {'ismeasuring':ret})
    return retc

@app.get("/potentiostat/potential")
def potential():
    ret = a.potential()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'getpotential',
                                    'parameters':None},
                        data = {'potential':ret})
    return retc

@app.get("/potentiostat/current")
def current():
    ret = a.current()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'getcurrent',
                                    'parameters':None},
                        data = {'current':ret})
    return retc

@app.get("/potentiostat/setcurrentrange")
def setCurrentRange(crange: str):
    a.setCurrentRange(crange)
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'setcurrentrange',
                                    'parameters':crange},
                        data = {'currentrange':crange})
    return retc

@app.get("/potentiostat/setstability")
def setStability(stability):
    a.setStability(stability)
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'setStability',
                                    'parameters':stability},
                        data = {'currentrange':stability})
    return retc

@app.get("/potentiostat/appliedpotential")
def appliedPotential():
    ret = a.appliedPotential()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'appliedpotential',
                                    'parameters':None},
                        data = {'appliedpotential':ret})
    return retc

@app.get("/potentiostat/abort")
def abort():
    ret = a.abort()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'abort',
                                    'parameters':None},
                        data = {'abort':True})

@app.get("/potentiostat/abort")
def loadProcedure(name:str):
        self.proc = self.inst.LoadProcedure(self.proceduresd[name])

def setSetpoints(self, setpoints):
        for comm, params in setpoints.items():
            for param, value in params.items():
                self.proc.Commands[comm].CommandParameters[param].Value = value

def whileMeasuring(self, type):
        import time
        from copy import copy
        then = copy(time.monotonic())
        while self.proc.IsMeasuring:
            freq = 100  # not to cause an exception
            sleep(0.5)
            if type == 'impedance':
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
            elif type == 'tCV':
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

def performMeasurement(self, conf):
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


if __name__ == "__main__":
    p = pump()
    uvicorn.run(app, host="127.0.0.1", port=13371)

    autolab_conf = mischbares_small.config['autolab']
    a = Autolab(mischbares_small.config['autolab'])
