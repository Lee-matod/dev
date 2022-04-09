from typing import *

import discord

from discord.ext import commands
from discord.ext.commands.core import hooked_wrapped_callback

from dev.utils.utils import MISSING


class CContext(commands.Context):
    def _set_properties(self, author: discord.Member, channel: discord.TextChannel):
        self._author = author
        self._channel = channel

    @property
    def author(self):
        return self._author

    @property
    def channel(self):
        return self._channel


class StringCodeblockConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Union[Tuple[Any, str], Tuple[str]]:
        start_pos: Optional[int] = None
        end_pos: Optional[int] = None

        arguments: str = ""
        codeblock: str = ""
        for i in range(len(argument.split())):
            if argument.split()[i].startswith("```") or "```" in argument.split()[i] and not end_pos:
                start_pos = i
            if argument.split()[i].endswith("```") or "```" in argument.split()[i] and start_pos:
                end_pos = i
        if start_pos and end_pos:
            arguments = argument[start_pos:end_pos + 1].strip(), codeblock.strip()
        return (arguments.strip(),)


class Paginator(discord.ui.View):
    def __init__(self, paginator: commands.Paginator, user_id: int, **kwargs):
        super().__init__()
        self.paginator = paginator
        self.display_page = 0
        self.user_id = user_id
        self.PATH = kwargs.pop("PATH", None)
        self.show_path = kwargs.pop("show_path", False)
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
        await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{self.paginator.pages[self.display_page]}", view=self)

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
            return await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{self.paginator.pages[self.display_page]}", view=self)
        self.enable_or_disable(next_=False, fastforward_=False)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.message.edit(embed=self.is_embed, view=self)
        await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{self.paginator.pages[self.display_page]}", view=self)

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
                return await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{pages}", view=self)
            self.enable_or_disable(rewind_=False, previous_=False)
            self.update_display_page()
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.message.edit(embed=self.is_embed, view=self)
            await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{pages}", view=self)
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
            await interaction.message.edit(content=f"{f'**{self.PATH}**' if self.show_path else ''}\n{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind_=True, previous_=True, next_=True, fastforward_=True)
            await interaction.message.edit(view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete", emoji="🗑️")
    async def delete_page(self, button: discord.Button, interaction: discord.Interaction):
        if isinstance(self.PATH, discord.Message):
            await self.PATH.delete()
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
        self._add_parent: Dict[Union[commands.Command, commands.Group], str] = {}

    def group(self, name: str = MISSING, cls: Type[commands.Group] = MISSING, version: float = MISSING, parent: str = None, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = group(name=name, cls=cls, **kwargs)(func)
            if parent:
                self._add_parent[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator

    def command(self, name: str = MISSING, cls: Type[commands.Command] = MISSING, version: float = MISSING, parent: str = None, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = command(name=name, cls=cls, **kwargs)(func)
            if parent:
                self._add_parent[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator


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


class Command(commands.Command):
    def __init__(self, func, name, *args, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.args = args
        self.kwargs = kwargs

    async def invoke(self, ctx: commands.Context):
        await self.prepare(ctx)
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(ctx, *ctx.args, **ctx.kwargs)

    @property
    def version(self):
        return self.kwargs.get("version", MISSING)


def group(name: str = MISSING, cls=MISSING, **attrs):
    if cls is MISSING:
        cls = Group  # type: ignore

    return command(name=name, cls=cls, **attrs)


def command(name: str = MISSING, cls=MISSING, **attrs):
    if cls is MISSING:
        cls = Command  # type: ignore

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **attrs)

    return decorator


root = GroupMixin()
