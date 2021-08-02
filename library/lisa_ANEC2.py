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
ACTUALIZERS = ['ADSS_CA_5','ADSS_CA_7','dilute_all', 'ADSS_CA', 'ADSS_CP', 'ADSS_CP10', 'orchtest']


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
    # action_list.append(Action(decision=decisionObj,
    #                      server_key="potentiostat",
    #                      action="run_CA",
    #                      action_pars={"Vval": '0.0',
    #                                   "Tval": '10.0',
    #                                   "SampleRate": '0.5',
    #                                   "TTLwait": '-1',
    #                                   "TTLsend": '-1',
    #                                   "IErange": 'auto',
    #                                   },
    #                      preempt=False,
    #                      block=False))
    
    
    

    # # turn on pump
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="nimax",
    #                       action="run_task_Pumps",
    #                       action_pars={"pumps": 'PeriPump',
    #                                   "on": 0,
    #                                   },
    #                       preempt=False,
    #                       block=False))    
    
    # action_list.append(Action(decision=decisionObj,
    #                  server_key="PAL",
    #                  action="run_method",
    #                  action_pars={'liquid_sample_no': 1,
    #                               'method': 'lcfc_fill_hardcodedvolume.cam',
    #                               'tool':'LS3',
    #                               'source': 'elec_res1',
    #                               'volume_uL': '30000', # uL
    #                               'totalvials': '1',
    #                               'sampleperiod': '0.0',
    #                               'spacingmethod': 'linear',
    #                               'spacingfactor': '1.0',
    #                               'wash1': 0, # dont use True or False but 0 AND 1
    #                               'wash2': 0,
    #                               'wash3': 0,
    #                               'wash4': 0,
    #                               },
    #                  preempt=False,
    #                  block=False))


    # # # OCV
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="potentiostat",
    #                       action="run_OCV",
    #                       action_pars={"Tval": '10',
    #                                   "SampleRate": '1.0',
    #                                   "TTLwait": '-1',
    #                                   "TTLsend": '-1',
    #                                   "IErange": 'auto',
    #                                   },
    #                       preempt=False,
    #                       block=False))
    
    action_list.append(Action(decision=decisionObj,
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": '10'},
                          preempt=True,
                          block=False))


    # # turn on pump
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="nimax",
    #                       action="run_task_Pumps",
    #                       action_pars={"pumps": 'PeriPump',
    #                                   "on": 0,
    #                                   },
    #                       preempt=True,
    #                       block=False))    
    
    return action_list



def dilute_all(decisionObj: Decision, liquid_sample_no = '55', source= 'elec_res2', volume_uL = '500'):

    action_list = []

    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': f'{liquid_sample_no}', # signals to use last item in liquid sample DB
                                      'method': 'lcfc_dilute.cam',
                                      'tool':'LS3',
                                      'source': f'{source}',
                                      'volume_uL': f'{volume_uL}', # uL
                                      'totalvials': '100', # need a huge number here else it will only fill the first 'totalvials', the loop will 'break' if no full are found
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    action_list.append(Action(decision=decisionObj,
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": '1'},
                          preempt=True,
                          block=False))    
    return action_list


def ADSS_CP(decisionObj: Decision, x_mm = '10.0', y_mm = '10.0', liquid_sample_no = '3', current = '0.001', duration = '30.0', samplerate = '0.01', filltime = 60.0):
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
                                      'method': 'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '30000', # uL
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
                          server_key="actionflow",
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '500', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
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
                          server_key="actionflow",
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




def ADSS_CA(decisionObj: Decision, x_mm = '10.0', y_mm = '10.0',liquid_sample_no = '3', potential = '0.0', duration = '1320', OCV_duration = '60', samplerate = '1', filltime = 10.0):
           
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

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '10000', # uL
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
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
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
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    # # deep clean
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="PAL",
    #                       action="run_method",
    #                       action_pars={'liquid_sample_no': '-1', # signals to use last item in liquid sample DB
    #                                   'method': 'lcfc_deep_clean.cam',
    #                                   'tool':'LS3',
    #                                   'source': '',
    #                                   'volume_uL': '500', # uL
    #                                   'totalvials': '1',
    #                                   'sampleperiod': '0.0',
    #                                   'spacingmethod': 'linear',
    #                                   'spacingfactor': '1.0',
    #                                   'wash1': 1, # dont use True or False but 0 AND 1
    #                                   'wash2': 1,
    #                                   'wash3': 1,
    #                                   'wash4': 1,
    #                                   },
    #                       preempt=True,
    #                       block=False))

    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=False, # should we wait? I guess not as it just pumps it back into the res
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="actionflow",
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


    # TODO DRAIN


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



# pH10 0.210 for AgAgCl


#-0.21-0.059*9.53
#-0.77227
#pot_offset = -0.21-0.059*9.53
def ADSS_CA_5(decisionObj: Decision,
              x_mm: float = 10.0, y_mm: float = 10.0,
              liquid_sample_no: int = '3',
              potential1: float = 1.23+0.2,
              potential2: float = 1.23+0.4,
              potential3: float = 1.23+0.6, 
              potential4: float = 1.23+0.8, 
              potential5: float = 1.23+1.0,
              erhe: float = -0.21-0.059*9.53,
              duration: float = 1320, OCV_duration: float = 60, samplerate: float = 1, filltime: float = 10.0):
           
    """Chronoamperometry (current response on amplied potential):\n
        x_mm / y_mm: plate coordinates of sample;\n
        potential (Volt): applied potential;\n
        duration (sec): how long the potential is applied;\n
        samplerate (sec): sampleperiod of Gamry;\n
        filltime (sec): how long it takes to fill the cell with liquid or empty it."""

    potential1 = float(potential1)+float(erhe)
    potential2 = float(potential2)+float(erhe)
    potential3 = float(potential3)+float(erhe)
    potential4 = float(potential4)+float(erhe)
    potential5 = float(potential5)+float(erhe)
    print(potential1)
    print(potential2)
    print(potential3)
    print(potential4)
    print(potential5)


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

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '10000', # uL
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
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # first cycle

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential1}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))




    # 2 cycle

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential2}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    # 3 cycle


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential3}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))


    # 4 cycle

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential4}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))


    # 5 cycle


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential5}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))
    # # deep clean
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="PAL",
    #                       action="run_method",
    #                       action_pars={'liquid_sample_no': '-1', # signals to use last item in liquid sample DB
    #                                   'method': 'lcfc_deep_clean.cam',
    #                                   'tool':'LS3',
    #                                   'source': '',
    #                                   'volume_uL': '500', # uL
    #                                   'totalvials': '1',
    #                                   'sampleperiod': '0.0',
    #                                   'spacingmethod': 'linear',
    #                                   'spacingfactor': '1.0',
    #                                   'wash1': 1, # dont use True or False but 0 AND 1
    #                                   'wash2': 1,
    #                                   'wash3': 1,
    #                                   'wash4': 1,
    #                                   },
    #                       preempt=True,
    #                       block=False))

    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=False, # should we wait? I guess not as it just pumps it back into the res
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": '120'},
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


    # TODO DRAIN


    # move z to home
    # action_list.append(Action(decision=decisionObj,
    #                      server_key="motor",
    #                      action="move",
    #                      action_pars={"d_mm": f'{z_home}',
    #                                   "axis": "z",
    #                                   "mode": "absolute",
    #                                   "transformation": "instrxy",
    #                                   },
    #                      preempt=True,
    #                      block=False))


    return action_list



#-0.21-0.059*9.53
#-0.77227
#pot_offset = -0.21-0.059*9.53
def ADSS_CA_7(decisionObj: Decision,
              x_mm: float = 10.0, y_mm: float = 10.0,
              liquid_sample_no: int = '3',
              potential1: float = 1.23-0.2,
              potential2: float = 1.23+0.0,             
              potential3: float = 1.23+0.2,
              potential4: float = 1.23+0.4,
              potential5: float = 1.23+0.6, 
              potential6: float = 1.23+0.8, 
              potential7: float = 1.23+1.0,
              erhe: float = -0.21-0.059*9.53,
              duration: float = 1320, OCV_duration: float = 60, samplerate: float = 1, filltime: float = 10.0):
           
    """Chronoamperometry (current response on amplied potential):\n
        x_mm / y_mm: plate coordinates of sample;\n
        potential (Volt): applied potential;\n
        duration (sec): how long the potential is applied;\n
        samplerate (sec): sampleperiod of Gamry;\n
        filltime (sec): how long it takes to fill the cell with liquid or empty it."""

    potential1 = float(potential1)+float(erhe)
    potential2 = float(potential2)+float(erhe)
    potential3 = float(potential3)+float(erhe)
    potential4 = float(potential4)+float(erhe)
    potential5 = float(potential5)+float(erhe)
    potential4 = float(potential6)+float(erhe)
    potential5 = float(potential7)+float(erhe)
    print(potential1)
    print(potential2)
    print(potential3)
    print(potential4)
    print(potential5)
    print(potential6)
    print(potential7)

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

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '10000', # uL
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
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": f'{filltime}'},
                          preempt=False,
                          block=False))


    # first cycle ############################################################

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential1}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))




    # 2 cycle ################################################################

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential2}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    # 3 cycle ################################################################


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential3}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))


    # 4 cycle ################################################################

    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))


    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential4}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))


    # 5 cycle ################################################################


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential5}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))


    # 6 cycle ################################################################


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential6}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    # 7 cycle ################################################################


    # fill liquid, no wash (assume it was cleaned before)
    action_list.append(Action(decision=decisionObj,
                         server_key="PAL",
                         action="run_method",
                         action_pars={'liquid_sample_no': f'{liquid_sample_no}',
                                      'method': 'lcfc_fill.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '1000', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                         preempt=True,
                         block=False))

    # OCV
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_OCV",
                         action_pars={"Tval": f'{OCV_duration}',
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      },
                          preempt=True,
                          block=False))

    # apply potential
    action_list.append(Action(decision=decisionObj,
                         server_key="potentiostat",
                         action="run_CA",
                         action_pars={"Vval": f'{potential7}',
                                      "Tval": f'{duration}',
                                      "SampleRate": f'{samplerate}',
                                      "TTLwait": '-1',
                                      "TTLsend": '-1',
                                      "IErange": 'auto',
                                      },
                         preempt=True,
                         block=False))

    # take multiple scheduled liquid samples
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-2', # signals to use second last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '3',
                                      'sampleperiod': '60,600,1140', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'timeoffset': '60.0',
                                      },
                          preempt=False,
                          block=False))

    # take last liquid sample and clean
    action_list.append(Action(decision=decisionObj,
                          server_key="PAL",
                          action="run_method",
                          action_pars={'liquid_sample_no': '-5', # signals to use third last item in liquid sample DB
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '200', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0', #1min, 10min, 10min
                                      'spacingmethod': 'custom',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
                                      },
                          preempt=True,
                          block=False))

    # end ####################################################################


    # # deep clean
    # action_list.append(Action(decision=decisionObj,
    #                       server_key="PAL",
    #                       action="run_method",
    #                       action_pars={'liquid_sample_no': '-1', # signals to use last item in liquid sample DB
    #                                   'method': 'lcfc_deep_clean.cam',
    #                                   'tool':'LS3',
    #                                   'source': '',
    #                                   'volume_uL': '500', # uL
    #                                   'totalvials': '1',
    #                                   'sampleperiod': '0.0',
    #                                   'spacingmethod': 'linear',
    #                                   'spacingfactor': '1.0',
    #                                   'wash1': 1, # dont use True or False but 0 AND 1
    #                                   'wash2': 1,
    #                                   'wash3': 1,
    #                                   'wash4': 1,
    #                                   },
    #                       preempt=True,
    #                       block=False))

    # set pump flow backward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 1,
                                      },
                          preempt=False, # should we wait? I guess not as it just pumps it back into the res
                          block=False))


    # wait some time to pump out the liquid
    action_list.append(Action(decision=decisionObj,
                          server_key="actionflow",
                          action="action_wait",
                          action_pars={"waittime": '120'},
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


    # TODO DRAIN


    # move z to home
    # action_list.append(Action(decision=decisionObj,
    #                      server_key="motor",
    #                      action="move",
    #                      action_pars={"d_mm": f'{z_home}',
    #                                   "axis": "z",
    #                                   "mode": "absolute",
    #                                   "transformation": "instrxy",
    #                                   },
    #                      preempt=True,
    #                      block=False))


    return action_list

def ADSS_CP10(decisionObj: Decision, 
              x_mm = '10.0', 
              y_mm = '10.0', 
              liquid_sample_no = '3', 
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
                                      'method': 'lcfc_fill_hardcodedvolume.cam',
                                      'tool':'LS3',
                                      'source': 'elec_res1',
                                      'volume_uL': '30000', # uL
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
                          server_key="actionflow",
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
                                      'method': 'lcfc_archive.cam',
                                      'tool':'LS3',
                                      'source': 'lcfc_res',
                                      'volume_uL': '500', # uL
                                      'totalvials': '1',
                                      'sampleperiod': '0.0',
                                      'spacingmethod': 'linear',
                                      'spacingfactor': '1.0',
                                      'wash1': 1, # dont use True or False but 0 AND 1
                                      'wash2': 1,
                                      'wash3': 1,
                                      'wash4': 1,
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
                          server_key="actionflow",
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
    # action_list.append(Action(decision=decisionObj,
    #                      server_key="motor",
    #                      action="move",
    #                      action_pars={"d_mm": f'{z_home}',
    #                                   "axis": "z",
    #                                   "mode": "absolute",
    #                                   "transformation": "instrxy",
    #                                   },
    #                      preempt=True,
    #                      block=False))


    return action_list
