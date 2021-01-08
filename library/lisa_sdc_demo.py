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
ACTUALIZERS = ['oer_screen', 'dummy_act']


def dummy_act():
    action_list = dummy_act2()
    return action_list


def dummy_act2():
    action_list = ['a', 'bunch', 'of', 'actions']
    return action_list

# map platemap x,y to stage x,y


def calmove(decisionObj: Decision):
    paramd = {}
    # read motor calibration
    # read platemap
    return(paramd)


move_x = {"x_mm": 10.0,
          "axis": "x",
        #   "speed": None,
          "mode": "relative"
          }
move_y = {"x_mm": 10.0,
          "axis": "y",
        #   "speed": None,
          "mode": "relative"
}
cv0_pars = {"Vinit": -0.5,
            "Vfinal": -0.5,
            "Vapex1": 0.5,
            "Vapex2": 0.5,
            "ScanRate": 0.1,
            "Cycles": 1,
            "SampleRate": 0.004,
            "control_mode": "galvanostatic"}
cv1_pars = {"Vinit": 0,
            "Vfinal": 0,
            "Vapex1": 1.0,
            "Vapex2": -1.0,
            "ScanRate": 0.2,
            "Cycles": 1,
            "SampleRate": 0.05,
            "control_mode": "galvanostatic"}

# action set for OER screening


def oer_screen(decisionObj: Decision):
    action_list = []
    # move x
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars=move_x,
                         preempt=False,
                         block=False))
    # move y
    action_list.append(Action(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars=move_y,
                         preempt=False,
                         block=False))
    # CV techniques:
    #   in general, need to preempt (wait for idle) and block during
    #   potentiostat measurements
    action_list.append(Action(decisionObj, "potentiostat", "potential_cycle",
                       cv0_pars, True, True))
    action_list.append(Action(decisionObj, "potentiostat", "potential_cycle",
                       cv1_pars, True, True))
    return action_list
