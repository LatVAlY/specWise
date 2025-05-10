from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime
from bson import ObjectId
from app.models.models import FileModel, ItemDto, TaskDto, TaskStatus
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from app.envirnoment import config

import logging

logger = logging.getLogger(__name__)
class PyObjectId(ObjectId):
    """Custom type for handling MongoDB's ObjectId"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class MongoDBService:
    """Service for handling MongoDB operations related to tasks and files"""
    
    def __init__(self):
        """
        Initialize the MongoDB service
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name to use
        """
        mongodb_connection_string =config.get("MONGO_DB_CONNECTION", "mongodb://localhost:27018")
        mongodb_database_name =config.get("MONGODB_DATABASE", "specwise")
    
        self.client = MongoClient(mongodb_connection_string)
        self.db = self.client[mongodb_database_name]
        self.tasks_collection = self.db["tasks"]
        self.files_collection = self.db["files"]
    
    def _setup_indexes(self):
        """Set up required indexes for collections"""
        # Tasks collection indexes
        self.tasks_collection.create_index("id", unique=True)
        self.tasks_collection.create_index("collection_id")
        self.tasks_collection.create_index("status")
        
        # Files collection indexes
        self.files_collection.create_index("id", unique=True)
        self.files_collection.create_index("customer_number")
        self.files_collection.create_index("task_id")
        self.files_collection.create_index("filename")
    
    def insert_task(self, task: TaskDto) -> UUID:
        """
        Insert a new task into the database
        
        Args:
            task: TaskDto object to insert
            
        Returns:
            UUID of the inserted task
            
        Raises:
            DuplicateKeyError: If a task with the same ID already exists
        """
        try:
            task_dict = task.to_dict()
            task_dict["id"] = str(task_dict["id"])  # Convert UUID to string for MongoDB
            task_dict["collectionId"] = str(task_dict["collectionId"])  # Convert UUID to string
            
            result = self.tasks_collection.insert_one(task_dict)
            if result.acknowledged:
                return task.id
            raise Exception("Task insertion not acknowledged")
        except DuplicateKeyError:
            raise DuplicateKeyError(f"Task with ID {task.id} already exists")
        except Exception as e:
            raise Exception(f"Failed to insert task: {str(e)}")
    
    def update_task_status(self, task_id: UUID, status: TaskStatus, description: Optional[str] = None) -> TaskDto:
        """
        Update the status of a task
        
        Args:
            task_id: UUID of the task to update
            status: New TaskStatus value
            description: Optional additional information to update
            
        Returns:
            Updated TaskDto
            
        Raises:
            Exception: If task not found or update fails
        """
        try:
            update_dict = {
                "status": status,
                "updatedAt": int(datetime.now().timestamp() * 1000)
            }
            
            if description is not None:
                update_dict["description"] = description
            
            result = self.tasks_collection.find_one_and_update(
                {"id": str(task_id)},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
            
            if not result:
                raise Exception(f"Task with ID {task_id} not found")
            
            # Convert the MongoDB document back to TaskDto
            return self._document_to_task_dto(result)
        except Exception as e:
            raise Exception(f"Failed to update task status: {str(e)}")
    
    def get_all_tasks(self) -> List[TaskDto]:
        """
        Get all tasks in the database
        Returns:
            List of TaskDto objects
        """
        cursor = self.tasks_collection.find()
        return [self._document_to_task_dto(doc) for doc in cursor]

    def get_task_by_id(self, task_id: UUID) -> TaskDto:
        """
        Get a task by its ID
        
        Args:
            task_id: UUID of the task to retrieve
            
        Returns:
            TaskDto object
            
        Raises:
            Exception: If task not found
        """
        task_doc = self.tasks_collection.find_one({"id": str(task_id)})
        if not task_doc:
            raise Exception(f"Task with ID {task_id} not found")
        
        return self._document_to_task_dto(task_doc)
    
    def delete_task(self, task_id: UUID) -> bool:
        """
        Delete a task by its ID
        
        Args:
            task_id: UUID of the task to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            Exception: If task not found or deletion fails
        """
        result = self.tasks_collection.delete_one({"id": str(task_id)})
        if result.deleted_count == 0:
            raise Exception(f"Task with ID {task_id} not found")
        
        return True
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskDto]:
        """
        Get all tasks with a specific status
        
        Args:
            status: TaskStatus value to filter by
            
        Returns:
            List of TaskDto objects
        """
        cursor = self.tasks_collection.find({"status": status})
        return [self._document_to_task_dto(doc) for doc in cursor]
    
    def get_tasks_by_collection(self, collection_id: UUID) -> List[TaskDto]:
        """
        Get all tasks for a specific collection
        
        Args:
            collection_id: UUID of the collection
            
        Returns:
            List of TaskDto objects
        """
        cursor = self.tasks_collection.find({"collectionId": str(collection_id)})
        return [self._document_to_task_dto(doc) for doc in cursor]
    
    def insert_file(self, file_model: FileModel) -> UUID:
        """
        Insert a new file document into the database
        
        Args:
            file_model: FileModel object to insert
            
        Returns:
            UUID of the inserted file document
            
        Raises:
            DuplicateKeyError: If a file with the same ID already exists
        """
        try:
            file_dict = file_model.dict()
            file_dict["id"] = str(file_dict["id"])  # Convert UUID to string for MongoDB
            
            if file_dict.get("task_id"):
                file_dict["task_id"] = str(file_dict["task_id"])
            
            # Convert items to dictionaries with proper serialization
            if "items" in file_dict and file_dict["items"]:
                items_dict = []
                for item in file_dict["items"]:
                    item_dict = {
                        "sku": item["sku"],
                        "name": item["name"],
                        "text": item["text"],
                        "quantity": item["quantity"],
                        "quantityunit": item["quantityunit"],
                        "price": item["price"],
                        "priceunit": item["priceunit"],
                        "commission": item["commission"],
                        "confidence": item["confidence"]
                    }
                    
                    items_dict.append(item_dict)
                
                file_dict["items"] = items_dict
            
            result = self.files_collection.insert_one(file_dict)
            if result.acknowledged:
                return file_model.id
            raise Exception("File insertion not acknowledged")
        except DuplicateKeyError:
            raise DuplicateKeyError(f"File with ID {file_model.id} already exists")
        except Exception as e:
            raise Exception(f"Failed to insert file: {str(e)}")
    
    def update_file_items(self, file_id: UUID, items: List[ItemDto]) -> FileModel:
        """
        Update the items for a file
        
        Args:
            file_id: UUID of the file to update
            items: List of ItemDto objects
            
        Returns:
            Updated FileModel
            
        Raises:
            Exception: If file not found or update fails
        """
        try:
            # Convert items to dictionaries
            items_dict = []
            for item in items:
                item_dict = {
                    "sku": item.sku,
                    "name": item.name,
                    "text": item.text,
                    "quantity": item.quantity,
                    "quantityunit": item.quantityunit,
                    "price": item.price,
                    "priceunit": item.priceunit,
                    "commission": item.commission,
                    "confidence": item.confidence
                }
                
                items_dict.append(item_dict)
            
            update_dict = {
                "items": items_dict,
                "updated_at": int(datetime.now().timestamp() * 1000)
            }
            
            result = self.files_collection.find_one_and_update(
                {"id": str(file_id)},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
            
            if not result:
                raise Exception(f"File with ID {file_id} not found")
            
            # Convert the MongoDB document back to FileModel
            return self._document_to_file_model(result)
        except Exception as e:
            raise Exception(f"Failed to update file items: {str(e)}")

    def update_xml_content(self, file_id: UUID, xml_content: str) -> FileModel:
        """
        Update the XML content for a file
        
        Args:
            file_id: UUID of the file to update
            xml_content: XML content as string
            
        Returns:
            Updated FileModel
            
        Raises:
            Exception: If file not found or update fails
        """
        try:
            update_dict = {
                "xml_content": xml_content,
                "is_xml_generated": True,
                "updated_at": int(datetime.now().timestamp() * 1000)
            }
            
            result = self.files_collection.find_one_and_update(
                {"id": str(file_id)},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
            
            if not result:
                raise Exception(f"File with ID {file_id} not found")
            
            # Convert the MongoDB document back to FileModel
            return self._document_to_file_model(result)
        except Exception as e:
            raise Exception(f"Failed to update XML content: {str(e)}")
    
    def get_file_by_id(self, file_id: UUID) -> FileModel:
        """
        Get a file by its ID
        
        Args:
            file_id: UUID of the file to retrieve
            
        Returns:
            FileModel object
            
        Raises:
            Exception: If file not found
        """
        try:
            file_doc = self.files_collection.find_one({"id": str(file_id)})
            if not file_doc:
                raise Exception(f"File with ID {file_id} not found")
            return self._document_to_file_model(file_doc)
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to retrieve file: {str(e)}")
        
    
    def get_files_by_customer(self, customer_number: str) -> List[FileModel]:
        """
        Get all files for a specific customer
        
        Args:
            customer_number: Customer number to filter by
            
        Returns:
            List of FileModel objects
        """
        cursor = self.files_collection.find({"customer_number": customer_number})
        return [self._document_to_file_model(doc) for doc in cursor]
    
    def get_files_by_task(self, task_id: UUID) -> List[FileModel]:
        """
        Get all files associated with a specific task
        
        Args:
            task_id: UUID of the task to filter by
            
        Returns:
            List of FileModel objects
        """
        cursor = self.files_collection.find({"task_id": str(task_id)})
        return [self._document_to_file_model(doc) for doc in cursor]
    
    def get_files(self) -> List[FileModel]:
        """
        Get all files in the database
        
        Returns:
            List of FileModel objects
        """
        cursor = self.files_collection.find()
        return [self._document_to_file_model(doc) for doc in cursor]

    def delete_file(self, file_id: UUID) -> bool:
        """
        Delete a file by its ID
        
        Args:
            file_id: UUID of the file to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            Exception: If file not found or deletion fails
        """
        result = self.files_collection.delete_one({"id": str(file_id)})
        if result.deleted_count == 0:
            raise Exception(f"File with ID {file_id} not found")
            
        return True
    
    def _document_to_task_dto(self, doc: Dict[str, Any]) -> TaskDto:
        """Convert a MongoDB document to a TaskDto object"""
        # Convert MongoDB's _id to string if needed
        if "_id" in doc:
            doc.pop("_id")
            
        # Handle specific field mappings between MongoDB and TaskDto
        task_dict = {
            "id": UUID(doc["id"]),
            "collection_id": UUID(doc["collectionId"]),
            "description": doc["description"],
            "file_name": doc.get("fileName"),
            "status": TaskStatus(doc["status"]),
            "created_at": doc["createdAt"],
            "updated_at": doc.get("updatedAt")
        }
        
        return TaskDto(**task_dict)
    
    def _document_to_file_model(self, doc: Dict[str, Any]) -> FileModel:
        """Convert a MongoDB document to a FileModel object"""
        # Convert MongoDB's _id to string if needed
        if "_id" in doc:
            doc.pop("_id")
            
        # Convert string IDs back to UUID
        doc["id"] = UUID(doc["id"])
        if doc.get("task_id"):
            doc["task_id"] = UUID(doc["task_id"])
            
        # Convert items if they exist
        if "items" in doc and doc["items"]:
            items = []
            for item_dict in doc["items"]:
                item = {
                    "sku": item_dict["sku"],
                    "name": item_dict["name"],
                    "text": item_dict["text"],
                    "quantity": item_dict["quantity"],
                    "quantityunit": item_dict["quantityunit"],
                    "price": item_dict["price"],
                    "priceunit": item_dict["priceunit"],
                    "commission": item_dict["commission"],
                    "confidence": item_dict["confidence"]
                }
                items.append(ItemDto(**item))
            
            doc["items"] = items
            
        return FileModel(**doc)
