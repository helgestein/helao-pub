"""
Action library for LiSA SDC demonstration

action tuples take the form:
(decision_id, server_key, action, param_dict, preemptive, blocking)

server_key must be a FastAPI action server defined in config
"""
import os
import sys
lib_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(lib_root)), 'core'))
from classes import Action, Decision

actualizers = ['oer_screen']


def dummy_acts():
    action_list = ['a', 'bunch', 'of', 'actions']
    return action_list

# map platemap x,y to stage x,y
def calmove(decisionObj:Decision):
    paramd = {}
    # read motor calibration
    # read platemap
    return(paramd)

ocv_pars = {}
ca_pars = {}
cv_pars = {}
cp_pars = {}

# action set for OER screening
def oer_screen(decisionObj:Decision):
    action_list = []
    # move x
    action_list.append(A(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars=calmove(decisionObj),
                         preempt=False,
                         block=False))
    # move y
    action_list.append(A(decision=decisionObj,
                         server_key="motor",
                         action="move",
                         action_pars=calmove(decisionObj),
                         preempt=False,
                         block=False))
    # OCV technique:
    #   in general, need to preempt (wait for idle) and block during
    #   potentiostat measurements
    action_list.append(A(decisionObj, "potentiostat", "OCV",
                       ocv_pars, True, True))
    # CA technique:
    action_list.append(A(decisionObj, "potentiostat", "CA",
                       ca_pars, True, True))
    # CV technique:
    action_list.append(A(decisionObj, "potentiostat", "CV",
                       cv_pars, True, True))
    # CP technique:
    action_list.append(A(decisionObj, "potentiostat", "CP",
                       cp_pars, True, True))
    return action_list
