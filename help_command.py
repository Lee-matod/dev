import discord

from discord.ext import commands

from dev.utils.baseclass import commands_


class RootHelp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="--help", aliases=["--man"], parent="dev")
    async def root_help(ctx: commands.Context, *, command: str = None):
        dev_cmd: commands.Group = ctx.bot.get_command("dev")
        if not command:
            command_list = [cmd.name for cmd in dev_cmd.commands if not cmd.name.startswith("--")]; command_list.sort()
            subcommands = '\n'.join(command_list)
            hce = discord.Embed(title=dev_cmd.name, description=f"Root command for the `dev` cog. Subcommands are shown below.\nExecute `{ctx.prefix}dev --help [command]` for more information on a subcommand.",  color=discord.Color.darker_gray())
            hce.add_field(name="usage", value="dev [--version|-V] [--help] [--source|-src] [--file] <command> [<args>]", inline=False)
            hce.add_field(name="docs", value=f"`--version`|`-V` [command] = Show the version of a command.\n`--help` [command] = Shows this help menu.\n`--source`|`-src` [command] = Show the source code of a command.\n`--file` [path] = Show a file with its specified `path`.", inline=False)
            hce.add_field(name="subcommands", value=subcommands)
            return await ctx.send(embed=hce)
        if command in [cmd.name for cmd in dev_cmd.commands]:
            cmd = ctx.bot.get_command(f"dev {command}")
            if not cmd or command.startswith("--"):
                return await ctx.send(f"Command `{command}` is not found.")
            options = {}
            docs = '\n'.join(cmd.help.split("\n")[1:])
            for option in cmd.option_descriptions:
                options[option] = cmd.option_descriptions[option]
            sche = discord.Embed(title=cmd.name, description=cmd.short_doc, color=discord.Color.darker_gray())
            sche.add_field(name="usage", value=f"dev {cmd.name}{'|' + '|'.join(alias for alias in cmd.aliases) if cmd.aliases else ' '} {cmd.usage or cmd.signature}", inline=False)
            sche.add_field(name="arguments", value='\n'.join(f"`{option}`: {cmd.option_descriptions[option]}" for option in options), inline=False)
            sche.add_field(name="docs", value=docs, inline=False)
            if isinstance(cmd, commands.Group):
                command_list = [cmd.name for cmd in cmd.commands]; command_list.sort()
                subcommands = '\n'.join(command_list)
                sche.add_field(name="subcommands", value=subcommands)
            return await ctx.send(embed=sche)


def setup(bot: commands.Bot):
    bot.add_cog(RootHelp(bot))