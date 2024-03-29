# -*- coding: utf-8 -*-

"""
dev.plugins.shell
~~~~~~~~~~~~~~~~~

Shell interpreter commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import pathlib
import re
import shutil
import tempfile
from typing import TYPE_CHECKING, Dict, List

import discord
from discord.ext import commands

from dev import root
from dev.converters import MessageCodeblock, codeblock_converter
from dev.interpreters import ShellSession
from dev.types import Annotated
from dev.utils.functs import send
from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from dev import types

try:
    import black  # type: ignore
except ModuleNotFoundError:
    _HASBLACK = False  # type: ignore
else:
    _HASBLACK = True

BLACK_ARGS = (
    re.compile(r"(-l|--line-length) ([0-9]+)"),
    re.compile(r"(-t|--target-version) (" + r"|".join(f"py3{vernum}" for vernum in range(3, 12)) + r")"),
)
BLACK_BOOLEANS = (
    "--pyi",
    "--skip-source-first-line",
    "-x",
    "--skip-string-normalization",
    "-S",
    "--skip-magic-trailing-comma",
    "--preview",
    "--check",
    "--diff",
    "--color",
    "--fast",
    "--quiet",
    "-q",
    "--verbose",
    "-v",
)

PYRIGHT_PYPROJ = re.compile(r"^#[ ]*pyproject:[ ]*([a-zA-Z]+)=(.+)$", re.MULTILINE)
PYRIGHT_ARGS = (
    re.compile(r"(--level) (error|warning)"),
    re.compile(r"(--pythonplatform) (Darwin|Linux|Windows)"),
    re.compile(r"(--pythonversion) (" + "|".join(rf"3\.{v}" for v in range(3, 12)) + ")"),
)
PYRIGHT_BOOLEANS = ("--dependencies", "--lib", "--output-json", "--skipunannotated", "--stats", "--warnings")


class RootShell(root.Plugin):
    """Shell interpreter commands"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.active_shell_sessions: Dict[int, ShellSession] = {}

    @root.command("shell", parent="dev", aliases=["sh", "cmd", "bash", "ps"])
    async def root_shell(self, ctx: commands.Context[types.Bot], *, script: Annotated[str, clean_code]):
        """Invoke and evaluate shell commands.

        After initiating a new session, reply to the message containing the terminal output to send
        a new command to the console.
        Type `exit` to quit the session.

        Parameters
        ----------
        script: :class:`str`
            The initial shell script to execute.
        """
        if ctx.author.id in self.active_shell_sessions:
            session = self.active_shell_sessions[ctx.author.id]
            session.terminated = True
        shell = ShellSession()
        self.active_shell_sessions[ctx.author.id] = shell
        try:
            with shell(script) as process:
                await process.run_until_complete(ctx)

            def check(msg: discord.Message) -> bool:
                return (
                    msg.reference is not None
                    and process.message is not None
                    and msg.reference.message_id == process.message.id
                    and msg.author == ctx.author
                    and msg.channel == ctx.channel
                )

            while not shell.terminated and not process.is_alive:
                try:
                    message: discord.Message = await self.bot.wait_for(
                        "message", check=check, timeout=30
                    )
                except asyncio.TimeoutError:
                    return await send(
                        ctx,
                        shell.set_exit_message(f"Return code: `{process.close_code}`"),
                        forced_pagination=False,
                        paginator=shell.paginator,
                    )
                if shell.terminated:  # Early check to prevent errors
                    return await send(
                        ctx,
                        shell.set_exit_message(f"Return code: `{process.close_code}`"),
                        forced_pagination=False,
                        paginator=shell.paginator,
                    )
                with shell(message.content) as process:
                    await process.run_until_complete(ctx)
                await asyncio.sleep(0)
            await send(
                ctx,
                shell.set_exit_message(f"Return code: `{process.close_code}`"),
                forced_pagination=False,
                paginator=shell.paginator,
            )
        finally:
            try:
                del self.active_shell_sessions[ctx.author.id]
            except KeyError:
                pass

    if shutil.which("pyright"):

        @root.command("pyright", parent="dev", require_var_positional=True)
        async def root_pyright(
            self, ctx: commands.Context[types.Bot], *, code: Annotated[MessageCodeblock, codeblock_converter]
        ):
            """Run Pyright with the provided code.

            Arguments that are before the codeblock will be forwarded to Pyright's executable options.

            Adjust a temporary `pyproject.toml` file to your liking by using comments
            (e.g. `# pyproject: typeCheckingMode="strict"`, `# pyproject: pythonVersion="3.9"`).

            Invokes the system shell. This feature is only available if the pyright executable is detected.

            Parameters
            ----------
            code: :class:`MessageCodeblock`
                Pyright arguments and code to type check.
            """
            cmd_args = code.content
            script = code.codeblock
            if script is None:
                return await send(ctx, "Malformed arguments were given.")

            enabled_options: List[str] = [opt for opt in PYRIGHT_BOOLEANS if opt in cmd_args.split()]

            for compiled in PYRIGHT_ARGS:
                match = compiled.search(cmd_args)
                if match:
                    enabled_options.append(f"{match.group(1)} {match.group(2)}")

            with tempfile.TemporaryDirectory() as directory:
                path = pathlib.Path(directory)
                main_tmp = path / "main.py"
                pyproject = path / "pyproject.toml"
                main_tmp.touch()
                pyproject.touch()

                with main_tmp.open("w") as fp:
                    fp.write(
                        "\n".join(
                            (
                                "from typing import *  # type: ignore",
                                "from typing_extensions import *  # type: ignore",
                                script,
                            )
                        )
                    )

                with pyproject.open("w") as fp:
                    pyproject_options = "\n".join(f"{name}={value}" for name, value in PYRIGHT_PYPROJ.findall(script))
                    fp.write(f"[tool.pyright]\n{pyproject_options}")

                full = f"cd {directory} && pyright main.py"
                if enabled_options:
                    full = f"cd {directory} && pyright {' '.join(enabled_options)} main.py"

                session = ShellSession()
                with session(full) as proc:
                    output = await proc.run_until_complete()
                    if output is not None:
                        output = "\n".join(output.split("\n")[13:])  # ignore verbose stuff
                        await send(ctx, codeblock_wrapper(output, "py"))

    if shutil.which("black") and not _HASBLACK:

        @root.command("black", parent="dev", require_var_positional=True)
        async def root_black(
            self, ctx: commands.Context[types.Bot], *, code: Annotated[MessageCodeblock, codeblock_converter]
        ):
            """Format a piece of code using the uncompromising black formatter.

            Arguments that are before the codeblock will be forwarded to black's executable options.

            Invokes the system shell. This feature is only available if the black executable is detected.

            Parameters
            ----------
            code: :class:`MessageCodeblock`
                Black arguments and code to format.
            """
            cmd_args = code.content
            script = code.codeblock
            if script is None:
                return await send(ctx, "Malformed arguments were given.")

            enabled_options: List[str] = [opt for opt in BLACK_BOOLEANS if opt in cmd_args.split()]

            for compiled in BLACK_ARGS:
                match = compiled.search(cmd_args)
                if match:
                    enabled_options.append(f"{match.group(1)} {match.group(2)}")

            with tempfile.TemporaryDirectory() as directory:
                path = pathlib.Path(directory)
                main_tmp = path / "main.py"
                main_tmp.touch()
                with main_tmp.open("w") as fp:
                    fp.write(script)
                full = f"cd {directory} && black main.py"
                if enabled_options:
                    full = f"cd {directory} && black {' '.join(enabled_options)} main.py"

                session = ShellSession()
                with session(full) as proc:
                    output = await proc.run_until_complete()
                    if output is not None:
                        await send(ctx, codeblock_wrapper(output, session.highlight), forced=True)

                with main_tmp.open() as fp:
                    new_file = fp.read()
                    if new_file == script:
                        return
                await send(ctx, codeblock_wrapper(new_file, "py"), forced=True)
