from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserOut(BaseModel):
    id: Optional[int] = None
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserIn(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)
