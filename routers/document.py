from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated

import aiofiles
import docx2txt  # alternativa: docx
import numpy
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pdfminer.high_level import extract_text as extract_pdf_text  # alternativa: PyPDF2
from sklearn.metrics.pairwise import cosine_similarity

from config import config
from database import database, document_table
from models.document import Document, DocumentWithSimilarity, Query, SearchResult
from models.user import UserOut
from security import get_current_user
from utils import extract_text_from_doc, find_answer_in_document, get_embedding

router = APIRouter()
UserDep = Annotated[UserOut, Depends(get_current_user)]


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile, current_user: UserDep):
    """
    Guarda el documento y crea los embeddings en la base de datos
    """
    CHUNK_SIZE = 1024 * 1024
    file_path = Path(config.DOCUMENT_PATH) / file.filename  # type: ignore
    async with aiofiles.open(file_path, "wb") as new_file:
        while chunk := await file.read(CHUNK_SIZE):
            await new_file.write(chunk)

    if file.content_type == "application/pdf":
        content = extract_pdf_text(file_path)

    elif (
        file.content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        content = docx2txt.process(str(file_path))

    elif file.content_type == "application/msword":
        content = extract_text_from_doc(file_path)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Format File: {file.content_type} Must be .pdf or .docx, or .doc",
        )

    content = (
        content.replace("\x00", "").encode("utf-8", errors="ignore").decode("utf-8")
    )

    data = {
        "name": file.filename,
        "content": content,
        "url": f"{config.DOMAIN}/{config.DOCUMENT_PATH}/{file.filename}",
        "embeddings": await get_embedding(content[:2000]),
    }
    query = document_table.insert().values(data)
    id = await database.execute(query)
    return {"detail": "file upload successfully", "id": id}


@router.post("/search", response_model=list[DocumentWithSimilarity])
async def get_relevant_documents(user_query: Query, limit: int = 3):
    user_query_embedding = await get_embedding(user_query.body)
    user_query_embedding = numpy.array(user_query_embedding).reshape(1, -1)

    query = document_table.select()
    documents = await database.fetch_all(query)

    def calculate_similarity(doc) -> DocumentWithSimilarity | None:
        if doc.embeddings:  # type: ignore
            doc_embedding = numpy.array(doc.embeddings).reshape(1, -1)  # type: ignore
            similarity = cosine_similarity(user_query_embedding, doc_embedding)[0][0]
            return DocumentWithSimilarity(
                id=doc.id,  # type: ignore
                name=doc.name,  # type: ignore
                url=doc.url,  # type: ignore
                similarity=float(similarity),
            )

        return None

    with ThreadPoolExecutor() as executor:
        documents_with_similarity = list(executor.map(calculate_similarity, documents))

    documents_with_similarity = [doc for doc in documents_with_similarity if doc]
    documents_with_similarity.sort(key=lambda doc: doc.similarity, reverse=True)
    return documents_with_similarity[:limit]


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: int):
    query = document_table.select().where(document_table.c.id == document_id)
    document = await database.fetch_one(query)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/{document_id}/search", response_model=SearchResult)
async def get_document_response(document_id: int, user_query: Query):
    query = document_table.select().where(document_table.c.id == document_id)
    document = await database.fetch_one(query)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    ans = {"document_id": document.id, "document_name": document.name}  # type: ignore
    ans.update(find_answer_in_document(document.content, user_query.body))  # type: ignore
    return ans


@router.get("/{document_id}/download")
async def download_document(document_id: int):
    query = document_table.select().where(document_table.c.id == document_id)
    document = await database.fetch_one(query)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    path = document.url.replace(config.DOMAIN, "")  # type: ignore
    if path.startswith("/"):
        path = path[1:]

    print(path)
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        file_path,
        filename=document.name,  # type: ignore
        headers={"Content-Disposition": f"attachment; filename={document.name}"},  # type: ignore
    )
