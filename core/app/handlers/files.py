import logging
from multiprocessing.pool import AsyncResult
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Depends, Query, Path, status
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
        logger.info(f"Retrieving file with ID: {file_id}")
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

class ItemIDs(BaseModel):
    ids: List[str]

@fileRouter.put("/{file_id}/xml", response_model=FileResponse)
async def generate_xml(
    file_id: UUID = Path(..., description="UUID of the file to generate XML for"),
    item_ids: ItemIDs = Body(..., description="List of item str to include in the XML"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Generate XML content for a file based on a subset of its classified items
    """
    try:
        # Fetch the file and its items
        file = db.get_file_by_id(file_id)
        selected_ids = set(item_ids.ids)

        # Filter items to only those requested
        items_to_generate = [item for item in file.items if item.commission in selected_ids]
        if not items_to_generate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No matching items found for the provided IDs."
            )

        # Build XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<catalog>\n'
        for item in items_to_generate:
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

        # Persist the XML
        updated_file = db.update_xml_content(file_id, xml_content)

        return FileResponse(
            file=updated_file,
            message="XML content generated for selected items and updated successfully"
        )
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error generating XML for file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating XML: {str(e)}",
        )


# delete
@fileRouter.delete("/{file_id}")
async def delete_file(
    file_id: UUID = Path(..., description="UUID of the file to delete"),
    db: MongoDBService = Depends(get_db_service),
):
    """
    Delete a file by its ID
    """
    try:
        logger.info(f"Deleting file with ID: {file_id}")
        file = db.get_file_by_id(file_id)  # Check if file exists
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )
        if file.task_id:
            try:
            # Delete the associated task if it exists
                task = db.get_task_by_id(file.task_id)
                if task:
                    db.delete_task(task.id)
            except Exception as e:
                logger.error(f"Error deleting task {file.task_id}: {str(e)}")

        db.delete_file(file_id)
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {str(e)}"
        )