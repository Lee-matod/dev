from typing import *

import re
import discord

from discord.ext import commands
from discord.ext.commands.core import hooked_wrapped_callback

from dev.utils.utils import MISSING, local_globals


__all__ = (
    "Command",
    "Group",
    "Paginator",
    "StringCodeblockConverter",
    "VirtualVarReplacer",
    "root"
)


class VirtualVarReplacer:
    def __init__(self, settings: dict, string: str):
        self.settings = settings
        self.string = string

    def __enter__(self):
        formatter = self._format()
        matches = re.finditer(formatter, self.string)
        if matches:
            for match in matches:
                var_string, var_name = match.groups()
                if var_name in local_globals:
                    self.string = self.string.replace(var_string, local_globals[var_name])
                else:
                    continue
        return self.string

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _format(self):
        format_style = re.compile(r"(%\(name\)s)")
        match = re.search(format_style, self.settings['virtual_vars_format'])
        compiler = "("
        added = False
        for i in range(len(self.settings['virtual_vars_format'])):
            if i in range(match.start(), match.end()):
                if match and not added:
                    compiler += r"(.+?)"
                    added = True
                    continue
                continue
            elif self.settings['virtual_vars_format'][i] in [".", "^", "$", "*", "+", "?", "{", "[", "(", ")", "|"]:
                compiler += f"\\{self.settings['virtual_vars_format'][i]}"
                continue
            compiler += self.settings['virtual_vars_format'][i]
        compiler += ")"
        return compiler


class StringCodeblockConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Tuple[str, str]:
        start: Optional[int] = None
        end: Optional[int] = None

        for i in range(len(argument)):
            if "".join([argument[i], argument[i+1], argument[i+2]]) == "```":
                if start is None and end is None:
                    start = i
                elif end is None and start is not None:
                    end = i + 3
                    break
        codeblock = argument[start:end]
        arguments = argument[:start]
        return arguments.strip(), codeblock


class Paginator(discord.ui.View):
    def __init__(self, paginator: commands.Paginator, user_id: int, **kwargs):
        super().__init__()
        self.paginator = paginator
        self.display_page = 0
        self.user_id = user_id
        self.is_embed: discord.Embed = kwargs.pop("embed", False)

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, disabled=True, custom_id="rewind")
    async def first_page(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
        self.display_page = 0
        self.enable_or_disable(rewind_=True, previous_=True)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.message.edit(embed=self.is_embed, view=self)
        await interaction.message.edit(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.success, disabled=True, custom_id="previous")
    async def previous_page(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
        self.display_page -= 1
        if self.display_page == 0:
            self.update_display_page()
            self.enable_or_disable(rewind_=True, previous_=True)
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.message.edit(embed=self.is_embed, view=self)
            return await interaction.message.edit(content=f"{self.paginator.pages[self.display_page]}", view=self)
        self.enable_or_disable(next_=False, fastforward_=False)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.message.edit(embed=self.is_embed, view=self)
        await interaction.message.edit(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.red, custom_id="current_stop")
    async def current_stop(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
        button: discord.Button
        for button in self.children:
            if not button.custom_id == "delete":
                button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.success, custom_id="next")
    async def next_page(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
        self.display_page += 1
        try:
            pages = self.paginator.pages[self.display_page]
            if self.display_page == len(self.paginator.pages) - 1:
                self.update_display_page()
                self.enable_or_disable(next_=True, fastforward_=True)
                if self.is_embed:
                    self.is_embed.description = self.paginator.pages[self.display_page]
                    return await interaction.message.edit(embed=self.is_embed, view=self)
                return await interaction.message.edit(content=f"{pages}", view=self)
            self.enable_or_disable(rewind_=False, previous_=False)
            self.update_display_page()
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.message.edit(embed=self.is_embed, view=self)
            await interaction.message.edit(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind_=True, previous_=True, next_=True, fastforward_=True)
            await interaction.message.edit(view=self)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary, custom_id="fastforward")
    async def last_page(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
        self.display_page = len(self.paginator.pages) - 1
        try:
            pages = self.paginator.pages[self.display_page]
            self.enable_or_disable(next_=True, fastforward_=True)
            self.update_display_page()
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.message.edit(embed=self.is_embed, view=self)
            await interaction.message.edit(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind_=True, previous_=True, next_=True, fastforward_=True)
            await interaction.message.edit(view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete", emoji="🗑️")
    async def delete_page(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.message.delete()

    def enable_or_disable(self, *, rewind_=False, previous_=False, next_=False, fastforward_=False):
        button: discord.Button
        b_rewind = [button for button in self.children if button.custom_id == "rewind"][0]
        b_previous = [button for button in self.children if button.custom_id == "previous"][0]
        b_next = [button for button in self.children if button.custom_id == "next"][0]
        b_fastforward = [button for button in self.children if button.custom_id == "fastforward"][0]
        b_rewind.disabled = rewind_
        b_previous.disabled = previous_
        b_next.disabled = next_
        b_fastforward.disabled = fastforward_

    def update_display_page(self):
        b: discord.Button
        current_stop = [b for b in self.children if b.custom_id == "current_stop"][0]
        current_stop.label = self.display_page + 1


class GroupMixin(commands.GroupMixin):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self._assign_cogs: Dict[str, ClassVar] = {}
        self._add_parent: Dict[Union[commands.Command, commands.Group], str] = {}

    def group(self, name: str = MISSING, cls: Type[commands.Group] = MISSING, version: float = MISSING, parent: str = None, supports_virtual_vars: bool = False, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = group(name=name, cls=cls, **kwargs)(func)
            if parent:
                self._add_parent[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator

    def command(self, name: str = MISSING, cls: Type[commands.Command] = MISSING, version: float = MISSING, parent: str = None, supports_virtual_vars: bool = False, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = command(name=name, cls=cls, **kwargs)(func)
            if parent:
                self._add_parent[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator


root = GroupMixin()


class Group(commands.Group):
    def __init__(self, func, name, *args, **kwargs):
        super().__init__(func, name=name, *args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    def command(self, name: str = MISSING, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(name=name, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator

    def group(self, name: str = MISSING, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = group(name=name, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator

    async def invoke(self, ctx: commands.Context) -> None:
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(ctx, *ctx.args, **ctx.kwargs)

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    @property
    def version(self):
        return self.kwargs.get("version", MISSING)

    @property
    def supports_virtual_vars(self):
        return self.kwargs.get("supports_virtual_vars", False)


class Command(commands.Command):
    def __init__(self, func, name, *args, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.args = args
        self.kwargs = kwargs

    async def reinvoke(self, ctx, /, *, call_hooks: bool = False) -> None:
        ctx.command = self
        await self._parse_arguments(ctx)

        if call_hooks:
            await self.call_before_hooks(ctx)

        ctx.invoked_subcommand = None
        try:
            await self.callback(ctx, *ctx.args, **ctx.kwargs)  # type: ignore
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)

    async def invoke(self, ctx: commands.Context):
        await self.prepare(ctx)
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(ctx, *ctx.args, **ctx.kwargs)

    @property
    def version(self):
        return self.kwargs.get("version", MISSING)

    @property
    def supports_virtual_vars(self):
        return self.kwargs.get("supports_virtual_vars", False)


def group(name: str = MISSING, cls=MISSING, **attrs):
    if cls is MISSING:
        cls = Group

    return command(name=name, cls=cls, **attrs)


def command(name: str = MISSING, cls=MISSING, **attrs):
    if cls is MISSING:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **attrs)

    return decorator
