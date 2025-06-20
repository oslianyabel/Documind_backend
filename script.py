import asyncio

import aiofiles


async def main():
    async with aiofiles.open("libros/test.txt", "r") as in_file:
        content = await in_file.read()

    print(content)


if __name__ == "__main__":
    asyncio.run(main())
