
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
                except Exception:
                    self.IOloop_data_run = False


##############################################################################
# potentiostat module class
##############################################################################
class C_nidaqmxvis:
    def __init__(self, config):
        self.config = config

        self.config = config
        self.data_url = config['wsdata_url']
        self.stat_url = config['wsstat_url']
        self.dataset_url = config['wsdataset_url']
        self.IOloop_data_run = False
        self.IOloop_dataset_run = False

        self.time_stamp = 0
        self.IVlist = {}
        self.activeCell = [False for _ in range(9)]

        self.sourceIV = ColumnDataSource(data=dict(t_s=[],
                                                     ICell_1=[],
                                                     ICell_2=[],
                                                     ICell_3=[],
                                                     ICell_4=[],
                                                     ICell_5=[],
                                                     ICell_6=[],
                                                     ICell_7=[],
                                                     ICell_8=[],
                                                     ICell_9=[],
                                                     VCell_1=[],
                                                     VCell_2=[],
                                                     VCell_3=[],
                                                     VCell_4=[],
                                                     VCell_5=[],
                                                     VCell_6=[],
                                                     VCell_7=[],
                                                     VCell_8=[],
                                                     VCell_9=[]))

        # create visual elements
        self.layout = []
        self.plot_VOLT = figure(title="CELL VOLTs", height=300)
        self.plot_CURRENT = figure(title="CELL CURRENTs", height=300)

        self.reset_plot()

        # combine all sublayouts into a single one
        self.layout = layout([
            [Spacer(width=20), Div(text="<b>NImax Visualizer module</b>", width=200+50, height=15)],
            layout([self.plot_VOLT]),
            Spacer(height=10),
            layout([self.plot_CURRENT]),
            Spacer(height=10)
            ],background="#C0C0C0")


    def add_points(self, new_data):
        self.sourceIV.data = {k: [] for k in self.sourceIV.data}
        self.sourceIV.stream(new_data)


    async def IOloop_data(self): # non-blocking coroutine, updates data source
        global doc
        async with websockets.connect(self.data_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    data = json.loads(await ws.recv())
                    self.IVlist = {'t_s':data['t_s']}
                    for cell in range(9): # nine cells, but len(data['t_s']) datapoints for each cell
                        self.IVlist[f"ICell_{cell+1}"] = data['I_A'][cell]
                        self.IVlist[f"VCell_{cell+1}"] = data['E_V'][cell]
                    doc.add_next_tick_callback(partial(self.add_points, self.IVlist))
                except Exception:
                    self.IOloop_data_run = False


    async def IOloop_datasettings(self): # non-blocking coroutine, updates data source
        global doc
        async with websockets.connect(self.dataset_url) as ws:
            self.IOloop_dataset_run = True
            while self.IOloop_dataset_run:
                try:
                    data = json.loads(await ws.recv())
                    if 'activeCell' in data:
                        self.activeCell = data['activeCell']
                        doc.add_next_tick_callback(partial(self.reset_plot))
                except Exception:
                    self.IOloop_dataset_run = False


    def reset_plot(self):
        global doc
        # remove all old lines and clear legend
        if self.plot_VOLT.renderers:
            self.plot_VOLT.legend.items = []

        if self.plot_CURRENT.renderers:
            self.plot_CURRENT.legend.items = []
            
        self.plot_VOLT.renderers = []
        self.plot_CURRENT.renderers = []
        
        colors = small_palettes['Category10'][9]
        for i,val in enumerate(self.activeCell):
            # only plot active cells
            if val:
                _ = self.plot_VOLT.line(x='t_s', y=f'VCell_{i+1}', source=self.sourceIV, name=f'VCell{i+1}', line_color=colors[i], legend_label=f'VCell{i+1}')
                _ = self.plot_CURRENT.line(x='t_s', y=f'ICell_{i+1}', source=self.sourceIV, name=f'ICell{i+1}', line_color=colors[i], legend_label=f'ICell{i+1}')

##############################################################################
# potentiostat module class
##############################################################################
class C_potvis:
    def __init__(self, config):
        self.config = config
        self.data_url = config['wsdata_url']
        self.stat_url = config['wsstat_url']

        self.IOloop_data_run = False
        self.IOloop_stat_run = False

        self.datasource = ColumnDataSource(data=dict(pt=[], t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))
        self.time_stamp = 0
#        self.pids = collections.deque(10*[0], 10)

        # create visual elements
        self.layout = []


        self.paragraph1 = Paragraph(text="""x-axis:""", width=50, height=15)
        self.radio_button_group = RadioButtonGroup(labels=["t_s", "Ewe_V", "Ach_V", "I_A"], active=1)
        self.paragraph2 = Paragraph(text="""y-axis:""", width=50, height=15)
        self.checkbox_button_group = CheckboxButtonGroup(labels=["t_s", "Ewe_V", "Ach_V", "I_A"], active=[3])
        
        self.plot = figure(title="Title", height=300)
        self.line1 = self.plot.line(x='t_s', y='Ewe_V', source=self.datasource, name=str(self.time_stamp))


#        self.pid_list = dict(
#            pids=[self.pids[i] for i in range(10)],
#        )
#        self.pid_source = ColumnDataSource(data=self.pid_list)
#        self.columns = [
#            TableColumn(field="pids", title="PIDs"),
#        ]
#        self.data_table = DataTable(source=self.pid_source, columns=self.columns, width=400, height=280)


        # combine all sublayouts into a single one
        self.layout = layout([
            [Spacer(width=20), Div(text="<b>Potentiostat Visualizer module</b>", width=200+50, height=15)],
            layout([self.paragraph1]),
            layout([self.radio_button_group]),
            layout([self.paragraph2]),
            layout([self.checkbox_button_group]),
            Spacer(height=10),
            layout([self.plot]),
#            Spacer(height=10),
#            layout([self.data_table]),
            Spacer(height=10)
            ],background="#C0C0C0")

        # to check if selection changed during ploting
        self.xselect = self.radio_button_group.active
        self.yselect = self.checkbox_button_group.active



    def add_points(self, new_data):
        # detect if plot selection changed
        if  (self.xselect != self.radio_button_group.active) or (self.yselect != self.checkbox_button_group.active):
            self.xselect = self.radio_button_group.active
            self.yselect = self.checkbox_button_group.active
            # use current(old) timestamp but force update via optional
            # second parameter
            self.reset_plot(self.time_stamp, True)
        
        
        tmpdata = {'pt':[0]}
        # for some techniques not all data is present
        # we should only get one data point at the time
        if 't_s' in new_data:
            tmpdata['t_s'] = new_data['t_s']
        else:
            tmpdata['t_s'] = [0]
        if 'Ewe_V' in new_data:
            tmpdata['Ewe_V'] = new_data['Ewe_V']
        else:
            tmpdata['Ewe_V'] = [0]
        if 'Ach_V' in new_data:
            tmpdata['Ach_V'] = new_data['Ach_V']
        else:
            tmpdata['Ach_V'] = [0]
        if 'I_A' in new_data:
            tmpdata['I_A'] = new_data['I_A']
        else:
            tmpdata['I_A'] = [0]
        self.datasource.stream(tmpdata)
        
        # self.datasource.stream({"t_s":new_data["t_s"],
        #                         "Ewe_V":new_data["Ewe_V"],
        #                         "Ach_V":new_data["Ach_V"],
        #                         "I_A":new_data["I_A"]})

    async def IOloop_data(self): # non-blocking coroutine, updates data source
        global doc
        async with websockets.connect(self.data_url) as ws:
            self.IOloop_data_run = True
            while self.IOloop_data_run:
                try:
                    new_data = json.loads(await ws.recv())
                    if new_data is not None:
                        doc.add_next_tick_callback(partial(self.add_points, new_data))
                except Exception:
                    self.IOloop_data_run = False


    async def IOloop_stat(self):
        global doc
        async with websockets.connect(self.stat_url) as sws:
            self.IOloop_stat_run = True
            while self.IOloop_stat_run:
                try:
                    new_status = await sws.recv()
                    new_status = json.loads(new_status)
                    # only reset graph at the beginning of a measurement and 
                    # not at every status change
                    if new_status is not None and new_status['status'] == 'running':
                        doc.add_next_tick_callback(partial(self.reset_plot, new_status['last_update']))
                except Exception:
                    self.IOloop_stat_run = False

    
    def reset_plot(self, new_time_stamp, forceupdate: bool = False):
        global doc
        if (new_time_stamp != self.time_stamp) or forceupdate:
            print(' ... reseting Gamry graph')
            self.time_stamp = new_time_stamp
        
            self.datasource.data = {k: [] for k in self.datasource.data}
    
    #        self.pid_source.data = {k: [] for k in self.pid_source.data}
    #        self.pids.appendleft(new_time_stamp)
    #        self.pid_list = dict(
    #            pids=[self.pids[i] for i in range(10)],
    #        )
    #        self.pid_source.stream(self.pid_list)
    
            
            # remove all old lines
            self.plot.renderers = []
    
            
            self.plot.title.text = ("Timecode: "+str(new_time_stamp))
            xstr = ''
            if(self.radio_button_group.active == 0):
                xstr = 't_s'
            elif(self.radio_button_group.active == 1):
                xstr = 'Ewe_V'
            elif(self.radio_button_group.active == 2):
                xstr = 'Ach_V'
            else:
                xstr = 'I_A'
            colors = ['red', 'blue', 'yellow', 'green']
            color_count = 0
            for i in self.checkbox_button_group.active:
                if i == 0:
                    self.plot.line(x=xstr, y='t_s', line_color=colors[color_count], source=self.datasource, name=str(self.time_stamp))
                elif i == 1:
                    self.plot.line(x=xstr, y='Ewe_V', line_color=colors[color_count], source=self.datasource, name=str(self.time_stamp))
                elif i == 2:
                    self.plot.line(x=xstr, y='Ach_V', line_color=colors[color_count], source=self.datasource, name=str(self.time_stamp))
                else:
                    self.plot.line(x=xstr, y='I_A', line_color=colors[color_count], source=self.datasource, name=str(self.time_stamp))
                color_count += 1
   


##############################################################################
# job queue module class
# for visualizing the content of the orch queue (with params), just a simple table
# TODO: work in progress
##############################################################################
class C_jobvis:
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
                except Exception:
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
                    pangle = math.pi/180.0*pangle # TODO
#                if 'x' in tmpmotordata['axis'] and 'y' in tmpmotordata['axis']:
#                    ptx = tmpmotordata['position'][tmpmotordata['axis'].index('x')]
#                    pty = tmpmotordata['position'][tmpmotordata['axis'].index('y')]
                if 'platexy' in tmpmotordata:
                    ptx = tmpmotordata['platexy'][0]
                    pty = tmpmotordata['platexy'][1]
                    
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

# is there any better way to inlcude external CSS? 
css_styles = Div(text="""<style>%s</style>""" % pathlib.Path(os.path.join(helao_root, 'visualizer\styles.css')).read_text())

doc.add_root(css_styles)

visoloop = asyncio.get_event_loop()



# create config for defined instrument 
potserv = dict()
motorserv = dict()
dataserv = dict()
NImaxserv = dict()

# create visualizer objects for defined instruments
if 'ws_potentiostat' in S.params:
    tmpserv = S.params.ws_potentiostat
    potserv['serv'] = tmpserv
    potserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data"
    potserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
    print(f"Create Visualizer for {potserv['serv']}")
    potvis = C_potvis(potserv)
    doc.add_root(layout([potvis.layout]))
    doc.add_root(layout(Spacer(height=10)))
    visoloop.create_task(potvis.IOloop_data())
    visoloop.create_task(potvis.IOloop_stat())
else:
    print('No potentiostat visualizer configured')
    potvis = []


if 'ws_data' in S.params:
    tmpserv = S.params.ws_data
    dataserv['serv'] = tmpserv
    dataserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data"
    dataserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
    print(f"Create Visualizer for {dataserv['serv']}")
    datavis = C_datavis(dataserv)
    visoloop.create_task(datavis.IOloop_data())
else:
    print('No data visualizer configured')
    datavis = []


if 'ws_motor' in S.params:    
    tmpserv = S.params.ws_motor
    motorserv['serv'] = tmpserv
    motorserv['params']  = S.params.ws_motor_params
    motorserv['axis_id'] = C[tmpserv].params.axis_id
    motorserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_motordata"
    motorserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
    if not 'sample_marker_type' in S.params.ws_motor_params:
        S.params.ws_motor_params.sample_marker_type = 0
    print(f"Create Visualizer for {motorserv['serv']}")
    motorvis = C_motorvis(motorserv)
    doc.add_root(layout([motorvis.layout]))
    doc.add_root(layout(Spacer(height=10)))
    visoloop.create_task(motorvis.IOloop_data())
else:
    print('No motor visualizer configured')
    motorvis = []


if 'ws_nidaqmx' in S.params:
    tmpserv = S.params.ws_nidaqmx
    NImaxserv['serv'] = tmpserv
    NImaxserv['wsdata_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data"
    NImaxserv['wsdataset_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_data_settings"
    NImaxserv['wsstat_url'] = f"ws://{C[tmpserv].host}:{C[tmpserv].port}/{tmpserv}/ws_status"
    print(f"Create Visualizer for {NImaxserv['serv']}")
    NImaxvis = C_nidaqmxvis(NImaxserv)
    doc.add_root(layout([NImaxvis.layout]))
    doc.add_root(layout(Spacer(height=10)))
    visoloop.create_task(NImaxvis.IOloop_data())
    visoloop.create_task(NImaxvis.IOloop_datasettings())
else:
    print('No NImax visualizer configured')
    NImaxvis = []


# web interface update loop
# todo put his in the respective classes?
doc.add_periodic_callback(IOloop_visualizer,500) # time in ms
