import asyncio

from config import config
from database import database, user_table
from models.document import UserQuery
from routers.document import get_relevant_documents
from utils import get_embedding

if __name__ == "__main__":

    async def main():
        await database.connect()
        user_query = UserQuery(content="Quien es Blancanieves?")
        documents = await get_relevant_documents(user_query)
        for doc in documents:
            print(doc.name)  # type: ignore

        await database.disconnect()

    async def test_get_embedding():
        embedding = await get_embedding("HEllo WOrld")
        print(type(embedding))

    import asyncpg
    from pgvector.asyncpg import register_vector

    async def get_db():
        conn = await asyncpg.connect(config.DATABASE_URL)
        await register_vector(conn)
        return conn

    async def delete_user(email):
        await database.connect()
        query = user_table.delete().where(user_table.c.email == email)
        await database.execute(query)
        await database.disconnect()

    asyncio.run(delete_user("oslianyabel@gmail.com"))
