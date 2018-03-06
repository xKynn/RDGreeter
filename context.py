import discord
from discord.ext import commands


class GreeterContext(commands.Context):
    async def error(self):
        """ Add a reaction signifying an error """
        await self.message.add_reaction('🛑')
        
    async def reply(self, content: str, *, embed: discord.Embed = None):
        """ replies with mention """
        await self.send(f'{content}\n{self.author.mention}', embed=embed)
