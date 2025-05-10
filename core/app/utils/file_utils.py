import logging
from pathlib import Path

from fastapi import UploadFile
from app.constants import PROCESSING_FILE_PATH

logger = logging.getLogger(__name__)


def create_processing_file_path():
    """
    Create a directory for processing files if it doesn't exist.
    """
    processing_file_path = Path(PROCESSING_FILE_PATH)
    if not processing_file_path.exists():
        processing_file_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {processing_file_path}")
    else:
        logger.info(f"Directory already exists: {processing_file_path}")


def save_file(file: UploadFile):
    """
    Save the uploaded file to the processing directory.
    """
    create_processing_file_path()
    file_path = Path(PROCESSING_FILE_PATH) / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    logger.info(f"Saved file to {file_path}")
    return file_path
