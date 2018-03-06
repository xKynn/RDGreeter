import json

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

    async def tally_invites(self):
        guild_invites = await self.get_guild(383240599328784395).invites()
        clan_invites = {}
        async with self.conn_pool.acquire() as conn:
            clans = await conn.fetch('SELECT * from greeter')
        for clan in clans:
            for invite in guild_invites:
                if invite.code == clan['invite']:
                    clan_invites[invite.code] = invite.uses
                    break
        return clan_invites

    # Utilise custom context for error messaging etc.
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=GreeterContext)
        await self.invoke(ctx)

    async def on_member_join(self, member):
        current_invites = await self.tally_invites()
        clan_link = None
        for invite in self.invites:
            if current_invites[invite] > self.invites[invite]:
                clan_link = invite
                break
        if clan_link is None:
            return
        async with self.conn_pool.acquire() as conn:
            clan = await conn.fetchrow('SELECT * FROM greeter WHERE invite=$1', clan_link)
        await member.send(clan['message'].replace('{USER}', member.name))

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
        self.invites = await self.tally_invites()
