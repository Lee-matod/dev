from typing import *

import discord

from discord.ext import commands
from traceback import format_exception

from dev.utils.baseclass import root
from dev.utils.startup import settings, cogs
from dev.utils.functs import is_owner, generate_ctx, send

if TYPE_CHECKING:
    from dev.experimental.python import RootPython


class ReinvokeFlags(commands.FlagConverter):
    has_: Optional[str] = commands.flag(name="has", default=None)
    startswith_: Optional[str] = commands.flag(name="startswith", default=None)
    endswith_: Optional[str] = commands.flag(name="endswith", default=None)


class RootInvoke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="debug", parent="dev", version=1, aliases=["dbg"])
    async def root_debug(self, ctx: commands.Context, *, command_args):
        """Catch errors when executing a command.
        This command will probably not catch errors with commands that already have an error handler.
        If `settings["folder"]["path_to_file"]` is specified, any instances of this path will be removed if a traceback is sent. Defaults to the current working directory.
        """
        kwargs = {"content": f"{ctx.prefix}{command_args}", "author": ctx.author, "channel": ctx.channel}
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await send(ctx, f"Command `{context.invoked_with}` not found.")
        try:
            await context.command.invoke(context)
            if context.command.name == "python":
                # Since commands.Command.cog will result in None, we must manually get the Cog instance.
                # Apart from that, the `dev python` command has its own error handler, so we must fetch the errors another way.
                python_class: Union[commands.Cog, RootPython] = cogs["RootPython"]
                if python_class.error:
                    error = python_class.error[0]  # For some reason simply having a variable wasn't good enough, so I had to resolve to a list
                    await send(ctx, is_py_bt=True, embed=discord.Embed(title=error.__class__.__name__, description="".join(format_exception(error, error, error.__traceback__)).replace(settings["path_to_file"], ""), color=discord.Color.red()))

        except Exception as e:
            err = "".join(format_exception(e, e, e.__traceback__)).replace(settings["path_to_file"], "")
            await send(ctx, is_py_bt=True, embed=discord.Embed(title=e.__class__.__name__, description=f"{err}", color=discord.Color.red()))

    @root.command(name="execute", parent="dev", version=1.1, aliases=["exec", "execute!", "exec!"])
    @is_owner()
    async def root_execute(self, ctx: commands.Context, attrs: commands.Greedy[Union[discord.Member, discord.TextChannel, discord.Thread]], *, command_attr: str):
        """Execute a command with custom attributes.
        Attributes support types are `discord.Member`, `discord.TextChannel` and `discord.Thread`. These will override the current context, thus executing the command as another user or place.
        Command checks can be optionally disabled by adding an exclamation mark at the end of the `execute` command.
        """
        kwargs = {"content": f"{ctx.prefix}{command_attr}", "author": ctx.author, "channel": ctx.channel}
        for attr in attrs:
            if isinstance(attr, discord.Member):
                kwargs["author"] = attr
            elif isinstance(attr, discord.TextChannel) or isinstance(attr, discord.Thread):
                kwargs["channel"] = attr
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await ctx.send(f"Command `{context.invoked_with}` not found.")
        if ctx.invoked_with.endswith("!"):
            return await context.command.reinvoke(context)
        await context.command.invoke(context)

    @root.command(name="reinvoke", parent="dev", version=1, aliases=["invoke"])
    @is_owner()
    async def root_reinvoke(self, ctx: commands.Context, skip_message: Optional[int] = 0, author: Optional[discord.Member] = None, *, flags: ReinvokeFlags):
        """Reinvoke the last command that was executed.
        By default, it will try to get the last command that was executed, excluding `dev reinvoke` (for obvious reasons).
        If `invoke` is used instead of reinvoke, command checks will not be ignored.
        If `Message.reference` is not of type `None`, then it will try to reinvoke the command that was executed in the reference. This method of reinvocation ignores all other options and flags.
        **Flag arguments:**
        `has`: _str_ = Check if the message has a specific sequence of characters. Defaults to _None_.
        `startswith`: _str_ = Check if the message startswith a specific characters. Defaults to _None_.
        `endswith`: _str_ = Check if the message endswith a specific characters. Defaults to _None_.
        """
        if ctx.message.reference:
            if ctx.message.reference.resolved.content.startswith(ctx.prefix):
                context: commands.Context = await self.bot.get_context(ctx.message.reference.resolved)
                if ctx.invoked_with == "invoke":
                    return await context.command.invoke(context)
                return await context.command.reinvoke(context)
            return await ctx.send("No command found in the message reference.")
        author = author or ctx.author
        c = 0
        async for message in ctx.channel.history(limit=100):
            if message.author == author:
                if message.content.startswith(f"{ctx.prefix}dev reinvoke") or message.content.startswith(f"{ctx.prefix}dev invoke"):
                    skip_message += 1
                    c += 1
                    continue
                if c == skip_message:
                    if flag_checks(message, flags):
                        context: commands.Context = await generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
                        if ctx.invoked_with == "invoke":
                            return await context.command.invoke(context)
                        return await context.command.reinvoke(context)
                c += 1
        await ctx.send("Unable to find any messages matching the given arguments.")


def flag_checks(message: discord.Message, flags: ReinvokeFlags) -> bool:
    if flags.has_:
        if flags.has_ not in message.content:
            return False
    if flags.startswith_:
        if not message.content.startswith(flags.startswith_):
            return False
    if flags.endswith_:
        if not message.content.endswith(flags.endswith_):
            return False
    return True


async def setup(bot):
    await bot.add_cog(RootInvoke(bot))