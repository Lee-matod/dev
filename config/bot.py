from discord.ext import commands

class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    """
    THIS IS STILL UNDER DEVELOPMENT.
    """



def setup(bot):
    bot.add_cog(RootBot(bot))