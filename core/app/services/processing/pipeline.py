import logging
import os
from typing import List
from uuid import UUID
from app.services.processing.data_processing import DataProcessingService

from app.services.processing.data_processing import DataProcessingService
from app.services.processing.vectore_client import VectoreDatabaseClient
from app.constants import PROCESSING_FILE_PATH
from app.models.models import FileModel, ItemDto, TaskStatus
from app.services.llm.llm import OpenAILlmService
from app.services.mongo_db import MongoDBService

logger = logging.getLogger(__name__)


class Pipelines:
    """the whole pipline for the document processing and creation"""

    def __init__(self):
        self.vector_db_service = VectoreDatabaseClient()
        self.llm_service = OpenAILlmService()
        self.mongoDbService = MongoDBService()
        self.data_processing_service = DataProcessingService()
        pass

    def process_data_from_file(
        self,
        user_id: str,
        collection_id: str,
        filename: str,
        task_id: str,
    ):
        """
        Process data from an uploaded file and store it in the associated collection.

        This method extracts content from various file types, processes the data,
        and stores it in the associated collection. The task can optionally
        extract images from documents if specified.

        Parameters:
        -----------
        user_id : str
            The ID of the user who uploaded the file.
        collection_id : str
            The ID of the collection where processed data will be stored.
        file_name : str
            The name of the file that needs to be processed.
        task_id : str
            A unique identifier for tracking this specific processing task.

        Returns:
        --------
        dict
            Results of the processing operation with metadata.

        Raises:
        -------
        Exception
            Any exception that occurs during processing is logged and re-raised.
        """
        
        try:
            file_path = f"{PROCESSING_FILE_PATH}/{filename}"
            logger.info(f"Starting data processing for file: {file_path}")

            self.mongoDbService.update_task_status(
                task_id=UUID(task_id),
                status=TaskStatus.in_progress,
            )
            logger.info(f"Task {task_id} marked as in progress")

            pages = self.data_processing_service.extract_pages_as_text(file_path)
            logger.info(f"Extracted {len(pages)} pages from the file")

            parsed_items = self.data_processing_service.process_data(pages)
            logger.info(f"Parsed {len(parsed_items)} items from document")

            items_dto: List[ItemDto] = self.llm_service.categorize(parsed_items)
            logger.info(f"LLM categorized {len(items_dto)} items")

            file = FileModel(
                id=UUID.uuid4(),
                filename=filename,
                filepath=file_path,
                customer_number=user_id,
                task_id=task_id,
                items=items_dto,
            )
            self.mongoDbService.insert_file(file_model=file)
            logger.info(f"Inserted file record into MongoDB: {file.id}")

            self.vector_db_repo.store_data(user_id, collection_id, parsed_items)
            logger.info(f"Stored parsed items in vector database under collection {collection_id}")

            self.mongoDbService.update_task_status(
                task_id=UUID(task_id),
                status=TaskStatus.completed,
            )
            logger.info(f"Task {task_id} marked as completed")

            self.clean_up(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")

            return {
                "status": "success",
                "message": "Data processed successfully",
            }

        except Exception as e:
            logger.error(f"Error processing data for task {task_id}: {e}", exc_info=True)
            self.mongoDbService.update_task_status(
                task_id=UUID(task_id),
                status=TaskStatus.failed,
            )
            return {
                "status": "error",
                "message": str(e),
            }

    def clean_up(self, file_path: str):
        """
        Clean up the file after processing.

        Parameters:
        -----------
        file_path : str
            The path to the file that needs to be cleaned up.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted successfully")
            else:
                print(f"The file {file_path} does not exist")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
