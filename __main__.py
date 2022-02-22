from discord.ext import commands

from dev.utils.setup import setup_
from dev.utils.functs import is_owner
from dev.utils.baseclass import commands_
from dev.utils.settings import set_settings


class Dev(commands.Cog, command_attrs=dict(slash_command=False)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.group(name="dev", invoke_without_command=True, version=1)
    @is_owner()
    async def root(self, ctx: commands.Context):
        pass

    @commands_.command(name="exit", aliases=["kys"], version=1, parent="dev")
    @is_owner()
    async def root_stop(ctx: commands.Context):
        """
        Exit the whole program at once.
        Not recommended using unless a critical event happens that requires the bot to be terminated immediately
        """
        await ctx.message.add_reaction("👋")
        exit()

    @commands_.command(name="close", version=1, parent="dev")
    @is_owner()
    async def root_quit(ctx: commands.Context):
        """
        Close the bot.
        Safely exit out of the bot.
        """
        await ctx.message.add_reaction("👋")
        await ctx.bot.close


def setup(bot: commands.Bot):
    set_settings(bot)
    bot.add_cog(Dev(bot))
    setup_(bot, "dev.flags.help_command", "dev.flags.flags", "dev.bot_config.over", "dev.experimental.invoke", "dev.experimental.python", "dev.experimental.http")