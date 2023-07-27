from math import pi

config = dict()

config['servers'] = dict(kadiDriver = dict(host="127.0.0.1",port=13376),
                         kadi = dict(host="127.0.0.1",port=13377),
                         orchestrator = dict(host="192.168.31.114",port=13380),
                         oceanDriver = dict(host="127.0.0.1",port=13383),
                         ocean = dict(host="127.0.0.1",port=13384),
                         arcoptixDriver = dict(host="127.0.0.1",port=13385),
                         arcoptix = dict(host="127.0.0.1",port=13386),
                         owisDriver = dict(host="127.0.0.1",port=13387),
                         owis = dict(host="127.0.0.1",port=13388))

config['kadiDriver'] = dict(host = "https://polis-kadi4mat.iam-cms.kit.edu",
            PAT = "99804736e3c4a1059eb5f805dc1520dab6f8714f6c7d2d88")
config['kadi'] = dict(group='2',url="http://127.0.0.1:13376")

#r'C:\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd'
#i don't know why a relative path is needed in scripts. it is not in terminal. but here we are.
config['arcoptixDriver'] = dict(dll = r'..\..\..\..\..\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd',safepath = 'C:/Users/Operator/Documents/data/safe/ftir')
config['arcoptix'] = dict(url="http://127.0.0.1:13385")

config['orchestrator'] = dict(path=r'C:\Users\Operator\Documents\data',kadiurl="http://127.0.0.1:13377")

#com ports are set using ComPortMan. should be consistent as long as you do not change which usb port they are plugged into
#to modify com port selection, modify C:/Users/Operator/Downloads/ComPortMan/ComPortMan.INI
#it seems like this breaks if I unplug and plug in the USB hub, or if the computer is turned off!!! USB hub gets new identity, and needs to be updated in manager.
config['owisDriver'] = dict(serials=[
                                #dict(port='COM27', baud=9600, timeout=0.1),dict(port='COM26', baud=9600, timeout=0.1),
                                dict(port='COM25', baud=9600, timeout=0.1),dict(port='COM24', baud=9600, timeout=0.1)],
                                currents=[
                                          #dict(mode=1,drive=80,hold=40),dict(mode=0,drive=50,hold=30),
                                          dict(mode=0,drive=50,hold=50),dict(mode=0,drive=50,hold=50)],
                                safe_positions=[
                                    #3750000,None,
                                    600000,600000])

#ftirLow might be bent slightly....
#from coordinates to origin is 100.25,45.25 or so. frankly i would like .1 mm precision on this and only have mm
#i think my calibration is .1 mm precise in z axis. work to do in x and y, and worried about angles
#so i think i can get .1 mm precise in z now, and .25 mm precise on x and y. 
# could do better with a better calibration point. definitely worried about the bend
config['owis'] = dict(coordinates={"sem":{"x":63.1,"y":49.493,"z":None,"theta":pi,"I":True},
                                   "base":{"x":100.25,"y":45.25,"z":0,"theta":pi,"I":True},
                                   "wafer":{"x":100.25,"y":45.25,"z":0,"theta":pi,"I":True},
                                   "motor":{"x":0,"y":0,"z":0,"theta":0,"I":True},
                                   "fuzhi":{},
                                   "alexey":{}},
                      references={"si":[-5.25,28.642,.48],"au":[-7.25,-33.673,3.8],"air":[0,0,60]}, #best intensity at 3.8. would expect it at 2. how much error in focal? how much in height of sample?
                      probes={"raman532":{"motor":1,"coordinates":[None,None,None],"focal":7.5}, #with the High probe, best intensity at 3.6. needs more study (after i put up light-shielding)
                             "raman785":{"motor":1,"coordinates":[None,None,None],"focal":7.5},
                             "ftirLow":{"motor":0,"coordinates":[31.25,51.25,20],"focal":1.4},
                             "ftirHigh":{"motor":0,"coordinates":[17.5,51.25,20.2],"focal":1.4},
                             "motor":{"motor":None,"coordinates":[0,0,None],"focal":None}},
                      x=0,y=1, #motor id for x and y motors
                      n=2, #number of connected motors
                      url="http://127.0.0.1:13387")
#reference coordinates are a vector pointing from reference point on sample holder to the given reference.
#       z value is displacement of reference point relative to bed of sample holder.
#       directionally in motor coordinate system
#probe coordinates are the x-y value in motor coordinates for which the probe is centered on reference point
#       z value is motor coordinate at which value is in contact with sample bed.

#let v1 be vector of x-y in motor coordinates, with origin at reference point, v2 vector of x-y in sample coordinates.
#v2 = R(theta)I(v1-[x,y]), so v1 = IR(-theta)v2 + [x,y]
#R is 2x2 rotation matrix, and I is identity matrix if I=True, and inversion on x if I=False.
#z is motor coordinates of probe motor when probe resting on sample
#x,y are a vector pointing from reference point on sample holder to sample coordinate system origin, in motor coordinate system


config['oceanDriver'] = dict(safepath = 'C:/Users/Operator/Documents/data/safe/raman')
config['ocean'] = dict(wavelength=785,url="http://127.0.0.1:13383")

#still need to fix launch and visualizer
config['launch'] = dict(server = ['owisDriver','oceanDriver','arcoptixDriver','kadiDriver'],
                        action = ['owis','ocean','arcoptix','kadi'],
                        orchestrator = ['orchestrator'])

config['instrument'] = "hits"


#so i am relieved that the turbulence wasn't forcasted; i couldn't have changed anyways