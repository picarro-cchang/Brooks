import asyncio
import aiosqlite
import json
import os


async def get_tables():
    my_path = os.path.dirname(os.path.abspath(__file__))
    dbname = os.path.normpath(os.path.join(my_path, "..", "LOLogger", "_2019_08.db"))
    col_names = [
        'rowid',
        'ClientTimestamp',
        'EpochTime',
        'ClientName',
        'Level',
        'IP',
        'LogMessage',
    ]
    print(dbname)
    last_row = 0
    with open(dbname.replace(".db", ".json"), "w") as fp:
        while True:
            async with aiosqlite.connect(f"file:{dbname}?mode=ro", uri=True) as db:
                async with db.execute(
                        f"SELECT {','.join(col_names)} FROM Events WHERE rowid>{last_row} ORDER BY rowid ASC;") as cursor:
                    async for row in cursor:
                        print(json.dumps({
                            col_name: int(1000 * float(value)) if col_name == 'EpochTime' else value
                            for col_name, value in zip(col_names, row)
                        }),
                              file=fp)
                        last_row = int(row[0])
            print('.', end='', flush=True)
            fp.flush()
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(get_tables())
