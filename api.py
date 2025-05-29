from contextlib import asynccontextmanager
from typing import List
from uuid import uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles

from config import logger
from models import Document, DocumentCreate, DocumentUpdate

documents_db: List[Document] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    documents_db.clear()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", response_model=List[Document])
async def list_documents(request: Request):
    logger.info("GET Docs")
    return documents_db


@app.get("/docs/{doc_id}", response_model=Document)
async def get_document(doc_id: str, request: Request):
    logger.info(f"GET Doc {doc_id}")

    for doc in documents_db:
        if doc.id == doc_id:
            return doc

    logger.error(f"Documento con ID {doc_id} no encontrado")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
    )


@app.post("/docs", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(document: DocumentCreate, request: Request):
    logger.info("POST Doc")

    new_doc = Document(
        id=str(uuid4()),
        title=document.title,
        content=document.content,
        owner=document.owner,
    )

    documents_db.append(new_doc)
    return new_doc


@app.put("/docs/{doc_id}", response_model=Document)
async def update_document(doc_id: str, document: DocumentUpdate, request: Request):
    logger.info(f"PUT Doc {doc_id}")

    for idx, doc in enumerate(documents_db):
        if doc.id == doc_id:
            update_data = document.dict(exclude_unset=True)
            updated_doc = doc.copy(update=update_data)
            documents_db[idx] = updated_doc
            return updated_doc

    logger.error(f"Documento con ID {doc_id} no encontrado para actualización")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
    )


@app.delete("/docs/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, request: Request):
    logger.info(f"DELETE Doc {doc_id}")

    for idx, doc in enumerate(documents_db):
        if doc.id == doc_id:
            documents_db.pop(idx)
            return

    logger.error(f"Documento con ID {doc_id} no encontrado para eliminación")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
    )
