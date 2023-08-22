
#Two force channels connected , packages necessary to be installed:
# https://www.me-systeme.de/setup/driver/usb/ftdi/
# and
# https://www.me-systeme.de/setup/gsv/gsvmulti/GSVmulti-1-48_64bit.zip
# the ladder will actually tell you which com port to use

# copy right 
#https://github.com/qdlmcfresh/gsv3usb/blob/main/gsv3_usb.py

# voltage input => -10 V to 10 V
# Current input => -20 mA to 20 mV 
# The baud rate can be differed from 4800  to 1,25 Mboud (bits/s)
# GSV has transmission rate of 38400 baud 
# range of change 500 mN 
import serial
import struct
import platform
import time



class MeasurementConverter:
    def convertValue(self, bytes):
        pass


class ForceMeasurementConverterKG(MeasurementConverter):
    def __init__(self, F_n, S_n, u_e):
        self.F_n = F_n
        self.S_n = S_n
        self.u_e = u_e

    def convertValue(self, bytes):
        A = struct.unpack('>H', bytes[1:])[0]
        return self.F_n / self.S_n * ((A - 0x8000) / 0x8000) * self.u_e * 2


class GSV3USB:
    def __init__(self, com_port=8, baudrate=38400):
        com_path = f'/dev/ttyUSB{com_port}' if platform.system(
        ) == 'Linux' else f'COM{com_port}'
        print(f'Using COM: {com_path}')
        self.sensor = serial.Serial(com_path, baudrate)
        self.converter = ForceMeasurementConverterKG(2000, 2, 1.05)

    def get_all(self, profile=0):
        self.sensor.write(struct.pack('bb', 9, profile))

    def save_all(self, profile=2):
        self.sensor.write(struct.pack('bb', 10, profile))

    def start_transmission(self):
        self.sensor.write(b'\x24')

    def stop_transmission(self):
        self.sensor.write(b'\x23')

    def set_zero(self):
        self.sensor.write(b'\x0C')

    def set_offset(self):
        self.sensor.write(b'\x0E')

    def set_bipolar(self):
        self.sensor.write(b'\x14')

    def set_unipolar(self):
        self.sensor.write(b'\x15')

    def get_serial_nr(self):
        self.stop_transmission()
        self.sensor.write(b'\x1F')
        ret = self.sensor.read(8)
        self.start_transmission()
        return ret

    def set_mode(self, text=False, max=False, log=False, window=False):
        x = 0
        if(text):
            x = x | 0b00010
        if(max):
            x = x | 0b00100
        if(log):
            x = x | 0b01000
        if(window):
            x = x | 0b10000
        self.sensor.write(struct.pack('bb', 0x26, x))

    def get_mode(self):
        self.stop_transmission()
        self.sensor.write(b'\x27')
        ret = self.sensor.read(1)
        self.start_transmission()
        return ret

    def get_firmware_version(self):
        self.stop_transmission()
        self.sensor.write(b'\x27')
        ret = self.sensor.read(2)
        self.start_transmission()
        return ret

    def get_special_mode(self):
        self.stop_transmission()
        self.sensor.write(b'\x89')
        ret = self.sensor.read(2)
        self.start_transmission()
        return ret

    def set_special_mode(self):
        pass
    #Helge commented this out because this is unsafe operation of the force sensor!!
    '''
    def read_value(self):
        read_val = self.sensor.read(3)
        return self.converter.convertValue(read_val)
    '''

    def read_value(self):
        self.stop_transmission()
        self.start_transmission()
        read_val = self.sensor.read(3)
        self.stop_transmission()
        return self.converter.convertValue(read_val)


    def clear_maximum(self):
        self.sensor.write(b'\x3C')

    def clear_buffer(self):
        self.sensor.write(b'\x25')


# def main():
# #     # 19206189 -> COM 5
# #     # 19206182 -> COM 4

#     dev = GSV3USB(9)
#     statement = True
#     count = 0
#     threshold = 2
#     if threshold < 3:
#         while abs(count) < 3:
#             dev.start_transmission()
#             count = dev.read_value()
#             dev.stop_transmission()
#             time.sleep(1)
#             print(count)
#     elif count > 3:
#         print("I am breaking")
#     else:
#         print("I am breaking any way")

# #     # try: 
# #     #     count = 0 
# #     #     while count < 3: 
# #     #         count = dev.read_value()
# #     #         print(count)
# #     # except: 
# #     #     print("I am breaking")


# #     # try:   
# #     #     while True:
# #     #         print(dev.read_value())
# #     # except KeyboardInterrupt:
# #     #     print("Exiting")
# #     #     return


#main()