async def fetch_clan(conn, clan_name):

    clan_row = await conn.fetchrow('SELECT * FROM greeter WHERE clan_name = $1', clan_name)

    return clan_row
    # if clan_row is not None:
    #     return clan_row
    # else:
    #     return await add_clan(conn, clan_name)


async def add_clan(conn, clan_name):

    async with conn.transaction():
        await conn.execute('INSERT INTO greeter VALUES($1)', clan_name)
        clan_row = await conn.fetchrow('SELECT * FROM greeter WHERE clan_name = $1', clan_name)

    return clan_row


async def edit_field(conn, fieldname, clan_name, val):

    async with conn.transaction():
        await conn.execute(f'UPDATE greeter SET {fieldname}=$1 WHERE clan_name=$2', val, clan_name)
