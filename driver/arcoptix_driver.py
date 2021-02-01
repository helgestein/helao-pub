import clr
import json

#DLLTest.dll (64 bit version) and CyUSB.dll must be in the same directory as ARCsoft.ARCspectroMd.dll

class arcoptix:
    def __init__(self,config):
        clr.AddReference(config['dll'])
        import ARCsoft.ARCspectroMd as arc
        self.interface = arc.ARCspectroMd.CreateApiInterface()

    def getSpectrum(self,filename:str):
        data = {'wavelengths':[float(i) for i in self.interface.Wavelength],'wavenumbers':[float(i) for i in self.interface.Wavenumber],'intensities':[float(i) for i in self.interface.Spectrum],
                'units':{'wavelengths':'nm','wavenumbers':'1/cm','intensities':'counts'}}
        with open(filename,'w') as outfile: 
            json.dump(data,outfile)
        return data

    def readSpectrum(self,av:int=1,):
        self.interface.ReadSpectrum(av,0)

    def readSpectrumTime(self,time:float):
        self.interface.ReadSpectrumTime(time,0)

    def loadFile(self,filename:str):
        with open(filename,'r') as infile:
            data = json.load(infile)
        return data









