
import os
import sys
import websockets
import json
import collections
from functools import partial
from importlib import import_module
import sys

from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
from bokeh.colors import HSL,Color
from tornado.ioloop import IOLoop

from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config


Sraman = config['servers']['oceanServer']
Sftir = config['servers']['arcoptixServer']
doc = curdoc()
ramanurl = f"ws://{Sraman['host']}:{Sraman['port']}/ws"
ftirurl = f"ws://{Sftir['host']}:{Sftir['port']}/ws"


def update_raman(newdata):
    global source
    global plot1,plot2
    doc.remove_root(plot1)
    doc.remove_root(plot2)
    source.append(newdata)

    plot1 = figure(title="newest data", height=300)
    plot1.title.align = "center"
    plot1.title.text_font_size = "24px"
    plot1.add_layout(Title(text="newest data", align="center"), "left")
    plot1.line(x="wavelengths", y='intensities', source=source[-1])    
    plot2 = figure(title="all data", height=300)
    plot2.title.align = "center"
    plot2.title.text_font_size = "24px"
    plot2.add_layout(Title(text="all data", align="center"), "left")
    l = len(source)
    colors = [HSL(round(240*i/(l-1)) if l != 1 else 180,1,.5).to_rgb() for i in range(l)]
    for i in range(l):
                plot2.line(x="wavelengths", y='intensities', source=source[i],line_color=colors[i]) 
    
    doc.add_root(plot1) # add plot to document
    doc.add_root(plot2)

def update_ftir(newdata):
    global source
    global plot3,plot4
    doc.remove_root(plot3)
    doc.remove_root(plot4)
    source.append(newdata)

    plot3 = figure(title="newest data", height=300)
    plot3.title.align = "center"
    plot3.title.text_font_size = "24px"
    plot3.add_layout(Title(text="newest data", align="center"), "left")
    plot3.line(x="wavelengths", y='intensities', source=source[-1])    
    plot4 = figure(title="all data", height=300)
    plot4.title.align = "center"
    plot4.title.text_font_size = "24px"
    plot4.add_layout(Title(text="all data", align="center"), "left")
    l = len(source)
    colors = [HSL(round(240*i/(l-1)) if l != 1 else 180,1,.5).to_rgb() for i in range(l)]
    for i in range(l):
                plot4.line(x="wavelengths", y='intensities', source=source[i],line_color=colors[i]) 
    
    doc.add_root(plot3) # add plot to document
    doc.add_root(plot4)

async def ramanloop(): # non-blocking coroutine, updates data source
    while True:
        async with websockets.connect(ramanurl) as ws:
            while True:
                new_data = await ws.recv()
                new_data=json.loads(new_data)
                doc.add_next_tick_callback(partial(update_raman, new_data))

async def ftirloop():
    while True:
        async with websockets.connect(ftirurl) as ws:
            while True:
                new_data = await ws.recv()
                new_data=json.loads(new_data)
                doc.add_next_tick_callback(partial(update_ftir, new_data))

source = []

plot1 = figure(title="newest raman data", height=300)
plot2 = figure(title="all raman data", height=300)
plot3 = figure(title="newest ftir data", height=300)
plot4 = figure(title="all ftir data", height=300)

doc.add_root(plot1) # add plot to document
doc.add_root(plot2)
doc.add_root(plot3)
doc.add_root(plot4)


IOLoop.current().spawn_callback(ramanloop) # add coro to IOLoop
IOLoop.current().spawn_callback(ftirloop)





