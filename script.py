from models.document import UserQuery
from routers.document import get_relevant_documents
import asyncio
from database import database


if __name__ == "__main__":
    async def main():
        await database.connect()
        user_query = UserQuery(content="Quien es Blancanieves?")
        documents = await get_relevant_documents(user_query)
        for doc in documents:
            print(doc.name)
            
        await database.disconnect()

    asyncio.run(main())
