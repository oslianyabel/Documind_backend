from pydantic import BaseModel, ConfigDict


class UploadDocument(BaseModel):
    detail: str
    document_id: int
    document_url: str


class UserQuery(BaseModel):
    content: str

    model_config = ConfigDict(from_attributes=True)


class Document(BaseModel):
    id: int
    name: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class DocumentWithSimilarity(Document):
    similarity: float


class PageWithSimilarity(BaseModel):
    document_id: int
    page_number: int
    similarity: float

    model_config = ConfigDict(from_attributes=True)


class SearchResult(BaseModel):
    query: str
    answer: str
    document_id: int
    page_number: int

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    detail: str
