import os
import tempfile

import aiofiles

from config import logger
from fastapi import APIRouter, HTTPException, UploadFile, status
from libs.b2 import b2_upload_file

router = APIRouter()
CHUNK_SIZE = 1024 * 1024
CUSTOM_TEMP_DIR = "./temp_uploads"
os.makedirs(CUSTOM_TEMP_DIR, exist_ok=True)


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile):
    try:
        file_path = None
        with tempfile.NamedTemporaryFile(
            dir=CUSTOM_TEMP_DIR,
            delete=False,  # Windows
        ) as temp_file:
            logger.info(f"Saving uploaded file temporarily to {file_path}")

            file_path = temp_file.name

            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = b2_upload_file(local_file=file_path, file_name=file.filename)  # type: ignore

            return {
                "detail": f"Successfully uploaded {file.filename}",
                "file_url": file_url,
            }

    except Exception as exc:
        logger.error(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )

    finally:  # Windows 
        if file_path and os.path.exists(file_path):  # type: ignore
            os.unlink(file_path)
