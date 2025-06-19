from pydantic import BaseModel, ConfigDict
import datetime


class P1BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


# region Models ---------------------------------


class Component(P1BaseModel):
    component_id: int
    component_name: str
    value_unit: str
    room_id: int


class Room(P1BaseModel):
    room_id: int
    room_name: str


class ComponentPage(P1BaseModel):
    component_id: int
    page_id: int


class DTOComponentPage(P1BaseModel):
    component_id: int
    page_id: int


class Log(P1BaseModel):
    log_id: int
    datetime: datetime.datetime
    value: float
    component_id: int
    component_name: str
    value_unit: str
    room_id: int
    room_name: str


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


class UpdatedSchedule(P1BaseModel):
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


class Card(P1BaseModel):
    inhabitant_id: int
    first_name: str
    last_name: str
    card_id: str


class EnergyLog(P1BaseModel):
    total_kwh: float


class HistoryLog(P1BaseModel):
    chart_date: datetime.datetime
    average_value: float


class LogAmount(P1BaseModel):
    component_id: int
    log_amount: int


class LogCountHistory(P1BaseModel):
    component_id: int
    chart_date: datetime
    log_count: int


class LastEntered(P1BaseModel):
    first_name: str


class Inhabitant(P1BaseModel):
    inhabitant_id: int
    first_name: str
    last_name: str
    card_id: str


class DTOInhabitant(P1BaseModel):
    first_name: str
    last_name: str
    card_id: str


class PasswordVerificationRequest(BaseModel):
    password: str
    component_id: int


class PasswordVerificationResponse(BaseModel):
    valid: bool
    message: str


# endregion Models ********************************


# region DTOModels ---------------------------------


class DTOLog(P1BaseModel):
    value: float
    component_id: int


class DTOSchedule(P1BaseModel):
    start_time: str
    end_time: str
    value: float
    enabled: int


class DTOCard(P1BaseModel):
    card_id: int


# endregion DTOModels ********************************
