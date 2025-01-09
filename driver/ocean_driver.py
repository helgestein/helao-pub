from seabreeze.cseabreeze import SeaBreezeAPI
import json
import os
#there are more features that the device has which we could implement
#try calling self.device.features to see a dictionary of them
#i think this is enough for now, however

class ocean:
    def __init__(self,config):
        self.api = SeaBreezeAPI()
        #this is convoluted, but will prevent code from crashing if initiated when no spectrometer connected
        for d in self.api.list_devices():
            if d.serial_number == config['serial']:
                self.device = d
        self.open()
        self.device.f.spectrometer.set_trigger_mode(0)
        self.safepath = config['safepath']

    def open(self):
        self.device.open()

    def close(self):
        self.device.close()

    #can integrate for between 8ms and 1600s
    #t is integration time in µs
    #maximum intensity is 200000
    def readSpectrum(self,t:int,filename:str):
        self.device.f.spectrometer.set_integration_time_micros(t)
        self.device.features['data_buffer'][0].clear()
        data = {'wavelengths':self.device.f.spectrometer.get_wavelengths().tolist(),'intensities':self.device.f.spectrometer.get_intensities().tolist(),
                'units':{'wavelengths':'nm','intensities':'counts'}}
        with open(os.path.join(self.safepath,filename),'w') as outfile: 
            json.dump(data,outfile)
        return data

    def loadFile(self,filename:str):
        with open(filename,'r') as infile:
            data = json.load(infile)
        return data
