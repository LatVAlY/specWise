from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from openai import BaseModel

class TaskStatus(str, Enum):
    pending = "PENDING"
    in_progress = "IN_PROGRESS"
    completed = "COMPLETED"
    failed = "FAILED"
    canceled = "CANCELED"
    updating = "UPDATING"
class TaskDto(BaseModel):
    id: UUID
    collection_id: UUID
    description: Optional[str] = None
    file_name: Union[str, None]
    status: TaskStatus
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


    def to_dict(self):
        return {
            "id": self.id,
            "collectionId": self.collection_id,
            "description": self.description,
            "fileName": self.file_name,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }


class ClassificationItem(BaseModel):
    """Model for items with classification results"""
    classification: str
    confidence: float
    match: bool
    relevant: bool

class ItemDto(BaseModel):
    ref_no: str
    description: str
    quantity: float
    unit: str
    classification_item: Optional[ClassificationItem] = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            ref_no=data.get("ref_no"),
            description=data.get("description"),
            quantity=data.get("quantity"),
            unit=data.get("unit"),
        )
    
class FileModel(BaseModel):
    """File metadata model for storage in MongoDB"""
    id: UUID
    filename: str
    filepath: str
    customer_number: str
    task_id: Optional[UUID] = None
    items: List[ItemDto] = []
    is_xml_generated: bool = False
    xml_content: Optional[str] = None
    created_at: int = int(datetime.now().timestamp() * 1000)
    updated_at: Optional[int] = None