import databases
import sqlalchemy
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from config import config

metadata = sqlalchemy.MetaData()

document_table = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("path", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("embeddings", Vector(384)),
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
    sqlalchemy.Column("answer", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("document_id", sqlalchemy.ForeignKey("documents.id"), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, nullable=False, server_default=func.now()),
)

connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
engine = sqlalchemy.create_engine(str(config.DATABASE_URL), connect_args=connect_args)

metadata.create_all(engine)
db_args = {"min_size": 1, "max_size": 3} if "postgres" in config.DATABASE_URL else {}
database = databases.Database(str(config.DATABASE_URL), force_rollback=False, **db_args)
