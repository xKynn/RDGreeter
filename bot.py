import json

from asyncio import TimeoutError
from asyncpg import create_pool
from discord.ext import commands
from pathlib import Path
from context import GreeterContext


class Greeter(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # Configs & token
        with open('data/config.json') as f:
            self.config = json.load(f)

        self.startup_ext = [x.stem for x in Path('cogs').glob('*.py')]

        super().__init__(command_prefix=commands.when_mentioned_or('g/'), description=self.description,
                         pm_help=None, *args, **kwargs)

        # Make room for the help command
        self.remove_command('help')

        self.invites = {}

    def run(self):
        super().run(self.config['token'])

    # Utilise custom context for error messaging etc.
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=GreeterContext)
        await self.invoke(ctx)

    async def on_member_update(self, before, after):
        async with self.conn_pool.acquire() as conn:
            roles = await conn.fetch('SELECT clan_name from greeter')
        roles = [role['clan_name'] for role in roles]
        new_roles = set(after.roles).difference(set(before.roles))
        added_role = None
        for role in new_roles:
            if role.name in roles:
                added_role = role
                break
        if not added_role: return
        async with self.conn_pool.acquire() as conn:
            clan = await conn.fetchrow('SELECT * FROM greeter WHERE clan_name=$1', added_role.name)
        try:
            await after.send(clan['message'].replace('{USER}', after.name))
        except:
            return

    async def on_ready(self):

        self.conn_pool = await create_pool(database='greeter', user='postgres', password=self.config['db_pass'])

        for ext in self.startup_ext:
            try:
                self.load_extension(f'cogs.{ext}')
            except Exception as e:
                print(f'Failed to load extension: {ext}\n{e}')
            else:
                print(f'Loaded extension: {ext}')

        print(f'Client logged in.\n'
              f'{self.user.name}\n'
              f'{self.user.id}\n'
              '--------------------------')
