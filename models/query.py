from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class DocumentQuery(BaseModel):
    query: str
    answer: str
    document_id: int
    page_number: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_dt(self, dt: datetime) -> str:
        return dt.isoformat()
