import asyncio
import aiosqlite
import os


async def get_tables():
    my_path = os.path.dirname(os.path.abspath(__file__))
    dbname = os.path.normpath(
        os.path.join(my_path, "../..", "LOLogger", "ULTRARACK_2019_08.db"))
    # col_names = ['ClientTimestamp', 'ClientName', 'EpochTime', 'LogMessage', 'Level', 'IP']
    print(dbname)
    async with aiosqlite.connect(f"file:{dbname}?mode=ro", uri=True) as db:
        async with db.execute(f"SELECT * FROM Events LIMIT 1;") as cursor:
            col_names = ([tup[0] for tup in cursor.description])
            print(col_names)
        async with db.execute(
                f"SELECT DISTINCT ClientName FROM Events;") as cursor:
            print([client[0] for client in await cursor.fetchall()])
        async with db.execute(f"SELECT DISTINCT Level FROM Events;") as cursor:
            print([client[0] for client in await cursor.fetchall()])
        async with db.execute(
                f"SELECT {','.join(col_names)} FROM Events LIMIT 10;"
        ) as cursor:
            print([row[1] async for row in cursor])
            # print(row[1])


if __name__ == "__main__":
    asyncio.run(get_tables())
