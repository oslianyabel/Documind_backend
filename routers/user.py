from config import logger
from database import database, user_table
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from models.user import UserIn
from notifications import send_confirmation_email
from security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)

router = APIRouter()


@router.post("/register")
async def register(user: UserIn, request: Request, background_tasks: BackgroundTasks):
    logger.info("register")

    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exist",
        )

    data = user.model_dump()

    data["password"] = get_password_hash(user.password)

    query = user_table.insert().values(data)

    await database.execute(query)

    token = create_confirmation_token(user.email)
    url = request.url_for("confirm_email", token=token)
    # background_tasks.add_task(send_confirmation_email, user.email, url)

    return {"detail": "User created. Please confirm your email", "confirmation_url": url}


@router.post("/token")
async def login(user: UserIn):
    await authenticate_user(user.email, user.password)
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/register/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )
    await database.execute(query)
    return {"detail": "User confirmed"}
