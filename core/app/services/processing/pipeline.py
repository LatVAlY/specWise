
from app.services.processing.data_processing import DataProcessingService


class Pipelines:
    """ the whole pipline for the document processing and creation"""
    def __init__(self):
        # self.mongo_db_repo = MongoDbRepository()
        # self.vector_db_repo = VectorDbRepository()
        # self.llm_service = OpenAILlmService()

        self.data_processing_service = DataProcessingService()
        pass

    def process_data_from_file(
        self,
        user_id: str,
        collection_id: str,
        file_path: str,
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
        file_path : str
            The path to the file that needs to be processed.
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
            # Extract pages as text
            pages = self.data_processing_service.extract_pages_as_text(file_path)
            # Process data
            parsed_items = self.data_processing_service.process_data(pages)
            # Store processed data in the database
            # self.mongo_db_repo.store_data(user_id, collection_id, parsed_items)

            # TODO: vector db input

            # self.vector_db_repo.store_data(user_id, collection_id, parsed_items)
            # self.llm_service.categorize()

            return {
                "status": "success",
                "message": "Data processed successfully",
                "data": parsed_items,
            }
        except Exception as e:
            print(f"Error processing data: {e}")
            raise e