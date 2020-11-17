
import os
import sys
import websockets
import json
import collections
from functools import partial
from importlib import import_module
import sys
sys.path.append("../config")
from mischbares_small import config

from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
from bokeh.colors import HSL,Color
from tornado.ioloop import IOLoop


S = config['servers']['oceanServer']
doc = curdoc()
uri = f"ws://{S['host']}:{S['port']}/ws"


def update_plot(newdata):
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

async def loop(): # non-blocking coroutine, updates data source
    while True:
        async with websockets.connect(uri) as ws:
            while True:
                new_data = await ws.recv()
                new_data=json.loads(new_data)
                doc.add_next_tick_callback(partial(update_plot, new_data))

source = []

plot1 = figure(title="newest data", height=300)
plot2 = figure(title="all data", height=300)

doc.add_root(plot1) # add plot to document
doc.add_root(plot2)

IOLoop.current().spawn_callback(loop) # add coro to IOLoop





