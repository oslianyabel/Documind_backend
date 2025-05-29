from typing import Optional

from pydantic import BaseModel


class Document(BaseModel):
    id: str
    title: str
    content: str
    owner: str


class DocumentCreate(BaseModel):
    title: str
    content: str
    owner: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    owner: Optional[str] = None
