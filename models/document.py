from typing import Optional

from pydantic import BaseModel, ConfigDict


class Query(BaseModel):
    body: str

    model_config = ConfigDict(from_attributes=True)


class Document(BaseModel):
    id: int
    name: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class DocumentWithSimilarity(Document):
    similarity: float


class SearchResult(BaseModel):
    document_id: int
    document_name: str
    answer: Optional[str] = None
    context: Optional[str] = None
    paragraph: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
