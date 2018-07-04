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

    async def on_member_join(self, member):
        def role_update_check(before, after):
            if before.id != member.id:
                return False
            new_roles = set(after.roles).difference(set(before.roles))
            for role in new_roles:
                if role.name.startswith('Royal Destiny') or role.name.startswith('Guest'):
                    print(role.name)
                    return True
            return False
        try:
            _, update = await self.wait_for('member_update', check=role_update_check, timeout=5)
        except TimeoutError:
            return
        clan_name = None
        for role in update.roles:
            if role.name.startswith('Royal Destiny') or role.name.startswith('Guest'):
                clan_name = role.name
                break
        if not clan_name:
            return
        async with self.conn_pool.acquire() as conn:
            clan = await conn.fetchrow('SELECT * FROM greeter WHERE clan_name=$1', clan_name)
        try:
            await member.send(clan['message'].replace('{USER}', member.name))
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
