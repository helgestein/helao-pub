
import os
import sys
import websockets
import asyncio
import json
import collections
from functools import partial
from importlib import import_module
from functools import partial

import aiohttp
from collections import deque

from bokeh.layouts import column

from bokeh.models import FileInput


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
from bokeh.io import show
from bokeh.models import CustomJS, Dropdown
from bokeh.models import Select
from bokeh.events import MenuItemClick
from bokeh.events import ButtonClick, DoubleTap
from bokeh.models import Button, TextAreaInput, TextInput


from bokeh.models import TextInput
from bokeh.models.widgets import Div
from bokeh.layouts import layout, Spacer
import pathlib
import copy
import math
import io
from pybase64 import b64decode
import numpy as np


import requests
from functools import partial


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))
#from classes import StatusHandler
from classes import OrchHandler, Decision, Action, getuid


confPrefix = sys.argv[1] # the name of the config file
servKey = sys.argv[2] # the server key of this script defined in config (i.e. servKey=dict(..)
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"] # get the config defined in config file under dict config["servers"]
S = C[servKey] # the config for this particular server/script in config file



# Multiple action libraries may be specified in the config, and all actualizers will be
# imported into the action_lib dictionary. When importing more than one action library,
# take care that actualizer function names do not conflict.
action_lib = {}
sys.path.append(os.path.join(helao_root, "library"))
for actlib in config["action_libraries"]:
    tempd = import_module(actlib).__dict__
    action_lib.update({func: tempd[func] for func in tempd["ACTUALIZERS"]})


##############################################################################
# Operator class
##############################################################################

class C_async_operator:
    def __init__(self, S_config, C_config):
        self.S_config = S_config
        self.C_config = C_config
        
        self.orch = self.C_config[self.S_config.params.orch]
#        self.data_server = self.C_config[self.S_config.params.data_server]
        
        
        self.dataserv = self.S_config.params.data_server
        self.datahost = self.C_config[self.S_config.params.data_server].host
        self.dataport = self.C_config[self.S_config.params.data_server].port
        
        self.pmdata = []
        
        # if 'servicemode' not in self.S_config.params:           
        #     self.servicemode = False
        # else:
        self.servicemode = self.S_config.params.get('servicemode', False)
        # self.service_loop_run = False

        # # for service mode orch operator
        # self.oporch = OrchHandler(C_config)
        # if self.servicemode:
        #     self.oporch.monitor_states()


        # self.data_url = config['wsdata_url']
        # self.stat_url = config['wsstat_url']

        # holds the page layout
        self.layout = []
        self.param_layout = []
        # self.param_text = []
        self.param_input = []

        self.decision_list = dict()
        self.action_list = dict()

        self.act_select_list = []
        self.actualizers = []

        # FastAPI calls
        self.get_actualizers()
        self.get_decisions()
        self.get_actions()


        #print([key for key in self.decision_list.keys()])
        self.decision_source = ColumnDataSource(data=self.decision_list)
        self.columns_dec = [TableColumn(field=key, title=key) for key in self.decision_list.keys()]
        self.decision_table = DataTable(source=self.decision_source, columns=self.columns_dec, width=620, height=200)

        self.action_source = ColumnDataSource(data=self.action_list)
        self.columns_act = [TableColumn(field=key, title=key) for key in self.action_list.keys()]
        self.action_table = DataTable(source=self.action_source, columns=self.columns_act, width=620, height=200)




        self.actions_dropdown = Select(title="Select actualizer:", value = None, options=self.act_select_list)
        self.actions_dropdown.on_change('value', self.callback_act_select)

        self.button_load_sample_list = FileInput(accept=".csv,.txt", width = 300)
        self.button_load_sample_list.on_change('value', self.get_sample_list)


        # buttons to control orch
        self.button_start = Button(label="Start", button_type="default", width=70)
        self.button_start.on_event(ButtonClick, self.callback_start)
        self.button_stop = Button(label="Stop", button_type="default", width=70)
        self.button_stop.on_event(ButtonClick, self.callback_stop)
        self.button_skip = Button(label="Skip", button_type="danger", width=70)
        self.button_skip.on_event(ButtonClick, self.callback_skip_dec)

        self.button_clear_dec = Button(label="clear decisions", button_type="danger", width=100)
        self.button_clear_dec.on_event(ButtonClick, self.callback_clear_decisions)
        self.button_clear_act = Button(label="clear actions", button_type="danger", width=100)
        self.button_clear_act.on_event(ButtonClick, self.callback_clear_actions)

        self.button_prepend = Button(label="prepend", button_type="default", width=150)
        self.button_prepend.on_event(ButtonClick, self.callback_prepend)
        self.button_append = Button(label="append", button_type="default", width=150)
        self.button_append.on_event(ButtonClick, self.callback_append)


        # service mode elements
        self.button_service_run = Button(label="Run", button_type="danger", width=70)
        self.button_service_run.on_event(ButtonClick, self.callback_sericemode_run)
        self.button_service_stop = Button(label="Stop", button_type="danger", width=70)
        self.button_service_stop.on_event(ButtonClick, self.callback_sericemode_stop)
        # service mode elements end
        



        self.act_descr_txt = Paragraph(text="""select item""", width=600, height=30)


        self.input_sampleno = TextInput(value="", title="sample no", disabled=False, width=330, height=40)
        self.input_plateid = TextInput(value="", title="plate id", disabled=False, width=60, height=40)
        self.input_plateid.on_change('value', self.callback_changed_plateid)
        self.input_label = TextInput(value="nolabel", title="label", disabled=False, width=120, height=40)

        self.input_elements = TextInput(value="", title="elements", disabled=False, width=120, height=40)
        self.input_code = TextInput(value="", title="code", disabled=False, width=60, height=40)
        self.input_composition = TextInput(value="", title="composition", disabled=False, width=220, height=40)



        self.plot_mpmap = figure(title="PlateMap", height=300,x_axis_label='X (mm)', y_axis_label='Y (mm)',width = 640)
        #taptool = plot_mpmap.select(type=TapTool)
        self.plot_mpmap.on_event(DoubleTap, self.callback_clicked_pmplot)



        if self.servicemode:
            print(' ... service mode activated for operator!')
            self.layout_servicemode = layout([
                [Spacer(width=20), Div(text="<b>Service Menu</b>", width=200+50, height=15, style={'font-size': '150%', 'color': 'red'})],
                [self.button_service_run,self.button_service_stop],
                ])            
        else:
            self.layout_servicemode = layout([])



        self.layout0 = layout([
            layout(
                [Spacer(width=20), Div(text=f"<b>{S_config.params.doc_name}</b>", width=200+50, height=15, style={'font-size': '200%', 'color': 'red'})],
                background="#C0C0C0",width=640),
            layout([
                [self.actions_dropdown],
                [Spacer(width=10), Div(text="<b>Actualizer description:</b>", width=200+50, height=15)],
                [self.act_descr_txt],
                Spacer(height=10),
                Spacer(height=10),
                ],background="#808080",width=640),
            layout([
                [Paragraph(text="""Load sample list from file:""", width=600, height=30)],
                [self.button_load_sample_list],
                [self.input_plateid, self.input_sampleno],
                [self.input_elements, self.input_code, self.input_composition],
                [self.input_label],
                Spacer(height=10),
                [self.plot_mpmap],
                Spacer(height=10),
                ]),
            ])


        self.layout2 = layout([
                layout([self.layout_servicemode],background="#E0E0E0",width=640),
                layout([
                    [self.button_append, self.button_prepend, self.button_start, self.button_stop],
                    ]),
                layout([
                [Spacer(width=20), Div(text="<b>Decisions:</b>", width=200+50, height=15)],
                [self.decision_table],
                [Spacer(width=20), Div(text="<b>Actions:</b>", width=200+50, height=15)],
                [self.action_table],
                Spacer(height=10),
                [self.button_skip, Spacer(width=5), self.button_clear_dec, Spacer(width=5), self.button_clear_act],
                Spacer(height=10),
                ],background="#7fdbff",width=640),
            ])




    def get_actualizers(self):
        '''get all available actualizers to populate later functions'''
        response = self.do_orch_request('list_actualizers')
        self.actualizers = json.loads(response)["actualizers"]
        
        for item in self.actualizers:
            self.act_select_list.append(item['action'])
            #print('##',item)
        
        #global actualizer_name_Enum
        
        #actualizer_name_Enum = Enum('actualizer_name_Enum', {item['action']:item['action'] for item in actualizeritems})
        #print(list(actualizer_name_Enum))


    def get_decisions(self):
        '''get decision list from orch'''
        response = json.loads(self.do_orch_request('list_decisions'))['decisions']
        self.decision_list = dict()
        if len(response):
            for key in response[0].keys():
                self.decision_list[key] = []
            for line in response:
                for key, value in line.items():
                    self.decision_list[key].append(value)
        print(' ... current active decisions:',self.decision_list)


    def get_actions(self):
        '''get action list from orch'''
        response = json.loads(self.do_orch_request('list_actions'))['actions']
        self.action_list = dict()
        if len(response):
            for key in response[0].keys():
                self.action_list[key] = []
        print(' ... current active actions:',self.action_list)


    def do_orch_request(self,item, itemparams: dict = {}):
        '''submit a FastAPI request to orch'''
        url = f"http://{self.orch.host}:{self.orch.port}/{self.S_config.params.orch}/{item}"
        with requests.Session() as session:
            with session.post(url, params=itemparams) as resp:
                response = resp.text
                print(response)
                return response
                #actualizeritems = json.loads(response)["actualizers"]
                #print(actualizeritems)


    def callback_act_select(self, attr, old, new):
        print(attr, old, new)
        idx = self.act_select_list.index(new)
        act_doc = self.actualizers[idx]['doc']
        for arg in self.actualizers[idx]['args']:
            print(arg)

        self.update_param_layout(self.actualizers[idx]['args'], self.actualizers[idx]['defaults'])

        operator_doc.add_next_tick_callback(partial(self.update_doc,act_doc))


    def callback_clicked_pmplot(self, event):
        '''double click/tap on PM plot to add/move marker'''
        #global calib_sel_motor_loc_marker
        #global pmdata
        print("DOUBLE TAP PMplot")
        print(event.x, event.y)
        # get selected Marker
     #   selMarker = MarkerNames.index(calib_sel_motor_loc_marker.value)
        # get coordinates of doubleclick
        platex = event.x
        platey = event.y
        # transform to nearest sample point
        PMnum = self.get_samples([platex], [platey])
        buf = ""
        if PMnum is not None:
            if PMnum[0] is not None: # need to check as this can also happen
                print(' ... selected sampleid:', PMnum[0])
                platex = self.pmdata[PMnum[0]]['x']
                platey = self.pmdata[PMnum[0]]['y']
                code = self.pmdata[PMnum[0]]["code"]
                #MarkerXYplate[selMarker] = (platex,platey,1)
                #MarkerSample[selMarker] = pmdata[PMnum[0]]["Sample"]
                #MarkerIndex[selMarker] = PMnum[0]
                #MarkerCode[selMarker] = pmdata[PMnum[0]]["code"]
        
                # only display non zero fractions
                buf = ""
                # TODO: test on other platemap
                for fraclet in ("A", "B", "C", "D", "E", "F", "G", "H"):
                    # if self.pmdata[PMnum[0]][fraclet] > 0:
#                    buf = "%s%s%d " % (buf,fraclet, self.pmdata[PMnum[0]][fraclet]*100)
                    buf = "%s%s_%s " % (buf,fraclet, self.pmdata[PMnum[0]][fraclet])
                if len(buf) == 0:
                    buf = "-"
                operator_doc.add_next_tick_callback(partial(self.update_samples,str(PMnum[0])))
                operator_doc.add_next_tick_callback(partial(self.update_xysamples,str(platex), str(platey)))
                operator_doc.add_next_tick_callback(partial(self.update_composition,buf))
                operator_doc.add_next_tick_callback(partial(self.update_code,str(code)))




                #MarkerFraction[selMarker] = buf
        ##    elif:
                # remove old Marker point
                old_point = self.plot_mpmap.select(name='selsample')
                if len(old_point)>0:
                    self.plot_mpmap.renderers.remove(old_point[0])
                # plot new Marker point
                self.plot_mpmap.square(platex, platey, size=7,line_width=2, color=None, alpha=1.0, line_color=(255,0,0), name='selsample')
        # add Marker positions to list
        #update_Markerdisplay(selMarker)
        #

    def callback_changed_plateid(self, attr, old, new):
        print(attr, old, new)
        asyncio.gather(self.get_pm(new))
        asyncio.gather(self.get_elements_plateid(new))


    def callback_start(self, event):
        print(' ... starting orch')
        response = self.do_orch_request('start')
        print(' ... orch start response:', response)


    def callback_stop(self, event):
        print(' ... stopping operator orch')
        response = self.do_orch_request('stop')
        print(' ... orch stop response:', response)


    def callback_skip_dec(self, event):
        print(' ... skipping decision')
        response = self.do_orch_request('skip')
        print(' ... orch response:', response)


    def callback_clear_decisions(self, event):
        print(' ... clearing decisions')
        response = self.do_orch_request('clear_decisions')
        print(' ... orch response:', response)


    def callback_clear_actions(self, event):
        print(' ... clearing actions')
        response = self.do_orch_request('clear_actions')
        print(' ... orch response:', response)


    def callback_prepend(self, event):
        self.prepend_action()
        operator_doc.add_next_tick_callback(partial(self.update_tables))



    def callback_append(self, event):
        self.append_action()
        operator_doc.add_next_tick_callback(partial(self.update_tables))


    def append_action(self):
        params = self.populate_action()
        # submit decission to orchestrator
        response = self.do_orch_request('append_decision',params)
        return response

    def prepend_action(self):
        params = self.populate_action()
        # submit decission to orchestrator
        response = self.do_orch_request('prepend_decision',params)
        return response


    def populate_action(self):
        selaction = self.actions_dropdown.value
        selplateid = self.input_plateid.value
        selsample = self.input_sampleno.value
        sellabel = self.input_label.value
        elements = self.input_elements.value
        code  = self.input_code.value
        composition = self.input_composition.value


        print(' ... selected action from list:', selaction)
        print(' ... selected plateid:', selplateid)
        print(' ... selected sample:', selsample)
        print(' ... selected label:', sellabel)

        actparams = []
        for paraminput in self.param_input:
            actparams.append(str(paraminput.value))
            print(' ... aditional action param:',paraminput.value)

        newuid = getuid('operator')
        params = {'uid':f'{newuid}',
             'plate_id':f'{selplateid}', 
             'sample_no':f'{selsample}', 
             'label':f'{sellabel}', 
             'elements':f'{elements}',
             'code':f'{code}',
             'sample_x':'',
             'sample_y':'',
             'composition':f'{composition}',
             'actualizer':f'{selaction}',
             'actparams':json.dumps(actparams)}
        return params




    def callback_sericemode_run(self, event):
        print(' ... starting operator orch')
        self.append_action()

        # start the orchestrator
        response = self.do_orch_request('start')
        print(' ... orch start response:', response)



    def callback_sericemode_stop(self, event):
        print('##############################################################')
        print(' ... stopping orch')
        response = self.do_orch_request('stop')
        print(' ... orch stop response:', response)


    def update_param_layout(self, args, defaults):
        global dynamic_col
        if len(dynamic_col.children)>2:
            dynamic_col.children.pop(1)

        for _ in range(len(args)-len(defaults)):
            defaults.insert(0,"")

        # self.param_text = []
        self.param_input = []
        # self.input_samplelist = TextInput(value="", title="sample no", disabled=False, width=330, height=40)
        # self.param_input.append(TextInput(value="", title="plate id", disabled=False, width=60, height=40))
        # self.param_input.append(self.input_samplelist)
        self.param_layout = []
        # self.param_layout.append(layout([
        #             [self.param_input[0], self.param_input[1]],
        #             Spacer(height=10),
        #             ]))
        
        item = 0
        # self.param_input.append(TextInput(value="", title="sample no" disabled=False, width=60, height=40))
        for idx in range(len(args)):
            buf = f'{defaults[idx]}'
            print(' ... action parameter:',args[idx])
            # skip the decisionObj parameter
            if args[idx] == 'decisionObj':
                continue

            # self.param_text.append(Paragraph(text=arg, width=120, height=15))
            self.param_input.append(TextInput(value=buf, title=args[idx], disabled=False, width=400, height=40))
            self.param_layout.append(layout([
                        [self.param_input[item]],
                        Spacer(height=10),
                        ]))
            item = item + 1

        dynamic_col.children.insert(-1, layout(self.param_layout))


    def update_doc(self, value):
        self.act_descr_txt.text = value


    def update_samples(self, value):
        self.input_sampleno.value = value


    def update_xysamples(self, xval, yval):
        for paraminput in self.param_input:
            if paraminput.title == 'x_mm':
                paraminput.value = xval
            if paraminput.title == 'y_mm':
                paraminput.value = yval


        # self.input_sampleno.value = value


    def update_pm_plot(self):
        '''plots the plate map'''
        #global pmdata
        x = [col['x'] for col in self.pmdata]
        y = [col['y'] for col in self.pmdata]
        # remove old Pmplot
        old_point = self.plot_mpmap.select(name="PMplot")
        if len(old_point)>0:
            self.plot_mpmap.renderers.remove(old_point[0])
        self.plot_mpmap.square(x, y, size=5, color=None, alpha=0.5, line_color='black',name="PMplot")


    async def get_elements_plateid(self, plateid: int):
        '''gets plate elements from aligner server'''

        #plateid = '4534'
        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_elements_plateid"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'plateid':plateid}) as resp:
                response = await resp.json()
                print(response)
                elements = response['data']['elements']
                operator_doc.add_next_tick_callback(partial(self.update_elements, elements))

        
    def update_elements(self, elements):
        self.input_elements.value = ','.join(elements) 

        
    def update_composition(self, composition):
        self.input_composition.value = composition

        
    def update_code(self, code):
        self.input_code.value = code


    def get_sample_list(self, attr, old_file, new_file):
        f = io.BytesIO(b64decode(new_file))
        samplelist = np.loadtxt(f, skiprows=2, delimiter=",")
        print(samplelist)
        samplestr = ''
        #print(','.join(samplelist))
        for sample in samplelist:
            samplestr += str(int(sample)) + ','
        if samplestr.endswith(','):
            samplestr = samplestr[:-1]
        print(samplestr)
        operator_doc.add_next_tick_callback(partial(self.update_samples,samplestr))


    async def get_pm(self, plateid):
        '''gets plate map from aligner server'''

        #plateid = '4534'
        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_platemap_plateid"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'plateid':plateid}) as resp:
                response = await resp.json()
                self.pmdata = json.loads(response['data']['map'])
                operator_doc.add_next_tick_callback(partial(self.update_pm_plot))

    
    def xy_to_sample(self, xy, pmapxy):
        '''get point from pmap closest to xy'''
        if len(pmapxy):
            diff = pmapxy - xy
            sumdiff = (diff ** 2).sum(axis=1)
            return np.int(np.argmin(sumdiff))
        else:
            return None
    
    
    def get_samples(self, X, Y):
        '''get list of samples row number closest to xy'''
        # X and Y are vectors
        #global pmdata
        xyarr = np.array((X, Y)).T
        pmxy = np.array([[col['x'], col['y']] for col in self.pmdata])
        samples = list(np.apply_along_axis(self.xy_to_sample, 1, xyarr, pmxy))
        return samples             

    def update_tables(self):
        # should maybe update it do ws later instead of polling once orch2 is ready
        self.get_decisions()
        self.columns_dec = [TableColumn(field=key, title=key) for key in self.decision_list.keys()]
        self.decision_table.source.data = self.decision_list
        self.decision_table.columns=self.columns_dec

        self.get_actions()
        self.columns_act = [TableColumn(field=key, title=key) for key in self.action_list.keys()]
        self.action_table.source.data=self.action_list
        self.action_table.columns=self.columns_act


    async def IOloop_visualizer(self):
        # should maybe update it do ws later instead of polling once orch2 is ready
        # itr seems when orch is in dispatch loop this here is not updating
        self.update_tables()

##############################################################################
# MAIN
##############################################################################

operator_doc = curdoc()
operator_doc.title = S.params.get('doc_name', 'Modular Visualizer')

operator = C_async_operator(S, C)

dynamic_col = column(operator.layout0, operator.layout2)

operator_doc.add_root(dynamic_col)

# get the event loop
operatorloop = asyncio.get_event_loop()

servicemode = S.params.get('servicemode', False)


# select the first item to force an update of the layout
if operator.act_select_list:
    operator.actions_dropdown.value = operator.act_select_list[0]

# operator_doc.add_periodic_callback(operator.IOloop_visualizer,2000) # time in ms