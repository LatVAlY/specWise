import datetime

from openai import BaseModel


class TaskDto(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime