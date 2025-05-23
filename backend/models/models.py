from pydantic import BaseModel


class DTOLampStatus(BaseModel):
    nieuwe_status: int


class LampStatus(BaseModel):
    lamp: int
    status: int
