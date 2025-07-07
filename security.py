import asyncio
from datetime import timezone, datetime, timedelta
from typing import Annotated, Literal

from databases.interfaces import Record
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from config import config, logger
from database import database, user_table

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(email: str):
    logger.info("Create access token")
    expire_date = datetime.now(timezone.utc) + timedelta(minutes=60 * 24)
    data = {"sub": email, "exp": expire_date, "type": "access"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


def create_confirmation_token(email: str):
    logger.info("Create confirmation token")
    expire_date = datetime.now(timezone.utc) + timedelta(minutes=60 * 24 * 7)
    data = {"sub": email, "exp": expire_date, "type": "confirmation"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


async def get_user(email: str) -> Record | None:
    logger.debug("get user", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    user = await database.fetch_one(query)
    return user if user else None


async def authenticate_user(email: str, password: str):
    user = await get_user(email)

    if not user:
        raise create_credentials_exception("Invalid email or password")

    if not verify_password(password, user.password):  # type: ignore
        raise create_credentials_exception("Invalid email or password")

    if not user.confirmed:  # type: ignore
        raise create_credentials_exception("User has not confirmed email")

    return user


def get_subject_for_token_type(
    token: str, type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore

    except ExpiredSignatureError as exc:
        raise create_credentials_exception("Token has expired") from exc

    except JWTError as exc:
        raise create_credentials_exception("Invalid token") from exc

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email


async def get_current_user(token: Annotated[str, Depends(oauth2_schema)]):
    email = get_subject_for_token_type(token, "access")

    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Could not find user for this token")

    return user


async def test():
    await database.connect()
    user = await get_user("oslianyabel@gmail.com")
    print(user["email"])  # type: ignore
    print(user.email)  # type: ignore


if __name__ == "__main__":
    asyncio.run(test())
