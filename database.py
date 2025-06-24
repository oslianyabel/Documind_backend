import asyncio

import databases
import sqlalchemy
from sqlalchemy.sql import func
# from sqlalchemy.dialects.postgresql import JSONB

from config import config

metadata = sqlalchemy.MetaData()

document_table = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("url", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("embeddings", sqlalchemy.ARRAY(sqlalchemy.Float)),
)

page_table = sqlalchemy.Table(
    "pages",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("page_number", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("document_id", sqlalchemy.ForeignKey("documents.id", ondelete="CASCADE"), nullable = False),
    sqlalchemy.Column("content", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("embeddings", sqlalchemy.ARRAY(sqlalchemy.Float)),  # sqlalchemy.dialects.postgresql.VECTOR(1536)
)

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False),
)

query_table = sqlalchemy.Table(
    "querys",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("query", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("answer", sqlalchemy.String),
    sqlalchemy.Column("page_number", sqlalchemy.Integer),
    sqlalchemy.Column(
        "document_id", sqlalchemy.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    ),
    sqlalchemy.Column(
        "created_at", sqlalchemy.TIMESTAMP, nullable=False, server_default=func.now()
    ),
)

connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {} # type: ignore
engine = sqlalchemy.create_engine(str(config.DATABASE_URL), connect_args=connect_args)

metadata.create_all(engine)
db_args = {"min_size": 1, "max_size": 3} if "postgres" in config.DATABASE_URL else {} # type: ignore
database = databases.Database(str(config.DATABASE_URL), force_rollback=False, **db_args)


if __name__ == "__main__":

    async def update_urls():
        await database.connect()

        base_url = f"{config.DOMAIN}/{config.DOCUMENT_PATH}/"

        query = document_table.select()
        documents = await database.fetch_all(query)

        for doc in documents:
            update_query = (
                document_table.update()
                .where(document_table.c.id == doc.id)  # type: ignore
                .values({"url": base_url + doc.name})  # type: ignore
            )
            await database.execute(update_query)
            print(f"{doc.url} -> {base_url + doc.name}")  # type: ignore

        await database.disconnect()

    async def main():
        await database.connect()
        query = document_table.select()
        document = await database.fetch_all(query)
        print(len(document))
        await database.disconnect()

    asyncio.run(main())
