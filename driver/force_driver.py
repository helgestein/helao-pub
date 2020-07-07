import ctypes
import time

#For referenced files and documentation, see https://www.me-systeme.de/en/software/programming/megsv

#If cross-referencing this code with the API found in ba-megsv.pdf, note that GSV_Error = -1, GSV_OK = 0, GSV_True = 1

#Limited testing shows that the force sensor transmits 25 values per second


class MEGSV:
    def __init__(self,port,buffer,dll):
        self.port = port
        self.buffer = buffer
        self.ad = ctypes.c_double()
        self.dll = ctypes.WinDLL(dll)
        self.adv = (ctypes.c_double*buffer)()
        self.nvals = ctypes.c_int()
    
    def activate(self):
        if self.dll.GSVactivate(self.port,self.buffer) == 0:
            print("Activation successful!")
        else:
            print("Failed to activate connection. Perhaps you have the wrong port, the device is not plugged in, or the connection is already active.")
    

    def read(self):
        res = self.dll.GSVread(self.port,ctypes.byref(self.ad))
        if res == 1:
            return self.ad.value
        if res == 0:
            return None
        if res == -1:
            print("Error.")
            return None

    def readBuffer(self):
        res = self.dll.GSVreadMultiple(self.port,self.adv,self.buffer,ctypes.byref(self.nvals))
        if res == 1:
            return [self.adv[i] for i in range(self.nvals.value)]
        if res == 0:
            print("No data in buffer.")
            return None
        if res == -1:
            print("Error.")
            return None
    
    def release(self):
        #Release the connection between the force probe and the computer.
        self.dll.GSVrelease(self.port,self.buffer)