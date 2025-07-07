from contextlib import asynccontextmanager

import aiofiles.os
import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import config
from database import database
from routers.document import router as document_router
from routers.query import router as query_router
from routers.user import router as user_router

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    send_default_pii=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


@asynccontextmanager
async def lifespam(app: FastAPI):
    await aiofiles.os.makedirs(config.DOCUMENT_PATH, exist_ok=True)  # type: ignore
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespam)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(document_router, prefix="/documents")
app.include_router(user_router, prefix="/users")
app.include_router(query_router, prefix="/querys")
app.mount("/media", StaticFiles(directory="media"), name="media")
