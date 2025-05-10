import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel

from app.services.mongo_db import MongoDBService
from app.models.models import FileModel, TaskDto, TaskStatus
from app.celery_tasks.tasks import run_file_data_processing
from app.models.validator import return_generic_http_error
from app.worker import app
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

taskRouter = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


# Response models for consistent API
class FileResponse(BaseModel):
    file: FileModel
    message: str


class FilesListResponse(BaseModel):
    files: List[FileModel]
    count: int
    message: str


class TaskResponse(BaseModel):
    task: TaskDto
    message: str

# Dependency for MongoDB service
def get_db_service():
    return MongoDBService()


#  get all tasks
@taskRouter.get("/", response_model=List[TaskDto])
async def get_all_tasks(
    db: MongoDBService = Depends(get_db_service),
):
    """
    Get all tasks in the system
    """
    try:
        logger.info("Retrieving all tasks")
        tasks = db.get_all_tasks()
        logger.info(f"Retrieved {len(tasks)} tasks")
        return tasks
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tasks: {str(e)}",
        )

@taskRouter.get("/task/{task_id}/status", response_model=TaskResponse)
async def get_task_status(
    task_id: UUID = Path(..., description="UUID of the task to check status"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Get the status of a specific task
    """
    try:
        task = db.get_task_by_id(task_id)
        return TaskResponse(task=task, message=f"Task status: {task.status}")
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task not found: {str(e)}"
        )


@taskRouter.put("/task/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID = Path(..., description="UUID of the task to update"),
    status: TaskStatus = Query(..., description="New status for the task"),
    additional_info: Optional[str] = Query(
        None, description="Optional additional information"
    ),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Update the status of a task
    """
    try:
        updated_task = db.update_task_status(
            task_id=task_id, status=status, additional_info=additional_info
        )

        return TaskResponse(
            task=updated_task, message=f"Task status updated to {status}"
        )
    except Exception as e:
        logger.error(f"Error updating task {task_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error updating task status: {str(e)}",
        )


@taskRouter.delete("/{taskt_id}")
async def delete_file(
    taskt_id: UUID = Path(..., description="UUID of the file to delete"),
):
    """
    Delete a task by its ID
    """
    try:
        db = get_db_service()
        db.delete_task(taskt_id)
        task_result = AsyncResult(taskt_id, app=run_file_data_processing.app)
        task_result.revoke(terminate=True)
    except Exception as e:
        logger.error(e)
        return return_generic_http_error()