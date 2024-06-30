import clr
import sys
from pathlib import Path
sys.path.append(r'C:/Users/juliu/helao-dev')
sys.path.append(r'C:/Users/juliu/helao-dev/config')
sys.path.append(r'C:\Users\juliu\Documents\PSPythonSDK')

from sdc_cyan import config as conf
sys.path.append(conf['palmsensDriver']["PalmsensSDK_python"])
from pspython.pspyinstruments import InstrumentManager, Instrument

clr.AddReference("System")

clr.AddReference(str(Path(conf['palmsensDriver']["PalmsensSDK_python"]).joinpath("pspython", "PalmSens.Core.dll")))
clr.AddReference(str(Path(conf['palmsensDriver']["PalmsensSDK_python"]).joinpath("pspython", "PalmSens.Core.Windows.dll")))

from System import Enum 
import PalmSens.Techniques.Impedance as eis
from PalmSens.Techniques.Impedance import enumScanType, enumFrequencyType, EnumFrequencyMode
from PalmSens.Techniques import ImpedimetricMethod, Potentiometry, OpenCircuitPotentiometry
import PalmSens.Techniques

### Read all the available parameters of the technique:

dir(PalmSens.Techniques.Chronocoulometry)
dir(ImpedimetricMethod)
dir(Potentiometry.RangingPotential)
dir(OpenCircuitPotentiometry)

### Get default value of the parameter using get method:
ImpedimetricMethod().get_FreqType()
ImpedimetricMethod().get_ExtraValueMsk()
ImpedimetricMethod().set_ExtraValueMsk(Enum(int(0)))
ImpedimetricMethod().get_FreqType()
ImpedimetricMethod().get_OCPmode()
Potentiometry().get_UseLimitMaxValue()

### Read possible values of the Enum parameter:
def read_enum_values(enum_type):
    return [(name, Enum.GetName(enum_type, name), Enum.ToObject(enum_type, name)) for name in Enum.GetValues(enum_type)]

read_enum_values(enumScanType)
read_enum_values(enumFrequencyType)