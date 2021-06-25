# http://127.0.0.1:5007/bokeh_platealigner
# http://127.0.0.1:8001/docs#/

# TODO: add hotkeys via external js
# TODO: 1p updates the offsets in TM and copies scale and angles
# TODO: 2p updates the scale and angles in TM and copies offsets
debugmode = 1 # for manual operation 

################################################################################
# Plate aligning GUI
################################################################################

import os
import sys
import websockets
import json
#import collections
from functools import partial
from importlib import import_module

#from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
#from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
#from bokeh.models.annotations import Title
#from tornado.ioloop import IOLoop
from munch import munchify

#from bokeh.models import FileInput
from bokeh.layouts import layout, Spacer
from bokeh.models import Button, TextAreaInput, TextInput, Select, CheckboxGroup, Toggle, CustomJS
from bokeh.models.widgets import Div, Markup
from bokeh.events import ButtonClick, DoubleTap
from bokeh.models import TapTool
import numpy as np

#import math
#from pybase64 import b64decode
#import io

import asyncio
import aiohttp
#import time


import pathlib


#from fastapi import FastAPI, WebSocket
#from fastapi.openapi.utils import get_flat_params
#from pydantic import BaseModel
#import uvicorn


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
###########################Begin Visualizer PART##############################


def clicked_reset():
    '''resets aligner to initial params'''
    init_mapaligner()
    

def clicked_addpoint(event):
    '''Add new point to calibration point list and removing last point'''
    global calib_ptsplate
    global calib_ptsmotor
    # (1) get selected marker
    selMarker = MarkerNames.index(calib_sel_motor_loc_marker.value)
    # (2) add new platexy point to end of plate point list
    calib_ptsplate.append(MarkerXYplate[selMarker])
    # (3) get current motor position
    motorxy = g_motor_position # gets the displayed position    
    # (4) add new motorxy to motor point list
    calib_ptsmotor.append(motorxy)
    print('motorxy:',motorxy)
    print('platexy:',MarkerXYplate[selMarker])
    alignerwebdoc.add_next_tick_callback(partial(update_status,"added Point:\nMotorxy:\n"+
                  (str)(motorxy)+"\nPlatexy:\n"+
                  (str)(MarkerXYplate[selMarker])))

    # remove first point from calib list
    calib_ptsplate.pop(0)
    calib_ptsmotor.pop(0)
    # display points
    for i in range(0,3):
        alignerwebdoc.add_next_tick_callback(partial(update_calpointdisplay,i))


def clicked_submit():
    '''submit final results back to aligner server'''
    asyncio.gather(finish_alignment(TransferMatrix,0))


def clicked_go_align():
    '''start a new alignment procedure'''
    global status_align
    global g_aligning    
    # init the aligner
    init_mapaligner()
    
    if g_aligning:
        asyncio.gather(get_pm())
    else:
        alignerwebdoc.add_next_tick_callback(partial(update_status,"Error!\nAlign is invalid!"))


def clicked_moveabs():
    '''move motor to abs position'''
    asyncio.gather(motor_move('absolute',motor_movexabs_text.value, motor_moveyabs_text.value))


def clicked_moverel():
    '''move motor by relative amount'''
    asyncio.gather(motor_move('relative',motor_movexrel_text.value, motor_moveyrel_text.value))


def clicked_readmotorpos():
    '''gets current motor position'''
    asyncio.gather(motor_getxy()) # updates g_motor_position


def clicked_calc():
    '''wrapper for async calc call'''
    asyncio.gather(align_calc())


def clicked_skipstep():
    '''Calculate Transformation Matrix from given points'''
    finish_alignment(initialTransferMatrix,0)


def clicked_buttonsel(idx):
    '''Selects the Marker by clicking on colored buttons'''
    calib_sel_motor_loc_marker.value = MarkerNames[idx]


def clicked_calib_del_pt(idx):
    '''remove cal point'''
    # remove first point from calib list
    calib_ptsplate.pop(idx)
    calib_ptsmotor.pop(idx)
    calib_ptsplate.insert(0,(None, None, 1))
    calib_ptsmotor.insert(0,(None, None, 1))
    # display points
    for i in range(0,3):
        alignerwebdoc.add_next_tick_callback(partial(update_calpointdisplay,i))


def clicked_button_marker_move(idx):
    '''move motor to maker position'''
    if not marker_x[idx].value == "None" and not marker_y[idx].value == "None":
        asyncio.gather(motor_move('absolute',marker_x[idx].value, marker_y[idx].value))


def clicked_pmplot(event):
    '''double click/tap on PM plot to add/move marker'''
    #global calib_sel_motor_loc_marker
    #global pmdata
    print("DOUBLE TAP PMplot")
    print(event.x, event.y)
    # get selected Marker
    selMarker = MarkerNames.index(calib_sel_motor_loc_marker.value)
    # get coordinates of doubleclick
    platex = event.x
    platey = event.y
    # transform to nearest sample point
    PMnum = get_samples([platex], [platey])
    buf = ""
    if PMnum is not None:
        if PMnum[0] is not None: # need to check as this can also happen
            platex = pmdata[PMnum[0]]['x']
            platey = pmdata[PMnum[0]]['y']
            MarkerXYplate[selMarker] = (platex,platey,1)
            MarkerSample[selMarker] = pmdata[PMnum[0]]["Sample"]
            MarkerIndex[selMarker] = PMnum[0]
            MarkerCode[selMarker] = pmdata[PMnum[0]]["code"]
    
            # only display non zero fractions
            buf = ""
            # TODO: test on other platemap
            for fraclet in ("A", "B", "C", "D", "E", "F", "G", "H"):
                if pmdata[PMnum[0]][fraclet] > 0:
                    buf = "%s%s%d " % (buf,fraclet, pmdata[PMnum[0]][fraclet]*100)
            if len(buf) == 0:
                buf = "-"
            MarkerFraction[selMarker] = buf
        ##    elif:
        # remove old Marker point
        old_point = plot_mpmap.select(name=MarkerNames[selMarker])
        if len(old_point)>0:
            plot_mpmap.renderers.remove(old_point[0])
        # plot new Marker point
        plot_mpmap.square(platex, platey, size=7,line_width=2, color=None, alpha=1.0, line_color=MarkerColors[selMarker], name=MarkerNames[selMarker])
        # add Marker positions to list
        update_Markerdisplay(selMarker)


async def finish_alignment(newTransfermatrix,errorcode):
    '''sends finished alignment back to FastAPI server'''
    global initialTransferMatrix
    global g_aligning
    if g_aligning:    
        print("sending alignment back to server")    
        A = dict(
            host = C[S.params.aligner_server].host,
            port = C[S.params.aligner_server].port,
            server = S.params.aligner_server,
            action = 'private/send_alignment',
            pars = {'Transfermatrix':f"{newTransfermatrix}",
                    'oldTransfermatrix':f"{initialTransferMatrix}",
                    'errorcode':f"{errorcode}"
                    }
            )
        url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=A['pars']) as resp:
                response = await resp.json()
                print("Allignment response:",response)
    else:
        alignerwebdoc.add_next_tick_callback(partial(update_status,"Error!\nAlign is invalid!"))


async def motor_ismoving():
    global g_aligning
    if g_aligning:
        A = dict(
            host = C[S.params.aligner_server].host,
            port = C[S.params.aligner_server].port,
            server = S.params.aligner_server,
            action = 'private/ismoving',
#            pars = {'axis':f"{C[S.params.aligner_server].params.x},{C[S.params.aligner_server].params.y}"}
            pars = {'axis':"x,y"}
            )

        url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=A['pars']) as resp:
                response = await resp.json()
                status = response['data']['data']['motor_status']
                if 'moving' in status:
                    return True
                else:
                    return False
    else:
        alignerwebdoc.add_next_tick_callback(partial(update_status,"Error!\nAlign is invalid!"))


async def motor_move(mode, x, y):
    '''moves the motor by submitting a request to aligner server'''
    global motor_readxmotor_text, motor_readyxmotor_text
    global g_motor_position, g_motor_ismoving
    global TransferMatrix
    global g_aligning
    if g_aligning:
        
        # transform xy to motor movement xy
        newxy = await transform_platexy_to_motorxy([(float)(x),(float)(y),1.0])
        print('converted plate to motorxy:',newxy)
        A = dict(
            host = C[S.params.aligner_server].host,
            port = C[S.params.aligner_server].port,
            server = S.params.aligner_server,
            action = 'private/align_move',
            pars = {'d_mm':f"{newxy[0]},{newxy[1]}",
                    'axis':"x,y",
                    'mode': mode}
            )
        url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=A['pars']) as resp:
                _ = await resp.text() # todo need timeout or increase it
                g_motor_ismoving = True
                while g_motor_ismoving:
                    await motor_getxy() # updates g_motor_position
                    await asyncio.sleep(1)
                    g_motor_ismoving = await motor_ismoving()
            
                # update again to get final position
                await motor_getxy() # updates g_motor_position


async def motor_getxy():
    '''gets current motor position from alignment server'''
    global g_motor_position
    global g_aligning
    if g_aligning:
        A = dict(
            host = C[S.params.aligner_server].host,
            port = C[S.params.aligner_server].port,
            server = S.params.aligner_server,
            action = 'private/align_get_position',
            pars = {}
            )
        url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=A['pars']) as resp:
                response = await resp.json()
                positions = response['data']['data']
                if 'x' in positions['ax']:
                    idx = positions['ax'].index('x')
                    xmotor = positions['position'][idx]
                else:
                    xmotor = None
            
                if 'y' in positions['ax']:
                    idx = positions['ax'].index('y')
                    ymotor = positions['position'][idx]
                else:
                    ymotor = None
                g_motor_position = [xmotor, ymotor, 1] # dim needs to be always + 1 for later transformations
    else:
        alignerwebdoc.add_next_tick_callback(partial(update_status,"Error!\nAlign is invalid!"))
    

async def get_pm():
    '''gets plate map from aligner server'''
    global g_aligning
    if g_aligning:
        A = dict(
            host = C[S.params.aligner_server].host,
            port = C[S.params.aligner_server].port,
            server = S.params.aligner_server,
            action = 'private/align_get_PM',
            pars = {}
            )
        url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=A['pars']) as resp:
                response = await resp.json()
                #TODO: check if dataserver actually send a map        
                plateid=response['parameters']['plateid']
                alignerwebdoc.add_next_tick_callback(partial(update_pm_plot_title, plateid))
                alignerwebdoc.add_next_tick_callback(partial(update_status,"Got plateID:\n"+plateid))
                global pmdata
                pmdata = json.loads(response['data']['data']['map'])
                alignerwebdoc.add_next_tick_callback(partial(update_status,"PM loaded"))
                alignerwebdoc.add_next_tick_callback(partial(update_pm_plot))
    else:
        alignerwebdoc.add_next_tick_callback(partial(update_status,"Error!\nAlign is invalid!"))
    

def xy_to_sample(xy, pmapxy):
    '''get point from pmap closest to xy'''
    if len(pmapxy):
        diff = pmapxy - xy
        sumdiff = (diff ** 2).sum(axis=1)
        return np.int(np.argmin(sumdiff))
    else:
        return None


def get_samples(X, Y):
    '''get list of samples row number closest to xy'''
    # X and Y are vectors
    #global pmdata
    xyarr = np.array((X, Y)).T
    pmxy = np.array([[col['x'], col['y']] for col in pmdata])
    samples = list(np.apply_along_axis(xy_to_sample, 1, xyarr, pmxy))
    return samples


def remove_allMarkerpoints():
    '''Removes all Markers from plot'''
    for idx in range(len(MarkerNames)):
        # remove old Marker point
        old_point = plot_mpmap.select(name=MarkerNames[idx])
        if len(old_point)>0:
            plot_mpmap.renderers.remove(old_point[0])


async def align_getstatus():
    '''gets align status from align server
       will be checked when pressing go, submitting, or trying to move motors
       will also checked in FastAPI server for double security'''
    global g_aligning
    A = dict(
        host = C[S.params.aligner_server].host,
        port = C[S.params.aligner_server].port,
        server = S.params.aligner_server,
        action = 'align_status',
        pars = {}
        )
    url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=A['pars']) as resp:
            response = await resp.json()
            if debugmode:
                g_aligning = True # override for testing
            else:
                g_aligning = response['data']['aligning']
            print('Aligner Status:', g_aligning)


def align_1p(xyplate,xymotor):
    '''One point alignment'''
    # can only calculate the xy offset
    xoff = xymotor[0][0]-xyplate[0][0]
    yoff = xymotor[0][1]-xyplate[0][1]
    M = np.matrix([[1,0,xoff],
                   [0,1,yoff],
                   [0,0,1]])
    return M


async def align_calc():
    '''Calculate Transformation Matrix from given points'''
    global calib_ptsplate, calib_ptsmotor
    global TransferMatrix
    global cutoff
    validpts = []

    # check for duplicate points
    platepts, motorpts = align_uniquepts(calib_ptsplate,calib_ptsmotor)

    # check if points are not None
    for idx in range(len(platepts)):
        if (not align_test_point(platepts[idx])) and (not align_test_point(motorpts[idx])):
            validpts.append(idx)

    # select the correct alignment procedure
    if len(validpts) == 3:
        # Three point alignment
        print("3P alignment")
        alignerwebdoc.add_next_tick_callback(partial(update_status,"3P alignment"))
        M = align_3p(platepts, motorpts)
    elif len(validpts) == 2:
        # Two point alignment
        print("2P alignment")
        alignerwebdoc.add_next_tick_callback(partial(update_status,"2P alignment"))
#        # only scale and offsets, no rotation
#        M = align_2p([platepts[validpts[0]],platepts[validpts[1]]],
#                     [motorpts[validpts[0]],motorpts[validpts[1]]])
        # only scale and rotation, offsets == 0
        M = align_3p([platepts[validpts[0]],platepts[validpts[1]],(0,0,1)],
                     [motorpts[validpts[0]],motorpts[validpts[1]],(0,0,1)])
    elif len(validpts) == 1:
        # One point alignment
        print("1P alignment")
        alignerwebdoc.add_next_tick_callback(partial(update_status,"1P alignment"))
        M = align_1p([platepts[validpts[0]]],
                     [motorpts[validpts[0]]])
    else:
        # No alignment
        print("0P alignment")
        alignerwebdoc.add_next_tick_callback(partial(update_status,"0P alignment"))
        M = TransferMatrix
        
    
    M = await transform_MxytoMPlate(M)
    print('####################')
    print(M)
    
    TransferMatrix = cutoffdigits(M, cutoff)
    print('new TransferMatrix:')
    print(M)


    alignerwebdoc.add_next_tick_callback(partial(update_TranferMatrixdisplay))
    alignerwebdoc.add_next_tick_callback(partial(update_status,'New Matrix:\n'+(str)(M)))


################################################################################
# Two point alignment
################################################################################
#def align_2p(xyplate,xymotor):
#    # A = M*B --> M = A*B-1
#    # A .. xymotor
#    # B .. xyplate
#    A = np.matrix([[xymotor[0][0],xymotor[1][0]],
#                   [xymotor[0][1],xymotor[1][1]]])
#    B = np.matrix([[xyplate[0][0],xyplate[1][0]],
#                   [xyplate[0][1],xyplate[1][1]]])


#    M = np.matrix([[1,0,xoff],
#                   [0,1,yoff],
#                   [0,0,1]])
#    return M


def align_3p(xyplate,xymotor):
    '''Three point alignment'''
    
    print('Solving: xyMotor = M * xyPlate')
    # can calculate the full transfer matrix
    # A = M*B --> M = A*B-1
    # A .. xymotor
    # B .. xyplate
    A = np.matrix([[xymotor[0][0],xymotor[1][0],xymotor[2][0]],
                   [xymotor[0][1],xymotor[1][1],xymotor[2][1]],
                   [xymotor[0][2],xymotor[1][2],xymotor[2][2]]])
    B = np.matrix([[xyplate[0][0],xyplate[1][0],xyplate[2][0]],
                   [xyplate[0][1],xyplate[1][1],xyplate[2][1]],
                   [xyplate[0][2],xyplate[1][2],xyplate[2][2]]])
    # solve linear system of equations
    print('xyMotor:\n',A)
    print('xyPlate:\n',B)

    try:
        M = np.dot(A,B.I)
    except Exception:
        # should not happen when all xyplate coordinates are unique
        # (previous function removes all duplicate xyplate points)
        # but can still produce a not valid Matrix
        # as xymotor plates might not be unique/faulty
        print('Matrix singular')
        M = TransferMatrix
    return M


def align_test_point(test_list):
    '''Test if point is valid for aligning procedure'''
    return [i for i in range(len(test_list)) if test_list[i] == None] 


def align_uniquepts(x,y): 
    unique_x = []
    unique_y = []
    for i in range(len(x)):
        if x[i] not in unique_x:
            unique_x.append(x[i])
            unique_y.append(y[i])
    return unique_x, unique_y


async def transform_platexy_to_motorxy(platexy):
    '''Converts plate to motor xy'''
    # M is Transformation matrix from plate to motor
    #motor = M*plate
    A = dict(
        host = C[S.params.aligner_server].host,
        port = C[S.params.aligner_server].port,
        server = S.params.aligner_server,
        action = 'private/toMotorXY',
        pars = {'platexy':json.dumps(np.array(platexy).tolist())}
        )
    url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=A['pars']) as resp:
            response = await resp.text()
            response = json.loads(response)
            return np.asarray(json.loads(response['data']['data']['motorxy']))


async def transform_motorxy_to_platexy(motorxy):
    '''Converts motor to plate xy'''
    # M is Transformation matrix from plate to motor
    #motor = M*plate
    #Minv*motor = Minv*M*plate = plate
    A = dict(
        host = C[S.params.aligner_server].host,
        port = C[S.params.aligner_server].port,
        server = S.params.aligner_server,
        action = 'private/toPlateXY',
        pars = {'motorxy':json.dumps(np.array(motorxy).tolist())}
        )
    url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=A['pars']) as resp:
            # response = await resp.json()
            response = await resp.text()
            response = json.loads(response)
            return np.asarray(json.loads(response['data']['data']['platexy']))

async def transform_MxytoMPlate(Mxy):
    A = dict(
        host = C[S.params.aligner_server].host,
        port = C[S.params.aligner_server].port,
        server = S.params.aligner_server,
        action = 'private/MxytoMPlate',
        pars = {'Mxy':json.dumps(Mxy.tolist())}
        )
    url = f"http://{A['host']}:{A['port']}/{A['server']}/{A['action']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=A['pars']) as resp:
            # response = await resp.json()
            response = await resp.text()
            response = json.loads(response)
            print(response)
            return np.asarray(json.loads(response['data']['data']['Mplate']))

    

def cutoffdigits(M, digits):
    for i in range(len(M)):
        for j in range(len(M)):
            M[i,j] = round(M[i,j],digits)
    return M


################################################################################
# 
################################################################################
def update_calpointdisplay(ptid):
    '''Updates the calibration point display'''
    calib_xplate[ptid].value = (str)(calib_ptsplate[ptid][0])
    calib_yplate[ptid].value = (str)(calib_ptsplate[ptid][1]) 
    calib_xmotor[ptid].value = (str)(calib_ptsmotor[ptid][0])
    calib_ymotor[ptid].value = (str)(calib_ptsmotor[ptid][1])


def update_status(updatestr, reset = 0):
    '''updates the web interface status field'''
    global status_align
    if reset:
        status_align.value = updatestr
    else:
        oldstatus = status_align.value
        status_align.value = updatestr+'\n######\n'+oldstatus


def update_pm_plot():
    '''plots the plate map'''
    #global pmdata
    x = [col['x'] for col in pmdata]
    y = [col['y'] for col in pmdata]
    # remove old Pmplot
    old_point = plot_mpmap.select(name="PMplot")
    if len(old_point)>0:
        plot_mpmap.renderers.remove(old_point[0])
    plot_mpmap.square(x, y, size=5, color=None, alpha=0.5, line_color='black',name="PMplot")



def update_Markerdisplay(selMarker):
    '''updates the Marker display elements'''
    marker_x[selMarker].value = (str)(MarkerXYplate[selMarker][0])
    marker_y[selMarker].value = (str)(MarkerXYplate[selMarker][1])
    marker_index[selMarker].value = (str)((MarkerIndex[selMarker]))
    marker_sample[selMarker].value = (str)((MarkerSample[selMarker]))
    marker_code[selMarker].value = (str)((MarkerCode[selMarker]))
    marker_fraction[selMarker].value = (str)(MarkerFraction[selMarker])


def update_TranferMatrixdisplay():
    global TransferMatrix
    calib_xscale_text.value = "%.1E" % TransferMatrix[0, 0]
    calib_yscale_text.value = "%.1E" % TransferMatrix[1, 1]
    calib_xtrans_text.value = "%.1E" % TransferMatrix[0, 2]
    calib_ytrans_text.value = "%.1E" % TransferMatrix[1, 2]
    calib_rotx_text.value = "%.1E" % TransferMatrix[0, 1] # or the other way around?
    calib_roty_text.value = "%.1E" % TransferMatrix[1, 0]
    

def update_pm_plot_title(plateid):
    plot_mpmap.title.text = ("PlateMap: "+plateid)



def init_mapaligner():
    '''resets all parameters'''
    global calib_ptsplate, calib_ptsmotor, MarkerSample, MarkerIndex, MarkerCode, MarkerXYplate, MarkerFraction
    global initialTransferMatrix
    global TransferMatrix
    global gbuf_motor_position, g_motor_position
    global gbuf_plate_position, g_plate_position
    global g_motor_ismoving
    asyncio.gather(align_getstatus())

    TransferMatrix = initialTransferMatrix
    calib_ptsplate = [(None, None,1),(None, None,1),(None, None,1)]
    calib_ptsmotor = [(None, None,1),(None, None,1),(None, None,1)]
    MarkerSample = [None, None, None, None, None]
    MarkerIndex = [None, None, None, None, None]
    MarkerCode = [None, None, None, None, None]
    MarkerXYplate = [(None, None,1),(None, None,1),(None, None,1),(None, None,1),(None, None,1)]
    MarkerFraction = [None, None, None, None, None]
    for idx in range(len(MarkerNames)):
        alignerwebdoc.add_next_tick_callback(partial(update_Markerdisplay,idx))
    for i in range(0,3):
        alignerwebdoc.add_next_tick_callback(partial(update_calpointdisplay,i))
    remove_allMarkerpoints()
    alignerwebdoc.add_next_tick_callback(partial(update_TranferMatrixdisplay))
    alignerwebdoc.add_next_tick_callback(partial(update_status,"Press ""Go"" to start alignment procedure.",reset = 1))
    
    # initialize motor position variables
    # by simply moving relative 0
    asyncio.gather(motor_move('relative','0', '0'))
    
    # force redraw of cell marker
    gbuf_motor_position = -1*gbuf_motor_position
    gbuf_plate_position = -1*gbuf_plate_position
    

async def IOloop_aligner(): # non-blocking coroutine, updates data source
    '''IOloop for updating web interface'''
    global g_motor_position, g_motor_ismoving
    global motor_readxmotor_text, motor_readymotor_text
    global motor_move_indicator
    global TransferMatrix
    global gbuf_motor_position
    motor_readxmotor_text.value = (str)(g_motor_position[0])
    motor_readymotor_text.value = (str)(g_motor_position[1])
    if g_motor_ismoving:
        motor_move_indicator.label = "Stage Moving"
        motor_move_indicator.button_type="danger"
    else:
        motor_move_indicator.label = "Stage Stopped"
        motor_move_indicator.button_type="success"

    # only update marker when positions differ
    # to remove flicker
    if not gbuf_motor_position == g_motor_position:
        # convert motorxy to platexy # todo, replace with wsdatapositionbuffer
        tmpplate = await transform_motorxy_to_platexy(g_motor_position)
        
        # update cell marker position in plot
        # remove old Marker point
        old_point = plot_mpmap.select(name=MarkerNames[0])
        if len(old_point)>0:
            plot_mpmap.renderers.remove(old_point[0])
        # plot new Marker point
        plot_mpmap.square(tmpplate[0], tmpplate[1], size=7,line_width=2, color=None, alpha=1.0, line_color=MarkerColors[0], name=MarkerNames[0])

        MarkerXYplate[0] = (tmpplate[0],tmpplate[1],1)
        # get rest of values from nearest point 
        PMnum = get_samples([tmpplate[0]], [tmpplate[1]])
        buf = ""
        if PMnum is not None:
            if PMnum[0] is not None: # need to check as this can also happen
                MarkerSample[0] = pmdata[PMnum[0]]["Sample"]
                MarkerIndex[0] = PMnum[0]
                MarkerCode[0] = pmdata[PMnum[0]]["code"]
        
                # only display non zero fractions
                buf = ""
                # TODO: test on other platemap
                for fraclet in ("A", "B", "C", "D", "E", "F", "G", "H"):
                    if pmdata[PMnum[0]][fraclet] > 0:
                        buf = "%s%s%d " % (buf,fraclet, pmdata[PMnum[0]][fraclet]*100)
                if len(buf) == 0:
                    buf = "-"
                MarkerFraction[0] = buf

        update_Markerdisplay(0)

    # buffer position
    gbuf_motor_position = g_motor_position


# only as a test, will produce race condition with other loop
# not for use to update the GUI elements in critical environment
async def IOloop_ws_motordata(): # non-blocking coroutine, updates data source
    global motorws_data_uri
    async with websockets.connect(motorws_data_uri) as ws:
        IOloop_ws_motordata_run = True
        while IOloop_ws_motordata_run:
            try:
                new_data = await ws.recv()
                new_data = json.loads(new_data)
                print(' ... AlignerWSrcv:',new_data)


                if 'x' in new_data['axis']:
                    idx = new_data['axis'].index('x')
                    xmotor = new_data['position'][idx]
                else:
                    xmotor = None
            
                if 'y' in new_data['axis']:
                    idx = new_data['axis'].index('y')
                    ymotor = new_data['position'][idx]
                else:
                    ymotor = None
                
                global g_motor_position
                g_motor_position = [xmotor, ymotor, 1] # dim needs to be always + 1 for later transformations
                
                global g_plate_position
                if 'platexy' in new_data:
                    g_plate_position = new_data['platexy']

                global g_motor_ismoving
                if 'moving' in new_data['motor_status']:
                    g_motor_ismoving = True
                else:
                    g_motor_ismoving = False
                
            except Exception:
                IOloop_ws_motordata_run = False


################################################################################
################################################################################
# Main Script Starts here
################################################################################
################################################################################



# flag to check if we actual should align
g_aligning = False
# global motor position variable
g_motor_position = [0,0,1] # dummy value, will be updated during init
gbuf_motor_position = -1*g_motor_position # to force drawing of marker
g_plate_position = [0,0,1] # dummy value, will be updated during init
gbuf_plate_position = -1*g_plate_position # to force drawing of marker
# global motor move flage
g_motor_ismoving = False # will be updated during init


# initial instrument specific TransferMatrix
initialTransferMatrix = np.matrix([[1,0,0],[0,1,0],[0,0,1]])
cutoff = np.array(C[S.params.aligner_server].params.cutoff)

# this is now used for plate to motor transformation and will be refined
TransferMatrix = initialTransferMatrix


alignerwebdoc = curdoc()
uri = f"ws://{S.host}:{S.port}/ws"


motorserv = C[S.params.aligner_server].params.motor_server
motorws_data_uri = f"ws://{C[motorserv].host}:{C[motorserv].port}/{motorserv}/ws_motordata"
#stat_uri = f"ws://{S.host}:{S.port}/{O.params.ws_host}/ws_status"


MarkerColors = [(255,0,0),(0,0,255),(0,255,0),(255,165,0),(255,105,180)]
#MarkerNames = ["Cell Marker", "Blue Marker", "Green Marker", "Orange Marker", "Pink Marker"]
MarkerNames = ["Cell", "Blue", "Green", "Orange", "Pink"]
MarkerSample = [None, None, None, None, None]
MarkerIndex = [None, None, None, None, None]
MarkerCode = [None, None, None, None, None]
MarkerFraction = [None, None, None, None, None]
# for 2D transformation, the vectors (and Matrix) need to be 3D
MarkerXYplate = [(None, None,1),(None, None,1),(None, None,1),(None, None,1),(None, None,1)]
# 3dim vector because for transformation matrix
calib_ptsplate = [(None, None,1),(None, None,1),(None, None,1)]
calib_ptsmotor = [(None, None,1),(None, None,1),(None, None,1)]


# PM data given as parameter or empty and needs to be loaded
pmdata = []

totalwidth = 800


##############################################################################
#### getPM group elements ###
##############################################################################

#text_1 = Div(text="<b>PlateMapFile:</b>", width=100, height=15)

button_goalign = Button(label="Go", button_type="default", width=150)
button_skipalign = Button(label="Skip this step", button_type="default", width=150)
button_goalign.on_event(ButtonClick, clicked_go_align)
button_skipalign.on_event(ButtonClick, clicked_skipstep)
status_align = TextAreaInput(value="", rows=8, title="Alignment Status:", disabled=True, width=150)


layout_getPM = layout([
#    [text_1],
#    [file_input],
    [button_goalign],
    [button_skipalign],
    [status_align],
#    [button_done],
])



##############################################################################
#### Calibration group elements ###
##############################################################################

calib_sel_motor_loc_marker = Select(title="Active Marker", value=MarkerNames[1], options=MarkerNames, width=110-50)

calib_button_addpt = Button(label="Add Pt", button_type="default", width=110-50)
calib_button_addpt.on_event(ButtonClick, clicked_addpoint)

#Calc. Motor-Plate Coord. Transform
calib_button_calc = Button(label="Calc", button_type="primary", width=110-50)
calib_button_calc.on_event(ButtonClick, clicked_calc)

calib_button_reset = Button(label="Reset", button_type="default", width=110-50)
calib_button_reset.on_event(ButtonClick, clicked_reset)

calib_button_done = Button(label="Sub.", button_type="danger", width=110-50)
calib_button_done.on_event(ButtonClick, clicked_submit)


calib_xplate = []
calib_yplate = []
calib_xmotor = []
calib_ymotor = []
calib_pt_del_button = []
for i in range(0,3):
    buf = "x%d plate" % (i+1)
    calib_xplate.append(TextInput(value="", title=buf, disabled=True, width=60, height=40))
    buf = "y%d plate" % (i+1)
    calib_yplate.append(TextInput(value="", title=buf, disabled=True, width=60, height=40))
    buf = "x%d motor" % (i+1)
    calib_xmotor.append(TextInput(value="", title=buf, disabled=True, width=60, height=40))
    buf = "y%d motor" % (i+1)
    calib_ymotor.append(TextInput(value="", title=buf, disabled=True, width=60, height=40))
    calib_pt_del_button.append(Button(label="Del", button_type="primary", width=(int)(30), height=25))
    calib_pt_del_button[i].on_click(partial(clicked_calib_del_pt, idx=i))

calib_xscale_text = TextInput(value="", title="xscale", disabled=True, width=50, height=40, css_classes=['custom_input1'])
calib_yscale_text = TextInput(value="", title="yscale", disabled=True, width=50, height=40, css_classes=['custom_input1'])
calib_xtrans_text = TextInput(value="", title="x trans", disabled=True, width=50, height=40, css_classes=['custom_input1'])
calib_ytrans_text = TextInput(value="", title="y trans", disabled=True, width=50, height=40, css_classes=['custom_input1'])
calib_rotx_text = TextInput(value="", title="rotx (deg)", disabled=True, width=50, height=40, css_classes=['custom_input1'])
calib_roty_text = TextInput(value="", title="roty (deg)", disabled=True, width=50, height=40, css_classes=['custom_input1'])

#calib_plotsmp_check = CheckboxGroup(labels=["don't plot smp 0"], active=[0], width = 50)

layout_calib = layout([
    [layout([
            [calib_sel_motor_loc_marker],
            [calib_button_addpt],
#            [calib_sel_alg],
            [calib_button_calc],
            [calib_button_reset],
            [calib_button_done],
            ]),
    layout([
            [Spacer(width=20), Div(text="<b>Calibration Coordinates</b>", width=200+50, height=15)],
            layout([
                [[Spacer(height=20),[calib_pt_del_button[0]]],Spacer(width=10),calib_xplate[0], calib_yplate[0],calib_xmotor[0],calib_ymotor[0]],
                Spacer(height=10),
                Spacer(height=5, background=(0,0,0)),
                [[Spacer(height=20),[calib_pt_del_button[1]]],Spacer(width=10),calib_xplate[1], calib_yplate[1],calib_xmotor[1],calib_ymotor[1]],
                Spacer(height=10),
                Spacer(height=5, background=(0,0,0)),
                [[Spacer(height=20),[calib_pt_del_button[2]]],Spacer(width=10),calib_xplate[2], calib_yplate[2],calib_xmotor[2],calib_ymotor[2]],
                [ Spacer(height=10)],
                ],background="#C0C0C0"),
           ])],
    [layout([
           [calib_xscale_text, calib_xtrans_text, calib_rotx_text, Spacer(width=10), calib_yscale_text, calib_ytrans_text, calib_roty_text],
           ]),
    ],
#    [layout([
#           [calib_xscale_text, calib_yscale_text,calib_xtrans_text, calib_ytrans_text,calib_rot_text],
#           ]),[Spacer(height=20),[calib_plotsmp_check]]],
])

##############################################################################
#### Motor group elements ####
##############################################################################
motor_movexabs_text = TextInput(value="0", title="abs x (mm)", disabled=False, width=60, height=40)
motor_moveyabs_text = TextInput(value="0", title="abs y (mm)", disabled=False, width=60, height=40)
motor_moveabs_button = Button(label="Move", button_type="primary", width=60)
motor_moveabs_button.on_event(ButtonClick, clicked_moveabs)

motor_movexrel_text = TextInput(value="0", title="rel x (mm)", disabled=False, width=60, height=40)
motor_moveyrel_text = TextInput(value="0", title="rel y (mm)", disabled=False, width=60, height=40)
motor_moverel_button = Button(label="Move", button_type="primary", width=60)
motor_moverel_button.on_event(ButtonClick, clicked_moverel)

motor_readxmotor_text = TextInput(value="0", title="motor x (mm)", disabled=True, width=60, height=40)
motor_readymotor_text = TextInput(value="0", title="motor y (mm)", disabled=True, width=60, height=40)


motor_read_button = Button(label="Read", button_type="primary", width=60)
motor_read_button .on_event(ButtonClick, clicked_readmotorpos)


motor_move_indicator = Toggle(label="Stage Moving", disabled=True, button_type="danger", width=50) #sucess: green, danger: red

motor_movedist_text = TextInput(value="0", title="move (mm)", disabled=False, width=40, height=40)
motor_move_check = CheckboxGroup(labels=["Arrows control motor"], width=40)

layout_motor = layout([
    layout([
        [[[Spacer(height=20)],[motor_moveabs_button]],motor_movexabs_text,Spacer(width=10),motor_moveyabs_text],
        [[[Spacer(height=20)],[motor_moverel_button]],motor_movexrel_text,Spacer(width=10),motor_moveyrel_text],
        [[[Spacer(height=20)],[motor_read_button]],motor_readxmotor_text,Spacer(width=10),motor_readymotor_text],
        [motor_move_indicator],
        [Spacer(height=15,width=240)],
        ], background="#008080"),
    layout([
        [motor_movedist_text,Spacer(width=10),[[Spacer(height=25)],[motor_move_check]]],
        [Spacer(height=10,width=240)],
        ],background="#808000"),
    ])

##############################################################################
#### Marker group elements ####
##############################################################################
marker_type_text = []
marker_move_button = []
marker_buttonsel = []
marker_index = []
marker_sample = []
marker_x = []
marker_y = []
marker_code = []
marker_fraction = []
marker_layout = []


for idx in range(len(MarkerNames)):
    marker_type_text.append(Paragraph(text=MarkerNames[idx]+" Marker", width=120, height=15))
    marker_move_button.append(Button(label="Move", button_type="primary", width=(int)(totalwidth/5-40), height=25))
    marker_index.append(TextInput(value="", title="Index", disabled=True, width=40, height=40, css_classes=['custom_input2']))
    marker_sample.append(TextInput(value="", title="Sample", disabled=True, width=40, height=40, css_classes=['custom_input2']))
    marker_x.append(TextInput(value="", title="x(mm)", disabled=True, width=40, height=40, css_classes=['custom_input2']))
    marker_y.append(TextInput(value="", title="y(mm)", disabled=True, width=40, height=40, css_classes=['custom_input2']))
    marker_code.append(TextInput(value="", title="code", disabled=True, width=40, height=40, css_classes=['custom_input2']))
    marker_fraction.append(TextInput(value="", title="fraction", disabled=True, width=120, height=40, css_classes=['custom_input2']))
    buf = ("custom_button_Marker%d") % (idx+1)
    marker_buttonsel.append(Button(label="", button_type="default", disabled=False, width=40, height=40,css_classes=[buf]))
    marker_buttonsel[idx].on_click(partial(clicked_buttonsel, idx=idx))
    
    marker_move_button[idx].on_click(partial(clicked_button_marker_move, idx=idx))
    
    buf = """<svg width="40" height="40"><rect width="40" height="40" style="fill:rgb(%d,%d,%d);stroke-width:3;stroke:rgb(%d,%d,%d)" /></svg>""" % (MarkerColors[idx][0],MarkerColors[idx][1],MarkerColors[idx][2],MarkerColors[idx][0],MarkerColors[idx][1],MarkerColors[idx][2])
    marker_layout.append(layout([
                        [marker_type_text[idx]],
                        [marker_buttonsel[idx],marker_index[idx], marker_sample[idx]],
                        [marker_x[idx],marker_y[idx], marker_code[idx]],
                        [marker_fraction[idx]],
                        [Spacer(height=5)],
                        [marker_move_button[idx]],
                        ], width=(int)((totalwidth-4*5)/5)))


# disbale cell marker
marker_move_button[0].disabled=True
marker_buttonsel[0].disabled=True

# combine marker group layouts
layout_markers = layout([
    [marker_layout[0], Spacer(width=5, background=(0,0,0)),
     marker_layout[1], Spacer(width=5, background=(0,0,0)),
     marker_layout[2], Spacer(width=5, background=(0,0,0)),
     marker_layout[3], Spacer(width=5, background=(0,0,0)),
     marker_layout[4]],
],background="#C0C0C0")


##############################################################################
## pm plot
##############################################################################
plot_mpmap = figure(title="PlateMap", height=300,x_axis_label='X (mm)', y_axis_label='Y (mm)',width = totalwidth)
taptool = plot_mpmap.select(type=TapTool)
plot_mpmap.on_event(DoubleTap, clicked_pmplot)


##############################################################################
# add all to alignerwebdoc
##############################################################################

divmanual = Div(text="""<b>Hotkeys:</b> Not supported by bokeh. Will be added later.<svg width="20" height="20">
<rect width="20" height="20" style="fill:{{supplied_color_str}};stroke-width:3;stroke:rgb(0,0,0)" />
</svg>""",
width=totalwidth, height=200)



# is there any better way to inlcude external CSS? 
css_styles = Div(text="""<style>%s</style>""" % pathlib.Path(os.path.join(helao_root, 'visualizer\styles.css')).read_text())

alignerwebdoc.add_root(css_styles)
alignerwebdoc.add_root(layout([[layout_getPM, layout_calib, layout_motor],])) # 150,120, 200, 240
alignerwebdoc.add_root(Spacer(height = 5,width = totalwidth, background=(0,0,0)))
alignerwebdoc.add_root(layout_markers)
alignerwebdoc.add_root(Spacer(height = 5,width = totalwidth, background=(0,0,0)))
alignerwebdoc.add_root(plot_mpmap)
alignerwebdoc.add_root(divmanual)

# init all controls
init_mapaligner()

# add aligner IOloop which updates the visual elements
alignerwebdoc.add_periodic_callback(IOloop_aligner,500) # time in ms

# get asyncIO loop
visoloop = asyncio.get_event_loop()
#add websocket IO loop
visoloop.create_task(IOloop_ws_motordata())
