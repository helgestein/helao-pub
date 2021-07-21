import ctypes
import time

#For referenced files and documentation, see https://www.me-systeme.de/en/software/programming/megsv

#If cross-referencing this code with the API found in ba-megsv.pdf, note that GSV_Error = -1, GSV_OK = 0, GSV_True = 1

class MEGSV:
    def __init__(self,conf):
        self.port = conf["port"]
        self.buffer = conf["buffer_size"]
        self.ad = ctypes.c_double()
        self.dll = ctypes.WinDLL(conf["dll_address"]) 
        self.adv = (ctypes.c_double*self.buffer)()
        self.nvals = ctypes.c_int()
        self.activate()
    
    def activate(self):
        if self.dll.GSVactivate(self.port,self.buffer) == 0:
            print("Activation successful!")
        else:
            raise ConnectionError
    

    def read(self):
        res = self.dll.GSVread(self.port,ctypes.byref(self.ad))
        if res == 1:
            return self.ad.value
        if res == 0:
            return None
        if res == -1:
            raise ConnectionError

    def readBuffer(self):
        res = self.dll.GSVreadMultiple(self.port,self.adv,self.buffer,ctypes.byref(self.nvals))
        if res == 1:
            return [self.adv[i] for i in range(self.nvals.value)]
        if res == 0:
            print("No data in buffer.")
            return None
        if res == -1:
            raise ConnectionError
    
    def release(self):
        self.dll.GSVrelease(self.port,self.buffer)