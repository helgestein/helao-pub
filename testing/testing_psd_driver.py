import sys
sys.path.append(r'C:/Users/juliu/helao-dev/driver')
sys.path.append(r'C:/Users/juliu/helao-dev/server')
from psd_driver import HamiltonPSD
import psd_server
pump = HamiltonPSD()

pump.pump(300)
pump.speed(5)
pump.rotate_valve(2)
pump.query_syringe()
pump.query_valve()

pump.disconnect()