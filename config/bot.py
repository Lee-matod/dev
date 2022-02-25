import discord

from discord.ext import commands

from dev.utils.baseclass import commands_


class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="reload", parent="dev", version=1)
    async def root_reload(ctx: commands.Context, extension: str = commands.Option(description="Extension to reload.", default="~")):
        """
        Reload a specific extension/cog or reload everything.
        When specifying an extension, errors are returned via a reaction - ❗
        When an extension is not specified, errors are returned to the same embed where other (if any) reloaded extension are showcased.
        """
        if extension == "~":
            reloaded_exts = []
            err_exts = []
            for ext in list(ctx.bot.extensions).copy():
                if ext not in ["dev.flags.help_command", "dev.flags.flags", "dev.config.over", "dev.config.bot", "dev.experimental.invoke", "dev.experimental.python", "dev.experimental.http"]:
                    try:
                        ctx.bot.unload_extension(ext)
                        ctx.bot.load_extension(ext)
                        reloaded_exts.append(ext)
                    except Exception as e:
                        err_exts.append(f"{ext} - {e}")
            description = ['\n'.join(f'☑ {ext}' for ext in reloaded_exts), '\n'.join(f'⛔ {ext}' for ext in err_exts) if err_exts else '']
            return await ctx.send(embed=discord.Embed(title="Cogs reloaded", description='\n'.join(description), colour=discord.Color.blurple()))
        try:
            ctx.bot.reload_extension(extension)
            await ctx.message.add_reaction("☑")
        except commands.ExtensionNotLoaded:
            await ctx.message.add_reaction("❗")




def setup(bot):
    bot.add_cog(RootBot(bot))