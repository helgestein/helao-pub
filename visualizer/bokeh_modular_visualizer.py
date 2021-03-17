
import os
import sys
import websockets
import asyncio
import json
import collections
from functools import partial
from importlib import import_module
from functools import partial


from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
from bokeh.models import Range1d
from bokeh.models import Arrow, NormalHead, OpenHead, VeeHead
#from tornado.ioloop import IOLoop
from munch import munchify
from bokeh.palettes import Spectral6, small_palettes
from bokeh.transform import linear_cmap

from bokeh.models import TextInput
from bokeh.models.widgets import Div
from bokeh.layouts import layout, Spacer
import pathlib
import copy
import math


# TODO
# - also display active PM as overlay in plot


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))
#from classes import StatusHandler


confPrefix = sys.argv[1] # the name of the config file
servKey = sys.argv[2] # the server key of this script defined in config (i.e. servKey=dict(..)
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"] # get the config defined in config file under dict config["servers"]
S = C[servKey] # the config for this particular server/script in config file


#C[S.params.aligner_server].params.motor_server

##############################################################################
# motor module class
##############################################################################
class C_motorvis:
    def __init__(self, config):
        self.config = config
        self.data_url = config['wsdata_url']
        self.stat_url = config['wsstat_url']
        self.IOloop_data_run = False
        self.axis_id = config['axis_id']
        self.params = config['params']

        self.data = dict()
        # buffered version
        self.dataold = copy.deepcopy(self.data)

        # create visual elements
        self.layout = []
        self.motorlayout_axis = []
        self.motorlayout_stat = []
        self.motorlayout_err = []
        # display of axis positions and status
        self.axisvaldisp = []
        self.axisstatdisp = []
        self.axiserrdisp = []
        tmpidx = 0
        for axkey, axitem in self.axis_id.items():
            self.axisvaldisp.append(TextInput(value="", title=axkey+"(mm)", disabled=True, width=100, height=40, css_classes=['custom_input2']))
            self.motorlayout_axis.append(layout([[self.axisvaldisp[tmpidx],Spacer(width=40)]]))
            self.axisstatdisp.append(TextInput(value="", title=axkey+" status", disabled=True, width=100, height=40, css_classes=['custom_input2']))
            self.motorlayout_stat.append(layout([[self.axisstatdisp[tmpidx],Spacer(width=40)]]))
            self.axiserrdisp.append(TextInput(value="", title=axkey+" Error code", disabled=True, width=100, height=40, css_classes=['custom_input2']))
            self.motorlayout_err.append(layout([[self.axiserrdisp[tmpidx],Spacer(width=40)]]))
            tmpidx = tmpidx+1

        # add a 2D map for xy
        ratio = (self.params['xmax']-self.params['xmin'])/(self.params['ymax']-self.params['ymin'])
        self.plot_motor = figure(title="xy MotorPlot", height=300,x_axis_label='plate X (mm)', y_axis_label='plate Y (mm)',width = 800, aspect_ratio=ratio)
        self.plot_motor.x_range=Range1d(self.params['xmin'], self.params['xmax'])
        self.plot_motor.y_range=Range1d(self.params['ymin'], self.params['ymax'])

        # combine all sublayouts into a single one
        self.layout = layout([
            [Spacer(width=20), Div(text="<b>Motor Visualizer module</b>", width=200+50, height=15)],
            layout([self.motorlayout_axis]),
            Spacer(height=10),
            layout([self.motorlayout_stat]),
            Spacer(height=10),
            layout([self.motorlayout_err]),
            Spacer(height=10),
            layout([self.plot_motor]),
            Spacer(height=10)
            ],background="#C0C0C0")


    async def IOloop_data(self): # non-blocking coroutine, updates data source
        async with websockets.connect(self.data_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    self.data =  await ws.recv()
                    print(" ... VisulizerWSrcv:",self.data)
                except:
                    self.IOloop_data_run = False


##############################################################################
# potentiostat module class
##############################################################################
class C_nidaqmxvis:
    def __init__(self, config):
        self.config = config

        self.config = config
        self.dataVOLT_url = config['wsdataVOLT_url']
        self.dataCURRENT_url = config['wsdataCURRENT_url']
        self.stat_url = config['wsstat_url']
        self.IOloop_data_run = False

        self.time_stamp = 0
        self.time_stampV = 0
        self.time_stampI = 0
        self.VOLTlist = {}
        self.CURRENTlist = {}

        self.sourceVOLT = ColumnDataSource(data=dict(t_s=[],
                                                     Cell_1=[],
                                                     Cell_2=[],
                                                     Cell_3=[],
                                                     Cell_4=[],
                                                     Cell_5=[],
                                                     Cell_6=[],
                                                     Cell_7=[],
                                                     Cell_8=[],
                                                     Cell_9=[]))
        self.sourceCURRENT = ColumnDataSource(data=dict(t_s=[],
                                                     Cell_1=[],
                                                     Cell_2=[],
                                                     Cell_3=[],
                                                     Cell_4=[],
                                                     Cell_5=[],
                                                     Cell_6=[],
                                                     Cell_7=[],
                                                     Cell_8=[],
                                                     Cell_9=[]))

        # create visual elements
        self.layout = []
        colors = small_palettes['Viridis'][9]                
        self.plot_VOLT = figure(title="CELL VOLTs", height=300)
        for i in range(9):
            _ = self.plot_VOLT.line(x='t_s', y=f'Cell_{i}', source=self.sourceVOLT, name=f'VCell{i}', line_color=colors[i])#str(self.time_stamp))
        self.plot_CURRENT = figure(title="CELL CURRENTs", height=300)
        for i in range(9):
            _ = self.plot_CURRENT.line(x='t_s', y=f'Cell_{i}', source=self.sourceCURRENT, name=f'ICell{i}', line_color=colors[i])#str(self.time_stamp))

        # combine all sublayouts into a single one
        self.layout = layout([
            [Spacer(width=20), Div(text="<b>NImax Visualizer module</b>", width=200+50, height=15)],
            layout([self.plot_VOLT]),
            Spacer(height=10),
            layout([self.plot_CURRENT]),
            Spacer(height=10)
            ],background="#C0C0C0")


    def updateVOLT(self, new_data):
        self.sourceVOLT.data = {k: [] for k in self.sourceVOLT.data}
        self.sourceVOLT.stream(new_data)
        # for i in range(9):
        #     old_point = self.plot_VOLT.select(name=f'VCell{i}')
        #     if len(old_point)>0:
        #         self.plot_VOLT.renderers.remove(old_point[0])
        #     colors = small_palettes['Viridis'][9]
        #     _ = self.plot_VOLT.line(x='t_s', y=f'Cell_{i}', source=self.sourceVOLT, name=f'VCell{i}', line_color=colors[i])


    def updateCURRENT(self, new_data):
        self.sourceCURRENT.data = {k: [] for k in self.sourceCURRENT.data}
        self.sourceCURRENT.stream(new_data)
    #     for i in range(9):
    #         old_point = self.plot_CURRENT.select(name=f'ICell{i}')
    #         if len(old_point)>0:
    #             self.plot_CURRENT.renderers.remove(old_point[0])
    #         colors = small_palettes['Viridis'][9]
    #         _ = self.plot_CURRENT.line(x='t_s', y=f'Cell_{i}', source=self.sourceCURRENT, name=f'ICell{i}', line_color=colors[i])


    async def IOloop_dataVOLT(self): # non-blocking coroutine, updates data source
        global doc
        async with websockets.connect(self.dataVOLT_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    data = json.loads(await ws.recv())
                    self.VOLTlist = {f"Cell_{idx+1}":data[idx] for idx in range(len(data))}
                    self.VOLTlist['t_s'] = [self.time_stampV+i for i in range(len(data[0]))]
                    self.time_stampV = self.time_stampV + 1
                    #print(" ... VisulizerWSrcv:",data)
                    doc.add_next_tick_callback(partial(self.updateVOLT, self.VOLTlist))
                except:
                    self.IOloop_data_run = False


    async def IOloop_dataCURRENT(self): # non-blocking coroutine, updates data source
        global doc
        async with websockets.connect(self.dataCURRENT_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    data = json.loads(await ws.recv())
                    self.CURRENTlist = {f"Cell_{idx+1}":data[idx] for idx in range(len(data))}                    
                    self.CURRENTlist['t_s'] = [self.time_stampI+i for i in range(len(data[0]))]
                    self.time_stampI = self.time_stampI + 1
                    #print(" ... VisulizerWSrcv:",data)
                    doc.add_next_tick_callback(partial(self.updateCURRENT, self.CURRENTlist))
                except:
                    self.IOloop_data_run = False



##############################################################################
# potentiostat module class
##############################################################################
class C_potvis:
    def __init__(self, config):
        self.config = config
        self.data_url = config['wsdata_url']
        self.stat_url = config['wsstat_url']

##############################################################################
# data module class
##############################################################################
class C_datavis:
    def __init__(self, config):
        self.config = config
        self.data_url = config['wsdata_url']
        self.stat_url = config['wsstat_url']
        self.data = dict()
        # buffered version
        self.dataold = copy.deepcopy(self.data)
        
        
    async def IOloop_data(self): # non-blocking coroutine, updates data source
        async with websockets.connect(self.data_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    self.data =  await ws.recv()
                    print(" ... VisulizerWSrcv: pm data")
                except:
                    self.IOloop_data_run = False


##############################################################################
# update loop for visualizer document
##############################################################################
async def IOloop_visualizer():
    # update if motor is present
    if datavis:
        if datavis.data:
            # update only if changed
            if not datavis.data == datavis.dataold:
                datavis.dataold = copy.deepcopy(datavis.data)
                pmdata = json.loads(datavis.data)['map']
                # plot only if motorvis is active
                if motorvis:
                    x = [col['x'] for col in pmdata]
                    y = [col['y'] for col in pmdata]
                    # remove old Pmplot
                    old_point = motorvis.plot_motor.select(name="PMplot")
                    if len(old_point)>0:
                        motorvis.plot_motor.renderers.remove(old_point[0])
                    motorvis.plot_motor.square(x, y, size=5, color=None, alpha=0.5, line_color='black',name="PMplot")

            
    if motorvis:
        MarkerColors = [(255,0,0),(0,0,255),(0,255,0),(255,165,0),(255,105,180)]
        if motorvis.data:
            # update only if changed
            if not motorvis.data == motorvis.dataold:
                motorvis.dataold = copy.deepcopy(motorvis.data)
                tmpmotordata = json.loads(motorvis.data)                
                for idx in range(len(motorvis.axisvaldisp)):
                    motorvis.axisvaldisp[idx].value = (str)(tmpmotordata['position'][idx])
                    motorvis.axisstatdisp[idx].value = (str)(tmpmotordata['motor_status'][idx])
                    motorvis.axiserrdisp[idx].value = (str)(tmpmotordata['err_code'][idx])
                # check if x and y motor is present and plot it
                pangle = 0.0
                if 's' in tmpmotordata['axis']:
                    pangle = tmpmotordata['position'][tmpmotordata['axis'].index('s')]
                    pangle = math.pi/180.0*pangle
#                if 'x' in tmpmotordata['axis'] and 'y' in tmpmotordata['axis']:
#                    ptx = tmpmotordata['position'][tmpmotordata['axis'].index('x')]
#                    pty = tmpmotordata['position'][tmpmotordata['axis'].index('y')]
                if 'PlateXY' in tmpmotordata:
                    ptx = tmpmotordata['PlateXY'][0]
                    pty = tmpmotordata['PlateXY'][1]
                    
                    # update plot
                    old_point = motorvis.plot_motor.select(name='motor_xy')
                    if len(old_point)>0:
                        for oldpoint in old_point:
                            motorvis.plot_motor.renderers.remove(oldpoint)

                    motorvis.plot_motor.rect(6.0*25.4/2,  4.0*25.4/2.0, width = 6.0*25.4, height = 4.0*25.4, angle = 0.0, angle_units='rad', fill_alpha=0.0, fill_color='gray', line_width=2, alpha=1.0, line_color=(0,0,0), name='motor_xy')
                    # plot new Marker point
                    if S.params.ws_motor_params.sample_marker_type == 0:
                        # standard square marker
                        motorvis.plot_motor.square(ptx, pty, size=7,line_width=2, color=None, alpha=1.0, line_color=MarkerColors[0], name='motor_xy')

                    elif S.params.ws_motor_params.sample_marker_type == 1: # RSHS
                        # marker symbold for ANEC2, need exact dimensions for final marker
                        sample_size = 5
                        sample_spacing = 0.425*25.4
                        sample_count = 9;
                        # the square box
                        motorvis.plot_motor.rect(ptx, pty, width = sample_size+10, height = (sample_count-1)*sample_spacing+10, angle = -1.0*pangle, angle_units='rad', fill_alpha=0.0, fill_color='gray', line_width=2, alpha=1.0, line_color=(255,0,0), name='motor_xy')
                        # and the different sample circles
                        motorvis.plot_motor.ellipse(ptx, pty, width = sample_size, height = sample_size, fill_alpha=0.0, fill_color=None, line_width=2, alpha=1.0, line_color=(0,0,255), name='motor_xy')
                        for i in range(1,(int)((sample_count-1)/2)+1):
                            motorvis.plot_motor.ellipse(ptx+i*sample_spacing*math.sin(pangle), pty+i*sample_spacing*math.cos(pangle), width = sample_size, height = sample_size, fill_alpha=0.0, fill_color='gray', line_width=2, alpha=1.0, line_color=(255,0,0), name='motor_xy')
                            motorvis.plot_motor.ellipse(ptx-i*sample_spacing*math.sin(pangle), pty-i*sample_spacing*math.cos(pangle), width = sample_size, height = sample_size, fill_alpha=0.0, fill_color='gray', line_width=2, alpha=1.0, line_color=(255,0,0), name='motor_xy')


##############################################################################
# MAIN
##############################################################################

doc = curdoc()
if 'doc_name' in S.params:
    doc.title = S.params['doc_name']
else:
    doc.title = "Modular Visualizer"

# create config for defined instrument 
potserv = dict()
motorserv = dict()
dataserv = dict()
NImaxserv = dict()

if 'ws_potentiostat' in S.params:
    tmpserv = S.params.ws_potentiostat
    potserv['serv'] = tmpserv
    potserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data"
    potserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"

if 'ws_data' in S.params:
    tmpserv = S.params.ws_data
    dataserv['serv'] = tmpserv
    dataserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data"
    dataserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
        
if 'ws_motor' in S.params:    
    tmpserv = S.params.ws_motor
    motorserv['serv'] = tmpserv
    motorserv['params']  = S.params.ws_motor_params
    motorserv['axis_id'] = C[tmpserv].params.axis_id
    motorserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_motordata"
    motorserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
    if not 'sample_marker_type' in S.params.ws_motor_params:
        S.params.ws_motor_params.sample_marker_type = 0



if 'ws_nidaqmx' in S.params:
    tmpserv = S.params.ws_nidaqmx
    NImaxserv['serv'] = tmpserv
    NImaxserv['wsdataVOLT_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data_VOLT"
    NImaxserv['wsdataCURRENT_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data_CURRENT"
    NImaxserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"

        
# create visualizer objects for defined instruments
if motorserv:
    print(f"Create Visualizer for {motorserv['serv']}")
    motorvis = C_motorvis(motorserv)
else:
    print('No motor visualizer configured')
    motorvis = []

if potserv:
    print(f"Create Visualizer for {potserv['serv']}")
    potvis = C_potvis(potserv)
else:
    print('No potentiostat visualizer configured')
    potvis = []

if dataserv:
    print(f"Create Visualizer for {dataserv['serv']}")
    datavis = C_datavis(dataserv)
else:
    print('No data visualizer configured')
    datavis = []

if NImaxserv:
    print(f"Create Visualizer for {NImaxserv['serv']}")
    NImaxvis = C_nidaqmxvis(NImaxserv)
else:
    print('No NImax visualizer configured')
    NImaxvis = []
    

# is there any better way to inlcude external CSS? 
css_styles = Div(text="""<style>%s</style>""" % pathlib.Path(os.path.join(helao_root, 'visualizer\styles.css')).read_text())

doc.add_root(css_styles)

visoloop = asyncio.get_event_loop()
# websockets loops
if motorvis:
    doc.add_root(layout([motorvis.layout]))
    visoloop.create_task(motorvis.IOloop_data())

if datavis:
    visoloop.create_task(datavis.IOloop_data())
    
if NImaxvis:
    doc.add_root(layout([NImaxvis.layout]))
    visoloop.create_task(NImaxvis.IOloop_dataVOLT())
    visoloop.create_task(NImaxvis.IOloop_dataCURRENT())
    

# web interface update loop
doc.add_periodic_callback(IOloop_visualizer,500) # time in ms
