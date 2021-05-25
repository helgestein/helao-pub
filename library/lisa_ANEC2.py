"""
Action library for ADSS (RSHS and ANEC2)

action tuples take the form:
(decision_id, server_key, action, param_dict, preemptive, blocking)

server_key must be a FastAPI action server defined in config
"""
from classes import Action, Decision
import os
import sys
lib_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(lib_root)), 'core'))

# list valid actualizer functions 
ACTUALIZERS = ['ADSS_CA', 'ADSS_CP', 'ADSS_CP10', 'orchtest']


# z positions for ADSS cell
z_home = 0.0
# touches the bottom of cell
z_engage = 2.5
# moves it up to put pressure on seal
z_seal = 4.5


def orchtest(decisionObj: Decision, d_mm = '1.0'):
    '''Test action for ORCH debugging'''
    action_list = []
    # action_list.append(Action(decision=decisionObj,
    #                      server_key="motor",
    #                      action="move",
    #                      action_pars={"d_mm": f'{d_mm}',
    #                                   "axis": "x",
    #                                   "mode": "relative",
    #                                   "transformation": "motorxy",
    #                                   },
    #                      preempt=False,
    #                      block=False))
    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": '0.0',
                                      "Tval": '10.0',
                                      "SampleRate": '0.5',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=False,
                         block=False))
    return action_list


def ADSS_CA(decisionObj: Decision, x_mm = '10.0', y_mm = '10.0',liquid_sample_no = '1', potential = '0.0', duration = '10.0', samplerate = '0.01', filltime = 10.0):
    """Chronoamperometry (current response on amplied potential):\n
        x_mm / y_mm: plate coordinates of sample;\n
        potential (Volt): applied potential;\n
        duration (sec): how long the potential is applied;\n
        samplerate (sec): sampleperiod of Gamry;\n
        filltime (sec): how long it takes to fill the cell with liquid or empty it."""

    action_list = []

    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # move to position
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{x_mm},{y_mm}',
                                      "axis": "x,y",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # engage
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_engage}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=False,
                         block=False))


    # seal
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_seal}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # fill liquid
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'fillfixed',#'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'electrolyte_res',
                                      'volume_uL': '30000', # uL
                                      'dest_tray': '2',
                                      'dest_slot': '1',
                                      'dest_vial': '1',
                                      #logfile: str = 'TestLogFile.txt',
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=False,
                         block=False))

    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=False,
                          block=False))


    # turn on pump
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 1,
                                      },
                          preempt=False,
                          block=False))


    # wait some time to pump in the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=True,
                          block=False))


    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=False,
                         block=False))


    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=True,
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=True,
                          block=False))


    # # turn pump off
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 0,
                                      },
                          preempt=True,
                          block=False))


    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=True,
                          block=False))


    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))


    return action_list


def ADSS_CP(decisionObj: Decision, x_mm = '10.0', y_mm = '10.0', liquid_sample_no = '3', dest_vial = '2', current = '0.001', duration = '30.0', samplerate = '0.01', filltime = 60.0):
    """Chronopotentiometry (Potential response on controlled current):
        x_mm / y_mm: plate coordinates of sample;
        potential (Volt): applied potential;
        duration (sec): how long the potential is applied;
        samplerate (sec): sampleperiod of Gamry;
        filltime (sec): how long it takes to fill the cell with liquid or empty it."""

    action_list = []

    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # move to position
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{x_mm},{y_mm}',
                                      "axis": "x,y",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # engage
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_engage}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=False,
                         block=False))


    # seal
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_seal}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))



    # fill liquid
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'fillfixed',#'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'electrolyte_res',
                                      'volume_uL': '30000', # uL
                                      'dest_tray': '2',
                                      'dest_slot': '1',
                                      'dest_vial': '1',
                                      #logfile: str = 'TestLogFile.txt',
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=False,
                         block=False))



    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=False,
                          block=False))


    # turn on pump
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 1,
                                      },
                          preempt=False,
                          block=False))


    # wait some time to pump in the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # apply current
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=False,
                         block=False))








    # take liquid sample
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-1', # signals to use last item in liquid sample DB
                                      'method': 'archive ',#'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '500', # uL
                                      'dest_tray': '2',
                                      'dest_slot': '1',
                                      'dest_vial': f'{dest_vial}',
                                      #logfile: str = 'TestLogFile.txt',
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))





    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=False,
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # # turn pump off
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 0,
                                      },
                          preempt=False,
                          block=False))

    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=True,
                          block=False))


    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))


    return action_list




def ADSS_CP10(decisionObj: Decision, 
              x_mm = '10.0', 
              y_mm = '10.0', 
              liquid_sample_no = '3', 
              dest_vial = '2', 
              current1 = '0.001',
              current2 = '0.001',
              current3 = '0.001',
              current4 = '0.001',
              current5 = '0.001',
              current6 = '0.001',
              current7 = '0.001',
              current8 = '0.001',
              current9 = '0.001',
              current10 = '0.001',
              duration = '30.0', samplerate = '0.01', filltime = 60.0):
    """Chronopotentiometry (Potential response on controlled current):
        x_mm / y_mm: plate coordinates of sample;
        potential (Volt): applied potential;
        duration (sec): how long the potential is applied;
        samplerate (sec): sampleperiod of Gamry;
        filltime (sec): how long it takes to fill the cell with liquid or empty it."""

    action_list = []

    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # move to position
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{x_mm},{y_mm}',
                                      "axis": "x,y",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))

    # engage
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_engage}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=False,
                         block=False))


    # seal
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_seal}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))



    # fill liquid
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'fillfixed',#'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'electrolyte_res',
                                      'volume_uL': '30000', # uL
                                      'dest_tray': '2',
                                      'dest_slot': '1',
                                      'dest_vial': '1',
                                      #logfile: str = 'TestLogFile.txt',
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=False,
                         block=False))



    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=False,
                          block=False))


    # turn on pump
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 1,
                                      },
                          preempt=False,
                          block=False))


    # wait some time to pump in the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # apply current1
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current1}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=False,
                         block=False))


    # apply current2
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current2}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))


    # apply current3
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current3}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current4
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current4}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current5
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current5}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current6
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current6}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current7
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current7}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current8
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current8}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current9
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current9}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # apply current10
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CP",
                         action_pars={"Ival": f'{current10}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))






    # take liquid sample
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-1', # signals to use last item in liquid sample DB
                                      'method': 'archive',#'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '500', # uL
                                      'dest_tray': '2',
                                      'dest_slot': '1',
                                      'dest_vial': f'{dest_vial}',
                                      #logfile: str = 'TestLogFile.txt',
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))





    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=False,
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="orchestrator",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # # turn pump off
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'PeriPump',
                                      "on": 0,
                                      },
                          preempt=False,
                          block=False))

    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=True,
                          block=False))


    # move z to home
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{z_home}',
                                      "axis": "z",
                                      "mode": "absolute",
                                      "transformation": "instrxy",
                                      },
                         preempt=True,
                         block=False))


    return action_list