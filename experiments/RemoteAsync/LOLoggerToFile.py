import asyncio
import aiosqlite
import json
import os


async def get_tables():
    my_path = os.path.dirname(os.path.abspath(__file__))
    dbname = os.path.normpath(
        os.path.join(my_path, "../..", "LOLogger", "ULTRARACK_2019_08.db"))
    col_names = [
        'ClientTimestamp', 'EpochTime', 'ClientName', 'Level', 'IP',
        'LogMessage'
    ]
    print(dbname)
    with open(dbname.replace(".db", ".json"), "w") as fp:
        async with aiosqlite.connect(f"file:{dbname}?mode=ro", uri=True) as db:
            async with db.execute(
                    f"SELECT {','.join(col_names)} FROM Events;") as cursor:
                async for row in cursor:
                    # print(json.dumps({col_name: int(float(value)) if col_name=='EpochTime' else value for col_name, value in zip(col_names, row)}), file=fp)
                    print(json.dumps({
                        col_name: value
                        for col_name, value in zip(col_names, row)
                    }),
                          file=fp)


if __name__ == "__main__":
    asyncio.run(get_tables())
