import logging
from celery.exceptions import MaxRetriesExceededError
import os
import sys

from app.envirnoment import config
from app.services.processing.pipeline import Pipelines
from app.worker import app

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'run_pipelines'))

pipelines = Pipelines()

logger = logging.getLogger(__name__)


@app.task(bind=True)
def run_file_data_processing(self, user_id: str, collection_id: str, filename: str, task_id: str):
    """
    Process data from an uploaded file asynchronously as a Celery task.
    
    This task extracts content from various file types, processes the data,
    and stores it in the associated collection. The task can optionally
    extract images from documents if specified.
    
    Parameters:
    -----------
    self : Task
        The Celery task instance (automatically passed when bind=True).
    user_id : str
    collection_id : str
        The ID of the collection where processed data will be stored.
    filename : str
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
        The task state is updated to 'FAILURE' with error details.
    """
    try:
        logger.info(f"Processing file: {filename} for user: {user_id} in collection: {collection_id}")
        # Call the pipeline's process_data_from_file method to handle the file processing
        return pipelines.process_data_from_file(
            user_id=user_id,
            collection_id=collection_id,
            filename=filename,
            task_id=task_id,
        )
    except Exception as e:
        print(f"Something went wrong during file processing: {e}")
        
        # Update the task state to indicate failure
        self.update_state(state='FAILURE', meta={
            'exc_type': type(e).__name__, 
            'exc_message': str(e)
        })
        
        raise e
