
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
from tornado.ioloop import IOLoop


S = config['servers']['oceanServer']
doc = curdoc()
uri = f"ws://{S['host']}:{S['port']}/ws"


def update_plot(newdata):
    print("i made it into update")
    global source
    global plot
    doc.remove_root(plot)
    source = newdata

    plot = figure(title="raman", height=300)
    plot.title.align = "center"
    plot.title.text_font_size = "24px"
    plot.add_layout(Title(text="Raman", align="center"), "left")
    plot.line(x="wavelengths", y='intensities', source=source, name="raman")    

    
    doc.add_root(plot) # add plot to document


async def loop(): # non-blocking coroutine, updates data source
    print("i made it into loop")
    while True:
        async with websockets.connect(uri) as ws:
            while True:
                print("hey everyone")
                new_data = await ws.recv()
                new_data=json.loads(new_data)
                doc.add_next_tick_callback(partial(update_plot, new_data))

source = ColumnDataSource(data=dict(wavelengths=[], intensities=[]))

plot = figure(title="Title", height=300)
line1 = plot.line(x='wavelengths', y='intensities', source=source, name="raman")


doc.add_root(plot) # add plot to document

IOLoop.current().spawn_callback(loop) # add coro to IOLoop





