""" schemas.py
Standard classes for experiment queue objects.

"""
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union
import types

from helao.core.helper import gen_uuid
from helao.core.model import return_finishedact, return_runningact


class Decision(object):
    "Sample-process grouping class."

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        orch_name: str = "orchestrator",
        technique_name: str = None,
        decision_label: str = "nolabel",
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.orch_name = imports.get("orch_name", orch_name)
        self.technique_name = imports.get("technique_name", technique_name)
        self.decision_uuid = imports.get("decision_uuid", None)
        self.decision_timestamp = imports.get("decision_timestamp", None)
        self.decision_label = imports.get("decision_label", decision_label)
        self.access = imports.get("access", access)
        self.actual = imports.get("actual", actualizer)
        self.actual_pars = imports.get("actual_pars", actual_pars)
        self.result_dict = imports.get("result_dict", result_dict)
        if self.decision_uuid is None:
            self.gen_uuid_decision()

    def as_dict(self):
        d = vars(self)
        attr_only = {
            k: v
            for k, v in d.items()
            if type(v) != types.FunctionType and not k.startswith("__")
        }
        return attr_only

    def gen_uuid_decision(self):
        "server_name can be any string used in generating random uuid"
        if self.decision_uuid:
            print(f"decision_uuid: {self.decision_uuid} already exists")
        else:
            self.decision_uuid = gen_uuid(self.orch_name)
            print(f"decision_uuid: {self.decision_uuid} assigned")

    def set_dtime(self, offset: float = 0):
        dtime = datetime.now()
        dtime = datetime.fromtimestamp(dtime.timestamp() + offset)
        self.decision_timestamp = dtime.strftime("%Y%m%d.%H%M%S%f")


class Action(Decision):
    "Sample-process identifier class."

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        action_server: str = None,
        action_name: str = None,
        action_params: dict = {},
        action_enum: str = None,
        action_abbr: str = None,
        save_rcp: bool = False,
        save_data: Union[bool, int, str] = None,
        start_condition: Union[int, dict] = 3,
        plate_id: Optional[int] = None,
        samples_in: Optional[dict] = None,
        # samples_out: Optional[dict] = None,
    ):
        super().__init__(inputdict)  # grab decision keys
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.action_uuid = imports.get("action_uuid", None)
        self.action_queue_time = imports.get("action_queue_time", None)
        self.action_server = imports.get("action_server", action_server)
        self.action_name = imports.get("action_name", action_name)
        self.action_params = imports.get("action_params", action_params)
        self.action_enum = imports.get("action_enum", action_enum)
        self.action_abbr = imports.get("action_abbr", action_abbr)
        self.save_rcp = imports.get("save_rcp", save_rcp)
        self.save_data = imports.get("save_data", save_data)
        self.start_condition = imports.get("start_condition", start_condition)
        self.plate_id = imports.get("plate_id", plate_id)
        self.samples_in = imports.get("samples_in", samples_in)
        # the following attributes are set during Action dispatch but can be imported
        self.samples_out = imports.get("samples_out", None)
        self.file_dict = defaultdict(lambda: defaultdict(dict))
        self.file_dict.update(imports.get("file_dict", {}))
        self.file_paths = imports.get("file_paths", [])
        self.data = imports.get("data", [])
        self.output_dir = imports.get("output_dir", None)
        self.column_names = imports.get("column_names", None)
        self.header = imports.get("header", None)
        self.file_type = imports.get("file_type", None)
        self.filename = imports.get("filename", None)
        self.file_group = imports.get("file_group", None)
        self.error_code = imports.get("error_code", "0")

        check_args = {"server": self.action_server, "name": self.action_name}
        missing_args = [k for k, v in check_args.items() if v is None]
        if missing_args:
            print(
                f'Action {" and ".join(missing_args)} not specified. Placeholder actions will only affect the action queue enumeration.'
            )
        if self.action_uuid is None:
            self.gen_uuid_action()

    def gen_uuid_action(self):
        if self.action_uuid:
            print(f"action_uuid: {self.action_uuid} already exists")
        else:
            self.action_uuid = gen_uuid(self.action_name)
            print(f"action_uuid: {self.action_uuid} assigned")

    def set_atime(self, offset: float = 0.0):
        atime = datetime.now()
        if offset is not None:
            atime = datetime.fromtimestamp(atime.timestamp() + offset)
        self.action_queue_time = atime.strftime("%Y%m%d.%H%M%S%f")

    # def return_finished(self):
    #     return return_finishedact(
    #         technique_name=self.technique_name,
    #         access=self.access,
    #         orch_name=self.orch_name,
    #         decision_timestamp=self.decision_timestamp,
    #         decision_uuid=self.decision_uuid,
    #         decision_label=self.decision_label,
    #         actualizer=self.actualizer,
    #         actual_pars=self.actual_pars,
    #         result_dict=self.result_dict,
    #         action_server=self.action_server,
    #         action_queue_time=self.action_queue_time,
    #         action_real_time=self.action_real_time,
    #         action_name=self.action_name,
    #         action_params=self.action_params,
    #         action_uuid=self.action_uuid,
    #         action_enum=self.action_enum,
    #         action_abbr=self.action_abbr,
    #         actionnum=self.actionnum,
    #         start_condition=self.start_condition,
    #         save_rcp=self.save_rcp,
    #         save_data=self.save_data,
    #         plate_id=self.plate_id,
    #         samples_in=self.samples_in,
    #         samples_out=self.samples_out,
    #         output_dir=self.output_dir,
    #         file_dict=self.file_dict,
    #         column_names=self.column_names,
    #         header=self.header,
    #         data=self.data,
    #     )

    # def return_running(self):
    #     return return_runningact(
    #         technique_name=self.technique_name,
    #         access=self.access,
    #         orch_name=self.orch_name,
    #         decision_timestamp=self.decision_timestamp,
    #         decision_uuid=self.decision_uuid,
    #         decision_label=self.decision_label,
    #         actualizer=self.actualizer,
    #         actual_pars=self.actual_pars,
    #         result_dict=self.result_dict,
    #         action_server=self.action_server,
    #         action_queue_time=self.action_queue_time,
    #         action_real_time=self.action_real_time,
    #         action_name=self.action_name,
    #         action_params=self.action_params,
    #         action_uuid=self.action_uuid,
    #         action_enum=self.action_enum,
    #         action_abbr=self.action_abbr,
    #         actionnum=self.actionnum,
    #         start_condition=self.start_condition,
    #         plate_id=self.plate_id,
    #         save_rcp=self.save_rcp,
    #         save_data=self.save_data,
    #         samples_in=self.samples_in,
    #         samples_out=self.samples_out,
    #         output_dir=self.output_dir,
    #     )

