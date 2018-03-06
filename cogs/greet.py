from discord.ext import commands
from utils import db as greeterDB


class Greet:
    def __init__(self, bot):
        self.bot = bot

    def is_admin(ctx):
        return ctx.author.permissions.manage_guild

    @commands.command()
    @commands.check(is_admin)
    async def add_clan(self, ctx, *, clan: str):
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
                elif msg == 'g/yes':
                    pass
                db_clan = await greeterDB.add_clan(conn, clan.lower().title())

                await ctx.send(f"Enter the invite link/code for clan **{clan.lower().title()}**.\nCancel with"
                               " `g/cancel`")
                link = await self.bot.wait('message', check=check)
                if link == 'g/cancel':
                    return
                await greeterDB.edit_field(conn, 'invite', clan.lower().title(), link.strip('<>').split('/')[-1])

                await ctx.send("Type out your greeting message, use {USER} in your message wherever you want to use the"
                               "invitee's name.\nCancel with `g/cancel`")
                greet = await self.bot.wait('message', check=check)
                if greet == 'g/cancel':
                    return
                await greeterDB.edit_field(conn, 'message', clan.lower().title(), greet)
            else:
                return await ctx.send(f"A clan with name **{clan.lower().title()}** already exists.\n"
                                      "Use `edit_invite` or `edit_message` instead.")

    @commands.command()
    @commands.check(is_admin)
    async def edit_message(self, ctx, *, clan: str):
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.error()
                return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")

            await ctx.send("Type out your greeting message, use {USER} in your message wherever you want to use the"
                           "invitee's name.\nCancel with `g/cancel`")
            greet = await self.bot.wait('message', check=check)
            if greet == 'g/cancel':
                return
            await greeterDB.edit_field(conn, 'message', clan.lower().title(), greet)

    @commands.command()
    @commands.check(is_admin)
    async def edit_link(self, ctx, *, clan: str):
        def check(message):
            return message.author.id == ctx.author.id and message.channel == ctx.channel
        async with self.bot.conn_pool.acquire() as conn:
            db_clan = await greeterDB.fetch_clan(conn, clan.lower().title())
            if db_clan is None:
                await ctx.error()
                return await ctx.send(f"A clan with name **{clan.lower().title()}** was not found in the DB.\n")

            await ctx.send(f"Enter the invite link/code for clan **{clan.lower().title()}**.\nCancel with `g/cancel`")
            link = await self.bot.wait('message', check=check)
            if link == 'g/cancel':
                return
            await greeterDB.edit_field(conn, 'invite', clan.lower().title(), link.strip('<>').split('/')[-1])
            await self.bot.tally_invites()


def setup(bot):
    bot.add_cog(Greet(bot))
