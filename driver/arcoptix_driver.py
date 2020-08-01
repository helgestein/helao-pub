import clr

#DLLTest.dll (64 bit version) and CyUSB.dll must be in the same directory as ARCsoft.ARCspectroMd.dll

class arcoptix:
    def __init__(self,config):
        self.safepath = config['safepath']
        clr.AddReference(config['dll'])
        import ARCsoft.ARCspectroMd as arc
        self.interface = self.connect()

    def connect(self):
        return arc.ARCspectroMd.CreateApiInterface()

    def getSpectrum(self):
        return [float(i) for i in self.interface.Spectrum]

    def getWavelengths(self):
        return [float(i) for i in self.interface.Wavelength]

    def getWavenumbers(self):
        return [float(i) for i in self.interface.Wavenumber]

    def readSpectrum(self,av=1,):
        self.interface.ReadSpectrum(av,0)

    def readSpectrumTime(self,time):
        self.interface.ReadSpectrumTime(time,0)










