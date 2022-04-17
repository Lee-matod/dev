import discord

from discord.ext import commands

from dev.utils.baseclass import root
from dev.utils.utils import local_globals
from dev.utils.functs import send, is_owner


class ValueSubmitter(discord.ui.Modal):
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph)

    def __init__(self, name: str, new: bool):
        super().__init__(title="Value Submitter")
        self.name = name
        self.new = new

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Successfully {'created a new variable called' if self.new else 'edited'} `{self.name}`")


class ModalSubmitter(discord.ui.View):
    def __init__(self, name: str, new: bool, author: discord.Member):
        super().__init__()
        self.name = name
        self.new = new
        self.author = author

    @discord.ui.button(label="Submit Variable Value", style=discord.ButtonStyle.gray)
    async def submit_value(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            return
        await interaction.response.send_modal(ValueSubmitter(self.name, self.new))
        button.disabled = True
        await interaction.message.edit(view=self)


class RootVariables(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="variable", parent="dev", version=1, aliases=["variables", "vars", "var"])
    @is_owner()
    async def root_variable(self, ctx: commands.Context, mode: str, name: str):
        """A virtual variable manager.
        This allows you to create temporary variables that can later be used as placeholder texts if you want to hide certain things from the public.
        Note that all variables created using this manager will later be destroyed once the bot restarts.
        **Modes:**
        `content` = Sends the content of the variable to ctx.author.
        `exists` = Check if a variable with the given name exists. The bot reacts with a checkmark if it does, else with an X.
        `edit`|`replace` = Edit the contents of an already existing variable.
        `delete`|`del` = Delete an already existing variable.
        `new`|`create` = Create a new variable.
        """
        if mode in ["new", "create"]:
            if name in local_globals:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, "\u200b", view=ModalSubmitter(name, True, ctx.author))

        elif mode in ["delete", "del"]:
            if local_globals.get(name, False):
                del local_globals[name]
                return await send(ctx, f"Successfully deleted the variable `{name}`.")
            await send(ctx, f"No variable called `{name}` found.")

        elif mode in ["edit", "replace"]:
            if name not in local_globals:
                return await send(ctx, f"No variable called `{name}` found.")
            await send(ctx, "\u200b", view=ModalSubmitter(name, False, ctx.author))

        elif mode == "exists":
            if name not in local_globals:
                return await ctx.message.add_reaction("❌")
            await ctx.message.add_reaction("☑")

        elif mode == "content":
            if name not in local_globals:
                return await send(ctx, f"No variable called `{name}` found.")
            await ctx.author.send(f"**{name}:** {local_globals[name]}")

        else:
            await ctx.message.add_reaction("❓")


async def setup(bot):
    await bot.add_cog(RootVariables(bot))