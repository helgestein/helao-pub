"""
Action library for LiSA SDC demonstration

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
#ACTUALIZERS = ['ADSS_CA', 'orchtest', 'oer_screen', 'dummy_act', 'dummy_act2']
ACTUALIZERS = ['ADSS_CA', 'orchtest']


# def dummy_act():
#     """doc dummy act"""
#     action_list = dummy_act2()
#     return action_list


# def dummy_act2(givemeaname, withdefaultvalue: str = 'default value test'):
#     '''This is the description for dummy act2... Test Test'''
#     action_list = ['a', 'bunch', 'of', 'actions']
#     return action_list

# # map platemap x,y to stage x,y


# def calmove(decisionObj: Decision):
#     paramd = {}
#     # read motor calibration
#     # read platemap
#     return(paramd)


# move_x = {"x_mm": 10.0,
#           "axis": "x",
#         #   "speed": None,
#           "mode": "relative"
#           }
# move_y = {"x_mm": 10.0,
#           "axis": "y",
#         #   "speed": None,
#           "mode": "relative"
# }
# cv0_pars = {"Vinit": -0.5,
#             "Vfinal": -0.5,
#             "Vapex1": 0.5,
#             "Vapex2": 0.5,
#             "ScanRate": 0.1,
#             "Cycles": 1,
#             "SampleRate": 0.004,
#             "control_mode": "galvanostatic"}
# cv1_pars = {"Vinit": 0,
#             "Vfinal": 0,
#             "Vapex1": 1.0,
#             "Vapex2": -1.0,
#             "ScanRate": 0.2,
#             "Cycles": 1,
#             "SampleRate": 0.05,
#             "control_mode": "galvanostatic"}

# action set for OER screening



# z positions for ADSS cell
z_home = 0.0
# touches the bottom of cell
z_engage = 1.0
# moves it up to put pressure on seal
z_seal = 3.0

# def oer_screen(decisionObj: Decision, arg1, arg2 = 3):
#     '''doc OER screen'''
#     action_list = []
#     # move x
#     action_list.append(Action(decision=decisionObj,
#                          server_key="motor",
#                          action="move",
#                          action_pars=move_x,
#                          preempt=False,
#                          block=False))
#     # move y
#     action_list.append(Action(decision=decisionObj,
#                          server_key="motor",
#                          action="move",
#                          action_pars=move_y,
#                          preempt=False,
#                          block=False))
#     # CV techniques:
#     #   in general, need to preempt (wait for idle) and block during
#     #   potentiostat measurements
#     action_list.append(Action(decisionObj, "potentiostat", "potential_cycle",
#                        cv0_pars, True, True))
#     action_list.append(Action(decisionObj, "potentiostat", "potential_cycle",
#                        cv1_pars, True, True))
#     return action_list

def orchtest(decisionObj: Decision, d_mm = '1.0'):
    '''Test action for ORCH debugging'''
    action_list = []
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars={"d_mm": f'{d_mm}',
                                      "axis": "x",
                                      "mode": "relative",
                                      "transformation": "motorxy",
                                      },
                         preempt=False,
                         block=False))

    return action_list


def ADSS_CA(decisionObj: Decision, x_mm = '10.0', y_mm = '10.0', potential = '0.0', duration = '10.0', samplerate = '0.01'):
    """Chronoamperometry (current response on amplied potential)"""
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


    # set pump flow forward
    action_list.append(Action(decision=decisionObj,
                          server_key="nimax",
                          action="run_task_Pumps",
                          action_pars={"pumps": 'Direction',
                                      "on": 0,
                                      },
                          preempt=True,
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