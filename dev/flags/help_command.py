import discord

from discord.ext import commands
from typing import Optional, Union, TYPE_CHECKING

from dev.utils.functs import send
from dev.utils.baseclass import root

if TYPE_CHECKING:
    from dev.utils.baseclass import Command, Group


class RootHelp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="--help", aliases=["--man"], parent="dev", version=1)
    async def root_help(self, ctx: commands.Context, *, command: str = None):
        """
        Help command made exclusively for the `?dev` cog.
        Flags are hidden, but they can still be accessed and attributes can still be viewed using their respective commands.
        """
        dev_cmd: Optional[commands.Group] = self.bot.get_command("dev")
        if not command:
            command_list = [cmd.name for cmd in dev_cmd.commands if not cmd.name.startswith("--")]; command_list.sort()
            subcommands = '\n'.join(command_list)
            hce = discord.Embed(title=dev_cmd.name, description=f"Root command for the `dev` cog. Subcommands are shown below.\nExecute `{ctx.prefix}dev --help [command]` for more information on a subcommand.",  color=discord.Color.darker_gray())
            hce.add_field(name="usage", value="dev [--version|-V] [--help|--man] [--source|-src] [--file] <command> [<args>]", inline=False)
            hce.add_field(name="docs", value=f"`--version`|`-V` [command] = Show the version of a command.\n`--help`|`--man` [command] = Shows this help menu.\n`--source`|`-src` [command] = Show the source code of a command.\n`--file` [path] = Show a file with its specified `path`.", inline=False)
            hce.add_field(name="subcommands", value=subcommands)
            return await send(ctx, embed=hce)

        cmd: Union[Command, Group] = self.bot.get_command(f"dev {command}")
        if cmd:
            docs = '\n'.join(cmd.help.split("\n")[1:]) if cmd.help else 'No docs available.'
            sche = discord.Embed(title=cmd.qualified_name, description=cmd.short_doc if cmd.short_doc else '', color=discord.Color.darker_gray())
            sche.add_field(name="usage", value=f"dev {cmd.name}{'|' + '|'.join(alias for alias in cmd.aliases) if cmd.aliases else ' '} {cmd.usage or cmd.signature}", inline=False)
            sche.add_field(name="docs", value=docs, inline=False)
            sche.set_footer(text=f"Supports virtual variables: {cmd.supports_virtual_vars}")
            if isinstance(cmd, commands.Group):
                command_list = [cmd.name for cmd in cmd.commands]; command_list.sort()
                subcommands = '\n'.join(command_list)
                sche.add_field(name="subcommands", value=subcommands or 'None')
            return await ctx.send(embed=sche)
        await send(ctx, f"Command `dev {command}` not found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(RootHelp(bot))