from celery.exceptions import MaxRetriesExceededError
import os
import sys

from app.envirnoment import config
from app.services.processing.pipeline import Pipelines
from app.worker import app

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'run_pipelines'))

pipelines = Pipelines()


@app.task(bind=True)
async def run_file_data_processing(self, user_id: str, collection_id: str, file_path: str, task_id: str):
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
        The task state is updated to 'FAILURE' with error details.
    """
    try:
        # Call the pipeline's process_data_from_file method to handle the file processing
        return await pipelines.process_data_from_file(
            user_id=user_id,
            collection_id=collection_id,
            file_path=file_path,
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

    """
    Send an email based on a specified template as a Celery task.
    
    This task handles email sending with automatic retry logic for specific
    error codes. It uses templates defined in the EmailTemplateType enum
    to format and send emails.
    
    Parameters:
    -----------
    self : Task
        The Celery task instance (automatically passed when bind=True).
    email_template : str
        The name of the email template to use (must match a value in EmailTemplateType enum).
    retry_error_codes : list[str], optional
        HTTP error codes that should trigger a retry (default: [401, 500, 400]).
    **kwargs : dict
        Additional parameters to pass to the email template, such as:
        - recipient_email: Email address of the recipient
        - subject_params: Parameters for the email subject
        - body_params: Parameters for the email body
        
    Returns:
    --------
    dict
        Results of the email sending operation with metadata.
        
    Raises:
    -------
    MaxRetriesExceededError
        If the maximum number of retries is exceeded.
    Exception
        Any other exception that occurs during email sending.
    """
    try:
        # Convert the template string to the corresponding enum value and send the email
        result = pipelines.send_email(EmailTemplateType[email_template], **kwargs)
        
    except Exception as e:
        # Check if the exception has an error code that should trigger a retry
        if hasattr(e, 'code') and e.code in retry_error_codes:
            loguru.logger.error(f"Retrying email task due to error code {e.code}: {e}")
            
            try:
                self.retry(default_retry_delay=60, max_retries=3, retry_backoff=True)
                
            except MaxRetriesExceededError as retry_error:
                loguru.logger.error("Max retries exceeded for email sending task")
                
                self.update_state(state='FAILURE', meta={
                    'exc_type': type(retry_error).__name__, 
                    'exc_message': str(retry_error)
                })
                
                raise retry_error
        else:
            # For non-retriable errors, log and update task state
            loguru.logger.error(f"Email sending failed with error: {e}")
            
            self.update_state(state='FAILURE', meta={
                'exc_type': type(e).__name__, 
                'exc_message': str(e)
            })
            
            # Re-raise the exception to be handled by Celery's error handling
            raise e

    # Return the result if email sending was successful
    return result