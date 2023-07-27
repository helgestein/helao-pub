import clr
import json
import os
from enum import Enum

#DLLTest.dll (64 bit version) and CyUSB.dll must be in the same directory as ARCsoft.ARCspectroMd.dll

class arcoptix:
    def __init__(self,config):
        clr.AddReference(config['dll'])
        import ARCsoft.ARCspectroMd as arc
        self.interface = arc.ARCspectroMd.CreateApiInterface()
        self.safepath = config['safepath']

    def getSpectrum(self,filename:str,time:bool=False,av:int=1,wlrange:str=None,wnrange:str=None,inrange:str=None):
        if time:
            self.interface.ReadSpectrumTime(av,0)
        else:
            self.interface.ReadSpectrum(av,0)
        j,k = 0,65536
        wavelengths = [float(i) for i in self.interface.Wavelength]
        wavenumbers = [float(i) for i in self.interface.Wavenumber]
        if wlrange != None and wnrange != None or wlrange != None and inrange != None or wnrange != None and inrange != None:
            raise Exception("cannot set limits on more than one of wavelength, wavenumber, and index")
        elif wlrange != None:
            wlrange = json.loads(wlrange)
            assert len(wlrange) == 2
            wlrange = (min(wlrange),max(wlrange))
            for wlin in range(k):
                if wavelengths[wlin] <= wlrange[1]:
                    j = wlin
                if wavelengths[wlin] < wlrange[0]:
                    k = wlin
                    break
        elif wnrange != None:
            wnrange = json.loads(wnrange)
            assert len(wnrange) == 2
            wnrange = (min(wnrange),max(wnrange))
            for wnin in range(k):
                if wavenumbers[wnin] >= wnrange[0]:
                    j = wnin
                if wavelengths[wnin] > wlrange[1]:
                    k = wlin
                    break
        elif inrange != None:
            j,k = json.loads(inrange)
        data = {'wavelengths':wavelengths[j:k],'wavenumbers':wavenumbers[j:k],'intensities':[float(i) for i in self.interface.Spectrum][j:k],
                'units':{'wavelengths':'m','wavenumbers':'1/m','intensities':'counts'}}
        with open(os.path.join(self.safepath,filename),'w') as outfile: 
            json.dump(data,outfile)
        return data

    #must be an int 0-3. 0 = Low, 1 = Medium, 2 = High, 3 = Extreme
    def setGain(self,gain:int):
        import ARCsoft.ARCspectroMd as arc
        assert gain in range(4)
        if gain == 0:
            self.interface.Gain = arc.Gain.Low
        elif gain == 1:
            self.interface.Gain = arc.Gain.Medium
        elif gain == 2:
            self.interface.Gain = arc.Gain.High
        elif gain == 3:
            self.interface.Gain = arc.Gain.Extreme

    def getSaturation(self):
        return self.interface.SaturationRatio
    
    def getGain(self):
        return int(self.interface.Gain)

    def loadFile(self,filename:str):
        with open(filename,'r') as infile:
            data = json.load(infile)
        return data









