import asyncio
import asyncpg
import json


async def main():
    with open('data/config.json') as f:
        config = json.load(f)

    conn = await asyncpg.connect('postgresql://postgres@localhost/greeter', password=config['db_pass'],
                                 port=config['db_port'])
    await conn.execute('''CREATE TABLE greeter(
    clan_name text PRIMARY KEY,
    invite text,
    message text
    );
    ''')
    await conn.close()

asyncio.get_event_loop().run_until_complete(main())

