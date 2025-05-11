import uuid
from pathlib import Path
from typing import List
import logging

from app.models.base_dto import FileAlreadyExists
from app.models.models import TaskDto, TaskStatus
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import pika
from fastapi import APIRouter, Form, UploadFile, File, Query
from app.celery_tasks.tasks import (
    run_file_data_processing,
)
from app.constants import ALLOWED_EXTENSIONS
from app.envirnoment import config
from app.models.validator import return_generic_http_error, return_http_error
from app.services.mongo_db import MongoDBService
from app.utils.file_utils import get_current_time_in_timezone, save_file

logger = logging.getLogger(__name__)

dataRouter = APIRouter(
    prefix="/data",
    tags=["data"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


def generate_collection_id():
    """
    Generate a unique collection ID.
    """
    return str(uuid.uuid4())


@dataRouter.post(
    "/",
    name="Upload Data",
    response_model=List[TaskDto],
    operation_id="upload_data",
)
async def load_data(
    files: List[UploadFile] = File(...),
    customer_id: str = Form(...) # Add this line
):
    db = MongoDBService()
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
        collection_id = generate_collection_id()

        tasks = []
        for file in files:
            if not (Path(file.filename).suffix in ALLOWED_EXTENSIONS):
                return return_http_error(
                    code="B0015", message="File format not supported"
                )
            file_path = save_file(file)
            task_id = str(uuid.uuid4())
            task_dto = TaskDto(
                id=task_id,
                collection_id=collection_id,
                file_name=file.filename,
                status=TaskStatus.pending,
                created_at=get_current_time_in_timezone(),
            )
            logger.info(f"Saving file {file.filename} to {file_path}")
            db.insert_task(task=task_dto)
            logger.info(f"in collection: {collection_id}")
            run_file_data_processing.apply_async(
                args=[
                    customer_id,
                    collection_id,
                    file.filename,
                    task_id,
                ],
                task_id=task_id,
            )
            tasks.append(task_dto)
        return tasks
    except FileAlreadyExists as e:
        logger.error(f"Tried Uploading File that already exists")
        return JSONResponse(
            status_code=400, content=jsonable_encoder({"detail": "FILE_ALREADY_EXISTS"})
        )
    except Exception as e:
        logger.info(f"Error uploading files: {e}")
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
