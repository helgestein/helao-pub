""" models.py
Standard classes for HelaoFastAPI server response objects.

"""
from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel


class return_dec(BaseModel):
    """Return class for queried Decision objects."""

    index: int
    uid: str
    label: str
    actualizer: str
    pars: dict
    access: str


class return_declist(BaseModel):
    """Return class for queried Decision list."""

    decisions: List[return_dec]


class return_act(BaseModel):
    """Return class for queried Action objects."""

    index: int
    uid: str
    server: str
    action: str
    pars: dict
    preempt: int


class return_actlist(BaseModel):
    """Return class for queried Action list."""

    actions: List[return_act]


class return_finishedact(BaseModel):
    """Standard return class for actions that finish with response."""

    technique_name: str
    access: str
    orch_name: str
    decision_timestamp: str
    decision_uuid: str
    decision_label: str
    actualizer: str
    actual_pars: dict
    result_dict: dict
    action_server: str
    action_queue_time: str
    action_real_time: Optional[str]
    action_name: str
    action_params: dict
    action_uuid: str
    action_enum: str
    action_abbr: str
    actionnum: str
    start_condition: Union[int, dict]
    save_rcp: bool
    save_data: bool
    samples_in: Optional[dict]
    samples_out: Optional[dict]
    output_dir: Optional[str]
    file_dict: Optional[dict]
    column_names: Optional[list]
    header: Optional[str]
    data: Optional[list]


class return_runningact(BaseModel):
    """Standard return class for actions that finish after response."""

    technique_name: str
    access: str
    orch_name: str
    decision_timestamp: str
    decision_uuid: str
    decision_label: str
    actualizer: str
    actual_pars: dict
    result_dict: dict
    action_server: str
    action_queue_time: str
    action_real_time: Optional[str]
    action_name: str
    action_params: dict
    action_uuid: str
    action_enum: str
    action_abbr: str
    actionnum: str
    start_condition: Union[int, dict]
    save_rcp: bool
    save_data: bool
    samples_in: Optional[dict]
    samples_out: Optional[dict]
    output_dir: Optional[str]
