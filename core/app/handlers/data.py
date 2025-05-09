import uuid
from pathlib import Path
from typing import List
import logging

from core.app.models.base_dto import ErrorBaseResponse, FileAlreadyExists
from core.app.models.models import TaskDto
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import pika
from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, File, Query
from app.celery_tasks.tasks import (
    run_file_data_processing,
)
from app.constants import ALLOWED_EXTENSIONS
from app.envirnoment import config
from core.app.models.validator import return_generic_http_error, return_http_error

logger = logging.getLogger(__name__)

dataRouter = APIRouter(
    prefix="/data",
    tags=["data"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@dataRouter.post(
    "/", name="Upload Data", response_model=List[TaskDto], operation_id="upload_data"
)
async def load_data(
    collection_id: uuid.UUID,
    files: List[UploadFile] = File(...),
):
    for f in files:
        logger.info(f"received {f.filename} ")
    try:
        if not files:
            return return_http_error(
                code="B0010", message="At least one file must be uploaded."
            )
        try:
            test_rabbitmq_connection()
        except Exception as rabbitmq_error:
            logger.error(f"RabbitMQ connection error: {rabbitmq_error}")
            return return_http_error(
                code="R0010", message="Unable to establish RabbitMQ connection."
            )

        tasks = []
        for file in files:
            if not (Path(file.filename).suffix in ALLOWED_EXTENSIONS):
                return return_http_error(
                    code="B0015", message="File format not supported"
                )
            task_id = run_file_data_processing.apply_async(
                args=[
                    str(uuid.uuid4()),
                    str(collection_id),
                    file.file,
                    str(file.filename),
                ]
            )
            task = TaskDto(
                task_id=task_id.id,
                collection_id=str(collection_id),
                filename=file.filename,
            )
            tasks.append(task)
        return tasks
    except FileAlreadyExists as e:
        logger.error(f"Tried Uploading File that already exists")
        return JSONResponse(
            status_code=400, content=jsonable_encoder({"detail": "FILE_ALREADY_EXISTS"})
        )
    except Exception as e:
        logger.error(e)
        return return_generic_http_error()


def test_rabbitmq_connection():
    rabbitmq_address = config["RABBITMQ_ADDRESS"]
    rabbitmq_user = config["RABBITMQ_DEFAULT_USER"]
    rabbitmq_password = config["RABBITMQ_DEFAULT_PASS"]
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)

    rabbitmq_host, rabbitmq_port = rabbitmq_address.split(":")
    try:

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host, port=rabbitmq_port, credentials=credentials
            )
        )
        connection.close()
    except Exception as e:
        raise Exception("RabbitMQ connection failed") from e


@dataRouter.get(
    "/task/files", response_model=list[TaskDto], operation_id="get_files_by_task_ids"
)
async def get_task_ids(
    task_ids: list[str] = Query(...),
):
    try:
        # get tasks from MongoDB
        task_service = TaskService()
        return await task_service.get_multiple_tasks_by_ids(
            list(map(uuid.UUID, task_ids))
        )
    except Exception as e:
        logger.error(e)
        return return_generic_http_error()


@dataRouter.delete(
    "/task", response_model=ErrorBaseResponse, operation_id="cancel_task_by_task_id"
)
async def cancel_task_id(task_id: str):
    try:
        task_result = AsyncResult(task_id, app=run_file_data_processing.app)
        task_result.revoke(terminate=True)
    except Exception as e:
        logger.error(e)
        return return_generic_http_error()
