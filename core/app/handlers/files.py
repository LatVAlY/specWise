import logging
from multiprocessing.pool import AsyncResult
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel

from app.services.mongo_db import MongoDBService
from app.models.models import FileModel


logger = logging.getLogger(__name__)

fileRouter = APIRouter(
    prefix="/files",
    tags=["files"],
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


class ClassificationUpdateRequest(BaseModel):
    match: bool
    relevant: bool


# Dependency for MongoDB service
def get_db_service():
    return MongoDBService()


@fileRouter.get("/", response_model=FilesListResponse)
async def get_all_files(db: MongoDBService = Depends(get_db_service)):
    """
    Get all files in the system
    """
    try:
        files = db.get_files()
        return FilesListResponse(
            files=files, count=len(files), message="Files retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving files: {str(e)}",
        )


@fileRouter.get("/task/{task_id}", response_model=FilesListResponse)
async def get_files_by_task(
    task_id: UUID = Path(..., description="UUID of the task to filter files by"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Get all files associated with a specific task
    """
    try:
        # First check if the task exists
        task = db.get_task_by_id(task_id)
        files = db.get_files_by_task(task_id)

        return FilesListResponse(
            files=files,
            count=len(files),
            message=f"Found {len(files)} files for task {task_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving files for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error retrieving files: {str(e)}",
        )


# Routes for file operations
@fileRouter.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: UUID = Path(..., description="UUID of the file to retrieve"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Get a file by its ID
    """
    try:
        file = db.get_file_by_id(file_id)
        return FileResponse(file=file, message="File retrieved successfully")
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {str(e)}"
        )


@fileRouter.get("/customer/{customer_number}", response_model=FilesListResponse)
async def get_files_by_customer(
    customer_number: str = Path(..., description="Customer number to filter files by"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Get all files for a specific customer
    """
    try:
        files = db.get_files_by_customer(customer_number)
        return FilesListResponse(
            files=files,
            count=len(files),
            message=f"Found {len(files)} files for customer {customer_number}",
        )
    except Exception as e:
        logger.error(f"Error retrieving files for customer {customer_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving files: {str(e)}",
        )

@fileRouter.put("/{file_id}/xml", response_model=FileResponse)
async def generate_xml(
    file_id: UUID = Path(..., description="UUID of the file to generate XML for"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Generate XML content for a file based on its classified items
    """
    try:
        # Get the current file
        file = db.get_file_by_id(file_id)

        # Generate XML from the items
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<catalog>\n'

        for item in file.items:
            xml_content += "  <item>\n"
            xml_content += f"    <sku>{item.sku}</sku>\n"
            xml_content += f"    <name>{item.name}</name>\n"
            xml_content += f"    <text>{item.text}</text>\n"
            xml_content += f"    <quantity>{item.quantity}</quantity>\n"
            xml_content += f"    <quantityUnit>{item.quantityunit}</quantityUnit>\n"
            xml_content += f"    <price>{item.price}</price>\n"
            xml_content += f"    <priceUnit>{item.priceunit}</priceUnit>\n"
            xml_content += f"    <commission>{item.commission}</commission>\n"
            xml_content += "  </item>\n"

        xml_content += "</catalog>"

        # Update the file with the XML content
        updated_file = db.update_xml_content(file_id, xml_content)

        return FileResponse(
            file=updated_file, message="XML content generated and updated successfully"
        )
    except Exception as e:
        logger.error(f"Error generating XML for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating XML: {str(e)}",
        )
