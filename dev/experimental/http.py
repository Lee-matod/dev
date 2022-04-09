import io
import re
import sys
import json
import shlex
import inspect
import aiohttp
import discord

from discord.ext import commands

from dev.utils.baseclass import root
from dev.utils.startup import settings
from dev.utils.functs import is_owner, convert_kwargs_format


class RootHTTP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.group(name="http", parent="dev", version=1)
    @is_owner()
    async def root_http(self, ctx: commands.Context, mode: str, name: str, *, value: str = None):
        """
        Add, remove, edit a virtual variable to be used when tokens or API keys are part of a link. You may also check the value or if the variable exists.
        For security reasons, this command is DM only.
        **Modes:**
        `add <name> <value>` = Add a new virtual variable.
        `remove <name>` = Remove an already existing virtual variable.
        `edit <name> <value>` = Edit an already existing virtual variable.
        `value <name>` = Check the value of an already existing virtual variable.
        `exists <name>` = Check if a virtual variable exists.
        """
        if ctx.guild and mode != "get":
            return await ctx.send("For security reasons, this command is DM only.")
        elif mode == "add":
            if value:
                setattr(sys.modules[__name__], name, value)
                return await ctx.send(f"Added `{name}` as a variable.")
            raise commands.MissingRequiredArgument(inspect.Parameter.KEYWORD_ONLY(value))

        elif mode == "remove":
            try:
                delattr(sys.modules[__name__], name)
                return await ctx.send(f"Removed the `{name}` variable.")
            except AttributeError:
                await ctx.send(f"Attribute `{name}` does not exist.")

        elif mode == "edit":
            if value:
                try:
                    if getattr(sys.modules[__name__], name):
                        delattr(sys.modules[__name__], name)
                        setattr(sys.modules[__name__], name, value)
                        return await ctx.send(f"Edited `{name}` variable.")
                except AttributeError:
                    await ctx.send(f"Attribute `{name}` does not exist.")
            raise commands.MissingRequiredArgument(inspect.Parameter.KEYWORD_ONLY(value))

        elif mode == "value":
            try:
                await ctx.send(f"`{name}`: `{getattr(sys.modules[__name__], name)}`")
            except AttributeError:
                await ctx.send(f"Attribute `{name}` does not exist.")

        elif mode == "exists":
            try:
                await ctx.send(f"{bool(getattr(sys.modules[__name__], name))}.")
            except AttributeError:
                await ctx.send(f"False.")

        elif mode == "get":
            command = ctx.bot.get_command("dev http get")
            try:
                values = shlex.split(value)
                mode_ = values[0]; allow_redirects = values[1]; kwargs = values[2:]
            except ValueError:
                mode_ = shlex.split(value)[0]
                allow_redirects = True if len(shlex.split(value)) > 1 else False
                kwargs = shlex.split(value)[3:] if shlex.split(value)[3:] else {}
            await command.__call__(ctx, name, mode_, allow_redirects=allow_redirects, kwargs=kwargs)
        else:
            await ctx.message.add_reaction("❓")

    @root.command(name="get", parent="dev http", version=1)
    @is_owner()
    async def root_http_get(self, ctx: commands.Context, url: str, mode: str, allow_redirects: bool = False, *, kwargs: str = ""):
        """
        Get a response from a specified url. Response modes can differ.
        Virtual variables act as placeholders text for the `url` parameter. Execute `?dev --help|--man http` for more information.
        These variables can be accessed by specifying their name (`%(name)s` in `settings["http"]["format"]`) and meeting with the entire format given.
        **Modes:**
        `status` = Return the status code of the website.
        `json` = Convert the response to JSON. This isn't always available.
        `text` = Send the response as text.
        `read` = Read the response's content and return it.
        """
        async with aiohttp.ClientSession() as session:
            kwargs_ = {}
            attr_pattern = convert_attr_format(settings["http"]["format"])
            matches = re.finditer(pattern=attr_pattern, string=url)
            if matches:
                for match in matches:
                    try:
                        attr = getattr(sys.modules[__name__], match.group(2))
                    except AttributeError:
                        return await ctx.send(f"Attribute `{match.group(2)}` does not exist.")
                    url = url.replace(match.group(1), attr)
            if kwargs:
                kwargs = shlex.split(kwargs)
                compiler = convert_kwargs_format(settings["kwargs"]["format"].strip())
                kwargs_pattern = re.compile(rf"{compiler}")
                for kw in kwargs:
                    match = re.finditer(string=kw, pattern=kwargs_pattern)
                    if match:
                        for m in match:
                            key, word = m.group().split(settings['kwargs']['separator'], 1)
                            kwargs_[key] = word
            try:
                async with session.get(url, allow_redirects=allow_redirects, **kwargs_) as response:
                    if mode == "status":
                        response = response.status
                        await ctx.send(f"Response {response}")
                    elif mode == "json":
                        try:
                            response = await response.json()
                            if len(response) > 3000:
                                return await ctx.send(file=discord.File(filename="response.json", fp=io.BytesIO(response.encode("utf-8"))))
                            await ctx.send(response)
                        except json.JSONDecodeError:
                            await ctx.send("Unable to decode as JSON file.")
                    elif mode == "text":
                        response = await response.text()
                        if len(response) > 3000:
                            return await ctx.send(file=discord.File(filename="response.txt", fp=io.BytesIO(response.encode("utf-8"))))
                        await ctx.send(response)
                    elif mode == "read":
                        response = await response.read()
                        if len(response) > 3000:
                            return await ctx.send(file=discord.File(filename="response.txt", fp=io.BytesIO(response)))
                        await ctx.send(f"{response}")
                    else:
                        await ctx.message.add_reaction("❓")
            except aiohttp.InvalidURL:
                await ctx.send(f"Invalid URL.")


def convert_attr_format(formatter: str):
    format_style = re.compile(r"(%\(\w+\)s)")
    match = re.search(format_style, formatter)
    compiler = "("
    added = False
    for i in range(len(formatter)):
        if i in range(match.start(), match.end()):
            if match and not added:
                compiler += r"(.+?)"
                added = True
                continue
            continue
        elif formatter[i] in [".", "^", "$", "*", "+", "?", "{", "[", "(", ")", "|"]:
            compiler += f"\\{formatter[i]}"
            continue
        compiler += formatter[i]
    compiler += ")"
    return compiler


def setup(bot: commands.Bot):
    bot.add_cog(RootHTTP(bot))