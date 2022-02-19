import discord

from discord.ext import commands
from discord.utils import MISSING
from discord.ext.commands.core import GroupT, CommandT, Command, Group

from typing import Type

add_parents = {}


class CContext(commands.Context):
    def set_properties(self, a: discord.Member, c: discord.TextChannel):
        self.a = a
        self.c = c

    @property
    def author(self):
        return self.a

    @property
    def channel(self):
        return self.c


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
        b_rewind = [button for button in self.children if button.custom_id == "rewind"][0]
        b_previous = [button for button in self.children if button.custom_id == "previous"][0]
        b_next = [button for button in self.children if button.custom_id == "next"][0]
        b_fastforward = [button for button in self.children if button.custom_id == "fastforward"][0]
        b_rewind.disabled = rewind_
        b_previous.disabled = previous_
        b_next.disabled = next_
        b_fastforward.disabled = fastforward_

    def update_display_page(self):
        current_stop = [b for b in self.children if b.custom_id == "current_stop"][0]
        current_stop.label = self.display_page + 1


class command_(commands.GroupMixin):
    def __init__(self, *args, **kwargs):
        global command_version, add_parents
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        command_version = {}

    def __call__(self, *args, **kwargs):
        return self

    def group(self, name: str = MISSING, cls: Type[GroupT] = MISSING, version: float = MISSING, parent: str = None, *args, **kwargs):
        command_version[name] = version

        def decorator(func) -> GroupT:
            kwargs.setdefault("parent", self)
            result = group(name=name, cls=cls, *args, **kwargs)(func)
            if parent:
                add_parents[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator

    def command(self, name: str = MISSING, cls: Type[CommandT] = MISSING,  version: float = MISSING, parent: str = None, *args, **kwargs):
        command_version[name] = version

        def decorator(func) -> CommandT:
            kwargs.setdefault("parent", self)
            result = command(name=name, cls=cls, *args, **kwargs)(func)
            if parent:
                add_parents[result] = parent
                return result
            self.add_command(result)
            return result
        return decorator

    class Group(commands.Group):
        def __init__(self, *args, **kwargs):
            super().__init__(*args)
            self.args = args
            self.kwargs = kwargs

        def __call__(self, *args, **kwargs):
            return self

        @property
        def version(self):
            return command_version[self.name]

    class Command(commands.Command):
        def __init__(self, *args, **kwargs):
            super().__init__(self)
            self.args = args
            self.kwargs = kwargs

        def __call__(self, *args, **kwargs):
            return self

        @property
        def version(self):
            return command_version[self.name]


commands_ = command_()


def group(name: str = MISSING, cls: Type[GroupT] = MISSING, **attrs):
    if cls is MISSING:
        cls = Group  # type: ignore
    return command(name=name, cls=cls, **attrs)


def command(name: str = MISSING, cls: Type[CommandT] = MISSING, **attrs):
    if cls is MISSING:
        cls = Command  # type: ignore

    def decorator(func) -> CommandT:
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **attrs)

    return decorator
