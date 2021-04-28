
import os
import sys
import websockets
import asyncio
import json
import collections
from functools import partial
from importlib import import_module
from functools import partial


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
from bokeh.events import ButtonClick
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


confPrefix = sys.argv[1] # the name of the config file
servKey = sys.argv[2] # the server key of this script defined in config (i.e. servKey=dict(..)
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"] # get the config defined in config file under dict config["servers"]
S = C[servKey] # the config for this particular server/script in config file

##############################################################################
# Operator class
##############################################################################

class C_async_operator:
    def __init__(self, S_config, C_config):
        self.S_config = S_config
        self.C_config = C_config
        
        self.orch = self.C_config[self.S_config.params.orch]

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




#        self.menu = [("Item 1", "item_1"), ("Item 2", "item_2"), None, ("Item 3", "item_3")]
        
        #self.dropdown = Dropdown(label="Dropdown button", button_type="warning", menu=self.act_list)
        # self.dropdown = Select(title="Actualizers:", value=self.act_select_list[0], options=self.act_select_list)
        self.dropdown = Select(title="Select actualizer:", value = None, options=self.act_select_list)
#        self.dropdown.js_on_event("menu_item_click", self.callback_act_select)
#        self.dropdown.on_event('', self.callback_act_select)
        self.dropdown.on_change('value', self.callback_act_select)
        self.button_prepend = Button(label="prepend", button_type="default", width=150)
        self.button_append = Button(label="append", button_type="default", width=150)

        #self.button_load_sample_list = Button(label="load sample list", button_type="default", width=150)
        self.button_load_sample_list = FileInput(accept=".csv,.txt", width = 300)
        self.button_load_sample_list.on_change('value', self.get_sample_list)

        # buttons to control orch
        self.button_start = Button(label="Start", button_type="default", width=70)
        self.button_stop = Button(label="Stop", button_type="default", width=70)
        self.button_skip = Button(label="Skip", button_type="default", width=70)
        self.button_clear_dec = Button(label="clear decisions", button_type="default", width=100)
        self.button_clear_act = Button(label="clear actions", button_type="default", width=100)
#        self.button_submit.on_event(ButtonClick, self.callback_act_select)


        self.act_descr_txt = Paragraph(text="""select item""", width=600, height=30)


        self.input_sampleno = TextInput(value="", title="sample no", disabled=False, width=330, height=40)
        self.input_plateid = TextInput(value="", title="plate id", disabled=False, width=60, height=40)





        # combine all sublayouts into a single one
#         self.layout0 = layout([
#             [Spacer(width=20), Div(text=f"<b>{S_config.params.doc_name}</b>", width=200+50, height=15)],
# #            layout([self.paragraph1]),
# #            layout([self.radio_button_group]),
# #            layout([self.paragraph2]),
# #            layout([self.checkbox_button_group]),
#             [self.dropdown],
#             [self.act_descr_txt],
#             Spacer(height=10),
#             [self.button_load_sample_list, self.button_append, self.button_prepend],
#             Spacer(height=10),
#             ],background="#C0C0C0",width=640)

        self.layout0 = layout([
            layout(
                [Spacer(width=20), Div(text=f"<b>{S_config.params.doc_name}</b>", width=200+50, height=15, style={'font-size': '200%', 'color': 'red'})],
                background="#C0C0C0",width=640),
            layout([
                [self.dropdown],
                [Spacer(width=10), Div(text="<b>Actualizer description:</b>", width=200+50, height=15)],
                [self.act_descr_txt],
                Spacer(height=10),
                Spacer(height=10),
                ],background="#808080",width=640),
            layout([
                [Paragraph(text="""Load sample list from file:""", width=600, height=30)],
                [self.button_load_sample_list],
                [self.input_plateid, self.input_sampleno],
                Spacer(height=10),
                ]),
            ])


        self.layout2 = layout([
                layout([
                    [self.button_append, self.button_prepend],
                    ]),
                layout([
                [Spacer(width=20), Div(text="<b>Decisions:</b>", width=200+50, height=15)],
                [self.decision_table],
                [Spacer(width=20), Div(text="<b>Actions:</b>", width=200+50, height=15)],
                [self.action_table],
                Spacer(height=10),
                [self.button_start, self.button_stop, self.button_skip, self.button_clear_dec, self.button_clear_act],
                Spacer(height=10),
                ],background="#7fdbff",width=640),
            ])




    def get_actualizers(self):
        '''get all available actualizers to populate later functions'''
        response = self.do_request('list_actualizers')
        self.actualizers = json.loads(response)["actualizers"]
        
        for item in self.actualizers:
            self.act_select_list.append(item['action'])
            #print('##',item)
        
        #global actualizer_name_Enum
        
        #actualizer_name_Enum = Enum('actualizer_name_Enum', {item['action']:item['action'] for item in actualizeritems})
        #print(list(actualizer_name_Enum))


    def get_decisions(self):
        '''get decision list from orch'''
        response = json.loads(self.do_request('list_decisions'))['decisions']
        self.decision_list = dict()
        if len(response):
            for key in response[0].keys():
                self.decision_list[key] = []
            for line in response:
                for key, value in line.items():
                    self.decision_list[key].append(value)


    def get_actions(self):
        '''get action list from orch'''
        response = json.loads(self.do_request('list_actions'))['actions']
        self.action_list = dict()
        if len(response):
            for key in response[0].keys():
                self.action_list[key] = []
        print(self.action_list)


    def do_request(self,item):
        '''submit a FastAPI request to orch'''
        url = f"http://{self.orch.host}:{self.orch.port}/{self.S_config.params.orch}/{item}"
        with requests.Session() as session:
            with session.post(url, params={}) as resp:
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
            print(buf)
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
        
        
##############################################################################
# MAIN
##############################################################################

operator_doc = curdoc()
if 'doc_name' in S.params:
    operator_doc.title = S.params['doc_name']
else:
    operator_doc.title = "Modular Visualizer"


operator = C_async_operator(S, C)
#operator_doc.add_root(operator.layout)

dynamic_col = column(operator.layout0, operator.layout2)

operator_doc.add_root(dynamic_col)

# select the first item to force an update of the layout
if operator.act_select_list:
    operator.dropdown.value = operator.act_select_list[0]

