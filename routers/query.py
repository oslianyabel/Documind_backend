from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from database import database, query_table
from models.query import DocumentQuery
from models.user import UserOut
from security import get_current_user

router = APIRouter()
UserWithToken = Annotated[UserOut, Depends(get_current_user)]


@router.get("/", response_model=list[DocumentQuery])
async def get_querys(current_user: UserWithToken, limit: Optional[int] = None):
    query = query_table.select()
    querys = await database.fetch_all(query)

    if not querys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There are not querys"
        )

    if limit:
        return querys[:limit]

    return querys


@router.get("/{document_id}", response_model=list[DocumentQuery])
async def get_query_by_document(document_id: int, current_user: UserWithToken, limit: Optional[int] = None):
    query = query_table.select().where(query_table.c.document_id == document_id)
    querys = await database.fetch_all(query)

    if not querys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are not querys for this document",
        )

    if limit:
        return querys[:limit]

    return querys
