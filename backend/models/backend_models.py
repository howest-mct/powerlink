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
    room_id: int
    room_name: str
    type_name: str


class Card(P1BaseModel):
    inhabitant_id: int
    first_name: str
    last_name: str
    card_id: str


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


class DTOCard(P1BaseModel):
    card_id: int


# endregion DTOModels ********************************
