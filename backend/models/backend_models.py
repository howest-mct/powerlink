from pydantic import BaseModel, ConfigDict
import datetime


class P1BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


# region Models ---------------------------------


class Log(P1BaseModel):
    log_id: int
    datetime: datetime.datetime
    value: float
    component_id: int


class Schedule(P1BaseModel):
    schedule_id: int
    schedule_name: str
    start_time: str
    end_time: str
    value: float
    value_unit: str
    enabled: int
    type_id: int
    component_id: int


# endregion Models ********************************


# region DTOModels ---------------------------------


class DTOLog(P1BaseModel):
    value: float
    component_id: int


class DTOSchedule(P1BaseModel):
    schedule_id: int
    start_time: str
    end_time: str
    value: float
    enabled: int


# endregion DTOModels ********************************
