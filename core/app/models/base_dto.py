from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class BaseError(BaseModel):
    code: str
    message: str
    
    def to_json(self):
        return self.model_dump()


class ErrorBaseResponse(BaseModel):
    error: BaseError = None
    success: bool

    def to_json(self):
        return self.model_dump()


class ChatRequest(BaseModel):
    message: str
    collection_id: UUID
    room_id: UUID
    evaluate: Optional[bool] = False


class TaskSubmittedModel(BaseModel):
    task_id: str
    collection_id: str
    filename: str

    def to_dict(self):
        return {
            "taskId": self.task_id,
            "collectionId": self.collection_id,
            "filename": self.filename
        }

    class Config:
        from_attributes = True


class TaskResultModel(BaseModel):
    task_id: str
    task_status: str
    task_result: dict = None
    error_message: str = None

    def to_dict(self):
        return {
            "taskId": self.task_id,
            "taskStatus": self.task_status,
            "taskResult": self.task_result,
            "errorMessage": self.error_message
        }

    class Config:
        from_attributes = True


class FileAlreadyExists(Exception):
    pass
    