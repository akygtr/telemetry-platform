from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReadingIn(BaseModel):
    machine_id: str = Field(min_length=1, max_length=64)
    tag: str = Field(min_length=1, max_length=64)
    value: float


class ReadingOut(ReadingIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
