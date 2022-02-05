import discord

from discord.ext import commands

from dev.utils.settings import set_settings
from dev.utils.setup import setup_
from dev.utils.functs import is_owner


class Dev(commands.Cog, command_attrs=dict(slash_command=False)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="dev", invoke_without_command=True)
    @is_owner()
    async def root(self, ctx: commands.Context):
        e = discord.Embed(title="Dev Tool",
                          description="A tool made for in-app bot re-configuration.\nMore coming soon.",
                          color=discord.Color.blurple())
        e.add_field(name="Version", value="1.0")
        await ctx.send(embed=e)

    @root.command(name="stop", aliases=["kys"])
    @is_owner()
    async def root_stop(self, ctx: commands.Context):
        await ctx.message.add_reaction("👋")
        exit()

    @root.command(name="quit")
    @is_owner()
    async def root_quit(self, ctx: commands.Context):
        await ctx.message.add_reaction("👋")
        await self.bot.close


def setup(bot: commands.Bot):
    set_settings(bot)
    bot.add_cog(Dev(bot))
    setup_(bot, extentions=["dev.functions.override", "dev.functions.python", "dev.functions.bot", "dev.functions.execute"], commands=["override", "bot", "python", "execute"])