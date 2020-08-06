from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
from functools import partial
from tornado.ioloop import IOLoop

import asyncio
import websockets
import json


doc = curdoc()

uri = "ws://localhost:8003/ws"
# ws = websockets()
# ws.connect(uri)

def update(new_data):
    print(new_data)
    source.stream(new_data)

async def loop(): # non-blocking coroutine, updates data source
    async with websockets.connect(uri) as ws:
        while True:
            new_data = await ws.recv()
            new_data=json.loads(new_data)
            if(type(new_data) == float):
            	pass # float means it is the PID and if that has changed we want to clear the plot
            else:
            	doc.add_next_tick_callback(partial(update, new_data))

source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))

plot = figure(height=300)
plot.line(x='t_s', y='Ewe_V', source=source)

doc.add_root(plot) # add plot to document
IOLoop.current().spawn_callback(loop) # add coro to IOLoop




