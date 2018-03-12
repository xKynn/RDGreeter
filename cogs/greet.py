import discord
import texttable
from discord.ext import commands
from utils import db as greeterDB


class Greet:
    def __init__(self, bot):
        self.bot = bot

    def is_admin(ctx):
        """ Check if the caller has manage_guild """
        perm = ctx.author.guild_permissions.manage_guild
        if not perm:
            ctx.bot.loop.create_task(ctx.error())
            ctx.bot.loop.create_task(ctx.send("You need the `Manage Server` permission to use this command."))
        return perm

    @staticmethod
    async def _clan_check(ctx, clan, conn):
        """ Common function called by all funcs to check if a role exists """
        db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
        if db_clan is None:
            await ctx.error()
            await ctx.send(f"A role with name **{clan.lower().title()}** was not found in the DB.\n")
        return bool(db_clan)

    async def _edit_message(self, ctx, clan, conn):
        """ Common function called by edit_message and add_role """

        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        await ctx.send("Type out your greeting message, use {USER} in your message wherever you want to use the"
                       "invitee's name and {SERVER} for the server's name.\nCancel with `g/cancel`")
        greet = await self.bot.wait_for('message', check=check)
        if greet.content == 'g/cancel':
            return await greet.add_reaction('🗑')
        await greeterDB.edit_field(conn, 'message', clan.lower().title(), greet.content)
        await greet.add_reaction('✅')

    async def _edit_link(self, ctx, clan, conn):
        """ Common function called by edit_link and add_role """

        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        await ctx.send(f"Enter the invite link/code for role **{clan.lower().title()}**.\nCancel with `g/cancel`")
        link = await self.bot.wait_for('message', check=check)
        if link.content == 'g/cancel':
            return await link.add_reaction('🗑')
        await greeterDB.edit_field(conn, 'invite', clan.lower().title(), link.content.strip('<>').split('/')[-1])
        await link.add_reaction('✅')
        self.bot.invites = await self.bot.tally_invites()

    @commands.command(aliases=['add_clan', 'new'])
    @commands.check(is_admin)
    async def add_role(self, ctx, *, clan: str):
        """ Add a new role or invite source to the database. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.send(f"A role with name **{clan.lower().title()}** was not found in the DB.\nWould you like"
                               "to create an entry for it? You will have to provide an invite link and a greet messa"
                               "ge.\nReply with `g/yes` or `g/no`.")

                def name_check(message):
                    return message.author.id == ctx.author.id and message.channel == ctx.channel and \
                           message.content in ['g/no', 'g/yes']

                msg = await self.bot.wait_for('message', check=name_check)
                if msg.content == 'g/no':
                    return await msg.add_reaction('🗑')
                await greeterDB.add_clan(conn, clan.lower().title())

                await self._edit_link(ctx, clan, conn)
                await self._edit_message(ctx, clan, conn)

            else:
                return await ctx.send(f"A role with name **{clan.lower().title()}** already exists.\n"
                                      "Use `edit_link` or `edit_message` instead.")

    @commands.command(aliases=['edit_msg'])
    @commands.check(is_admin)
    async def edit_message(self, ctx, *, clan: str):
        """ Edit the message for an existing role/source. """
        async with self.bot.conn_pool.acquire() as conn:
            if not await self._clan_check(ctx, clan, conn):
                return
            await self._edit_message(ctx, clan, conn)

    @commands.command()
    @commands.check(is_admin)
    async def edit_link(self, ctx, *, clan: str):
        """ Edit the invite link/code for an existing role/source. """
        async with self.bot.conn_pool.acquire() as conn:
            if not await self._clan_check(ctx, clan, conn):
                return
            await self._edit_link(ctx, clan, conn)

    @commands.command(aliases=['delete_clan'])
    @commands.check(is_admin)
    async def delete_role(self, ctx, *, clan: str):
        """ Delete an existing role/source from the databse. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel and \
                           message.content in ['g/no', 'g/yes']
        async with self.bot.conn_pool.acquire() as conn:
            if not await self._clan_check(ctx, clan, conn):
                return

            await ctx.send(f"Are you sure you want to delete **{clan.lower().title()}** from the DB?.\n"
                           "Reply with `g/yes` or `g/no`.")
            conf = await self.bot.wait_for('message', check=check)
            if conf.content == 'g/no':
                return await conf.add_reaction('🗑')
            async with conn.transaction():
                await conn.execute('DELETE FROM greeter WHERE clan_name=$1', clan.lower().title())
            await conf.add_reaction('✅')

    @commands.command(aliases=['roles', 'clans'])
    @commands.check(is_admin)
    async def info(self, ctx):
        """ List the current sources/roles and their invite codes. """
        async with self.bot.conn_pool.acquire() as conn:
            clans = await conn.fetch('SELECT * from greeter')
        tbl = ['```', '```']
        tab = texttable.Texttable()
        tab.header(('Roles', 'Invites'))
        for clan in clans:
            tab.add_row((clan['clan_name'], clan['invite']))
        tbl.insert(1, tab.draw())
        await ctx.send('\n'.join(tbl))

    @commands.command(aliases=['test'])
    @commands.check(is_admin)
    async def preview(self, ctx, *, clan: str):
        """ Get DMed with the specified role/source's greet message. """
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
        if db_clan is None:
            await ctx.error()
            return await ctx.send(f"A role with name **{clan.lower().title()}** was not found in the DB.\n")
        try:
            await ctx.author.send(db_clan['message'].replace('{USER}', ctx.author.name).replace(
                '{SERVER}', self.bot.get_guild(138067606119645184).name))
        except discord.DiscordException:
            await ctx.error()
            await ctx.send("You have DMs from non-friends disabled!")


def setup(bot):
    bot.add_cog(Greet(bot))
