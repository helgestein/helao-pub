from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
from functools import partial
from tornado.ioloop import IOLoop

import asyncio
import websockets
import json

from bokeh.plotting import show
from bokeh.io import output_notebook
from bokeh.models import Range1d, ColumnDataSource
from bokeh.models.renderers import GlyphRenderer

import numpy as np


doc = curdoc()

uri = "ws://localhost:8003/ws"
# ws = websockets()
# ws.connect(uri)

time_stamp = 0

def update(new_data):
    print(new_data)
    source.stream(new_data)

def remove_glyphs(figure, glyph_name_list):
    renderers = figure.select(dict(type=GlyphRenderer))
    for r in renderers:
        if r.name in glyph_name_list:
            col = r.glyph.y
            r.data_source.data[col] = [np.nan] * len(r.data_source.data[col])

def remove_line(new_time_stamp):
    global time_stamp
    global source
    # print("removing line")
    # remove_glyphs(plot, [str(time_stamp)])
    line = plot.select_one({'name': str(time_stamp)})
    line.visible = False
    time_stamp = new_time_stamp
    source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))
    plot.line(x='t_s', y='Ewe_V', source=source, name=str(time_stamp))

async def loop(): # non-blocking coroutine, updates data source
    async with websockets.connect(uri) as ws:
        while True:
            new_data = await ws.recv()
            new_data=json.loads(new_data)
            if(type(new_data) == float):
                if(new_data != time_stamp): 
                    doc.add_next_tick_callback(partial(remove_line, new_data))
            else:
                doc.add_next_tick_callback(partial(update, new_data))

source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))

plot = figure(height=300)
plot.line(x='t_s', y='Ewe_V', source=source, name=str(time_stamp))

doc.add_root(plot) # add plot to document
IOLoop.current().spawn_callback(loop) # add coro to IOLoop





