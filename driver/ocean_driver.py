import numpy
from seabreeze.cseabreeze import SeaBreezeAPI

#there are more features that the device has which we could implement
#try calling self.device.features to see a dictionary of them
#i think this is enough for now, however

class ocean:
    def __init__(self):
        self.api = SeaBreezeAPI()
        #this is convoluted, but will prevent code from crashing if initiated when no spectrometer connected
        a = self.api.list_devices()
        self.device = None if len(a) == 0 else a[0]

    def findDevice(self):
        a = self.api.list_devices()
        self.device = None if len(a) == 0 else a[0]
        return self.device

    def open(self):
        self.device.open()

    def close(self):
        self.device.close()

    def getWavelengths(self):
        return self.device.f.spectrometer.get_wavelengths().tolist()

    def getIntensities(self):
        return self.device.f.spectrometer.get_intensities().tolist()
.