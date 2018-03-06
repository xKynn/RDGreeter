import discord
import texttable
from discord.ext import commands
from utils import db as greeterDB


class Greet:
    def __init__(self, bot):
        self.bot = bot

    def is_admin(ctx):
        return ctx.author.guild_permissions.manage_guild

    @commands.command()
    @commands.check(is_admin)
    async def add_clan(self, ctx, *, clan: str):
        """ Add a new clan or invite source to the database. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\nWould you like"
                               "to create an entry for it? You will have to provide an invite link and a greet messa"
                               "ge.\nReply with `g/yes` or `g/no`.")

                def name_check(message):
                    return message.author.id == ctx.author.id and message.channel == ctx.channel and \
                           message.content in ['g/no', 'g/yes']

                msg = await self.bot.wait_for('message', check=name_check)
                if msg == 'g/no':
                    return
                await greeterDB.add_clan(conn, clan.lower().title())

                await ctx.send(f"Enter the invite link/code for clan **{clan.lower().title()}**.\nCancel with"
                               " `g/cancel`")
                link = await self.bot.wait_for('message', check=check)
                if link == 'g/cancel':
                    return
                await greeterDB.edit_field(conn, 'invite', clan.lower().title(), link.content.strip('<>').split('/')[-1])
                await link.add_reaction('✅')

                await ctx.send("Type out your greeting message, use {USER} in your message wherever you want to use the"
                               "invitee's name.\nCancel with `g/cancel`")
                greet = await self.bot.wait_for('message', check=check)
                if greet == 'g/cancel':
                    return
                await greeterDB.edit_field(conn, 'message', clan.lower().title(), greet.content)
                await greet.add_reaction('✅')
            else:
                return await ctx.send(f"A clan with name **{clan.lower().title()}** already exists.\n"
                                      "Use `edit_invite` or `edit_message` instead.")

    @commands.command()
    @commands.check(is_admin)
    async def edit_message(self, ctx, *, clan: str):
        """ Edit the message for an existing clan/source. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.error()
                return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")

            await ctx.send("Type out your greeting message, use {USER} in your message wherever you want to use the"
                           "invitee's name.\nCancel with `g/cancel`")
            greet = await self.bot.wait_for('message', check=check)
            if greet == 'g/cancel':
                return
            await greeterDB.edit_field(conn, 'message', clan.lower().title(), greet.content)
            await greet.add_reaction('✅')

    @commands.command()
    @commands.check(is_admin)
    async def edit_link(self, ctx, *, clan: str):
        """ Edit the invite link/code for an existing clan/source. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.error()
                return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")

            await ctx.send(f"Enter the invite link/code for clan **{clan.lower().title()}**.\nCancel with `g/cancel`")
            link = await self.bot.wait_for('message', check=check)
            if link == 'g/cancel':
                return
            await greeterDB.edit_field(conn, 'invite', clan.lower().title(), link.content.strip('<>').split('/')[-1])
            await link.add_reaction('✅')
            self.bot.invites = await self.bot.tally_invites()

    @commands.command()
    @commands.check(is_admin)
    async def delete_clan(self, ctx, *, clan: str):
        """ Delete an existing clan/source from the databse. """
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel and \
                           message.content in ['g/no', 'g/yes']
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.error()
                return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")

            await ctx.send(f"Are you sure you want to delete **{clan.lower().title()}** from the DB?.\n"
                           "Reply with `g/yes` or `g/no`.")
            conf = await self.bot.wait_for('message', check=check)
            if conf == 'g/no':
                return
            async with conn.transaction():
                await conn.execute('DELETE FROM greeter WHERE clan_name=$1', clan.lower().title())
            await conf.add_reaction('✅')

    @commands.command()
    @commands.check(is_admin)
    async def info(self, ctx):
        """ List the current sources/clans and their invite codes. """
        async with self.bot.conn_pool.acquire() as conn:
            clans = await conn.fetch('SELECT * from greeter')
        tbl = ['```', '```']
        tab = texttable.Texttable()
        tab.header(('Clans', 'Invites'))
        for clan in clans:
            tab.add_row((clan['clan_name'], clan['invite']))
        tbl.insert(1, tab.draw())
        await ctx.send('\n'.join(tbl))

    @commands.command()
    @commands.check(is_admin)
    async def preview(self, ctx, *, clan: str):
        """ Get DMed with the specified clan/source's greet message. """
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
        if db_clan is None:
            await ctx.error()
            return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")
        try:
            await ctx.author.send(db_clan['message'].replace('{USER}', ctx.author.name))
        except discord.DiscordException:
            await ctx.error()
            await ctx.send("You have DMs from non-friends disabled!")


def setup(bot):
    bot.add_cog(Greet(bot))
