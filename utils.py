import asyncio
from enum import Enum
from pathlib import Path
from tqdm import tqdm
from typing import Optional

import aiofiles
import PyPDF2
from docx import Document as DocxDocument
from fastapi import HTTPException, status

from config import config, logger, openai_client


async def get_embedding(
    text: str, model: str = "text-embedding-3-small"
) -> list[float]:
    text = text.replace("\n", " ")
    response = await openai_client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def clean_text(text: str) -> str:
    """Remove null bytes and ensure UTF-8 encoding"""
    return text.replace("\x00", "").encode("utf-8", errors="ignore").decode("utf-8")


async def get_page_embedding(idx: int, content: str, pbar: Optional[tqdm] = None):
    logger.debug(
        f"Getting embeddings from page or paragraph {idx} with {len(content)} characters"
    )
    result = {
        "page_number": idx,
        "content": content,
        "embeddings": await get_embedding(content[:2000]),
    }
    if pbar:
        pbar.update(1)

    return result


async def download_file(file):
    CHUNK_SIZE = 1024 * 1024
    file_path = Path(config.DOCUMENT_PATH) / file.filename  # type: ignore
    file_size = file.size
    
    with tqdm(total=file_size, unit='B', unit_scale=True, desc="Downloading file") as pbar:
        async with aiofiles.open(file_path, "wb") as new_file:
            while chunk := await file.read(CHUNK_SIZE):
                await new_file.write(chunk)
                pbar.update(len(chunk))

    return file_path


class FileType(Enum):
    pdf = "application/pdf"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def get_document_content(content_type, file_path):
    if content_type == FileType.pdf.value:
        return await get_pdf_content(file_path)

    elif content_type == FileType.docx.value:
        return await get_docx_content(file_path)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Format File: {content_type} Must be .pdf or .docx",
        )


async def get_pdf_content(file_path):
    content = ""
    pages = []
    process_list = []

    with open(file_path, "rb") as new_file:
        reader = PyPDF2.PdfReader(new_file)
        num_pages = len(reader.pages)
        
        with tqdm(total=num_pages, desc="Processing PDF pages") as pbar:
            for idx, page in enumerate(reader.pages):
                content_page = clean_text(page.extract_text())
                if content_page:
                    process_list.append(get_page_embedding(idx, content_page, pbar))
                content += content_page + "\n"

            if process_list:
                pages = await asyncio.gather(*process_list)

    return content, pages


async def get_docx_content(file_path):
    content = ""
    pages = []
    process_list = []
    doc = DocxDocument(file_path)  # type: ignore
    paragraphs = doc.paragraphs
    num_paragraphs = len(paragraphs)
    
    with tqdm(total=num_paragraphs, desc="Processing DOCX paragraphs") as pbar:
        for idx, para in enumerate(paragraphs):
            content_page = clean_text(para.text)
            if content_page:
                process_list.append(get_page_embedding(idx, content_page, pbar))
            content += content_page + "\n"

        if process_list:
            pages = await asyncio.gather(*process_list)


    return content, pages


get_relevant_documents_query = """
    SELECT id, name, url, embeddings <=> :embedding AS similarity
    FROM documents
    WHERE embeddings IS NOT NULL
    ORDER BY similarity ASC
    LIMIT :limit
"""
