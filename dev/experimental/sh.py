# -*- coding: utf-8 -*-
"""
dev.experimental.sh
~~~~~~~~~~~~~~~~~~~

Shell interpreter commands.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, Callable, IO, NoReturn, TypeVar

import discord
from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    from dev import types

    P = ParamSpec("P")


T = TypeVar("T")

WINDOWS = sys.platform == "win32"
POWERSHELL = pathlib.Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe").exists() if WINDOWS else False
SHELL = os.getenv("SHELL") or "/bin/bash"


class SigKill(discord.ui.View):
    def __init__(self, session: ShellSession, /):
        super().__init__()
        self.session: ShellSession = session
        self.process: Process | None = session.current_process

    @discord.ui.button(label="Kill", emoji="\u26D4", style=discord.ButtonStyle.danger)
    async def signalkill(self, interaction: discord.Interaction, button: discord.ui.Button[SigKill]):
        assert self.process is not None
        self.process.process.kill()
        self.process.process.terminate()
        self.process.force_kill = True
        await interaction.response.edit_message(
            content=self.session.raw.replace(Settings.PATH_TO_FILE, "~"),
            view=SigKill(self.session)
        )


class Process:
    __slots__ = (
        "__session",
        "close_code",
        "cmd",
        "errput",
        "force_kill",
        "has_set_cmd",
        "loop",
        "output",
        "process",
        "stdout_task",
        "stderr_task",
    )

    def __init__(self, session: ShellSession, cwd: str, cmd: str, /) -> None:
        self.__session: ShellSession = session
        self.cmd: str = cmd
        self.force_kill: bool = False
        self.has_set_cmd: bool = False
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.process: subprocess.Popen[bytes] = subprocess.Popen(
            session.prefix + (cmd + session.suffix,),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
        self.errput: list[str] = []
        self.output: list[str] = []
        self.stdout_task: asyncio.Task[str | None] | None = self.start_reading(
            self.process.stdout,
            lambda b: self.output.append(b.decode("utf-8").replace("``", "`\u200b`").strip("\n"))
        ) if self.process.stdout else None
        self.stderr_task: asyncio.Task[str | None] | None = self.start_reading(
            self.process.stderr,
            lambda b: self.errput.append(b.decode("utf-8").replace("``", "`\u200b`").strip("\n"))
        ) if self.process.stderr else None

        for a in cmd.split(";"):
            for b in a.split("&&"):
                if b.strip().startswith("exit"):
                    self.__session.terminate = True
                    break
        self.close_code: int | None = None

    def __enter__(self) -> Process:
        return self

    def __exit__(self, *_: Any) -> None:
        self.process.kill()
        self.process.terminate()
        self.close_code = self.process.wait(timeout=0.5)

    async def run_until_complete(
            self,
            context: commands.Context[types.Bot],
            /,
            *,
            first: bool = False
    ) -> discord.Message | None:
        while self.is_alive and not self.force_kill:
            if not first and not self.has_set_cmd:
                self.__session.add_line(f"{self.__session.interface} {self.cmd.strip()}")
                self.has_set_cmd = True
            if self.__session.terminate:
                return
            try:
                line = await self.in_executor(self.get_next_line)
            except TimeoutError:
                return await send(
                    context,
                    self.__session.set_exit_message("Timed out").replace(Settings.PATH_TO_FILE, "~")
                )
            except InterruptedError:
                return await send(
                    context,
                    self.__session.raw.replace(Settings.PATH_TO_FILE, "~"),
                    SigKill(self.__session)
                )
            if line:
                await send(
                    context,
                    self.__session.add_line(line).replace(Settings.PATH_TO_FILE, "~"),
                    SigKill(self.__session)
                )
            else:
                await send(context, self.__session.raw.replace(Settings.PATH_TO_FILE, "~"), SigKill(self.__session))

    def start_reading(self, stream: IO[bytes], callback: Callable[[bytes], Any]) -> asyncio.Task[str | None]:
        return self.loop.create_task(
            self.in_executor(self.reader, stream, callback)
        )

    async def in_executor(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        return await self.loop.run_in_executor(None, func, *args)

    def reader(self, stream: IO[bytes], callback: Callable[[bytes], Any]) -> None:
        for line in iter(stream.readline, b""):
            self.loop.call_soon_threadsafe(callback, line)

    def get_next_line(self) -> str | NoReturn:
        start = time.perf_counter()
        while not self.output and not self.errput:
            if self.force_kill:
                raise InterruptedError
            if time.perf_counter() - start > 60:
                raise TimeoutError
        if self.process.poll() is None:
            out = ("\n".join(self.output) + "\n" + "\n".join(self.errput)).strip("\n")
        else:
            out = ("\n".join(self.output[:-1]) + "\n" + "\n".join(self.errput)).strip("\n")
            self.__session.cwd = self.output[-1]
        self.output.clear()
        self.errput.clear()
        return out

    @property
    def is_alive(self) -> bool:
        return self.process.poll() is None or bool(self.output) or bool(self.errput)


class ShellSession:
    __slots__ = (
        "__terminate",
        "_previous_processes",
        "current_process",
        "cwd"
    )

    def __init__(self) -> None:
        self.cwd: str = os.getcwd()
        self.current_process: Process | None = None
        self._previous_processes: list[str] = []
        self.__terminate: bool = False

    @property
    def terminate(self) -> bool:
        return self.__terminate

    @terminate.setter
    def terminate(self, value: bool) -> None:
        if self.__terminate and not value:
            raise ConnectionError("Cannot restart a shell session")
        self.__terminate = True

    def __call__(self, script: str) -> Process:
        if self.terminate:
            raise ConnectionRefusedError("Shell has been terminated. Initiate another shell session")
        self.current_process = Process(self, self.cwd, script)
        return self.current_process

    def format_process(self, p: Process, /) -> str:
        resp = (f"```{self.highlight}\n{self.interface} {p.cmd.strip()}".strip()
                + "\n".join(self._previous_processes)
                + "\n").strip("\n")
        output: str = (
                ("".join(p.output).replace("``", "`\u200b`") if p.output else "")
                + "\n"
                + ("".join(p.errput).replace("``", "\u200b") if p.errput else "")
        )
        self._previous_processes.append(f"{self.interface} {p.cmd.strip()}\n{output}".strip("\n"))
        resp = (resp + output).strip("\n") + "```"
        return resp

    def add_line(self, line: str) -> str:
        self._previous_processes.append(line)
        return (f"```{self.highlight}\n" + "\n".join(self._previous_processes) + "\n").strip("\n") + "```"

    def set_exit_message(self, msg: str, /) -> str:
        self.terminate = True
        return f"```{self.highlight}\n" + "\n".join(self._previous_processes) + f"```\n{msg}"

    @property
    def raw(self) -> str:
        return f"```{self.highlight}\n" + "\n".join(self._previous_processes) + f"```"

    @property
    def suffix(self) -> str:
        if WINDOWS:
            return "; cwd"
        return "; pwd"

    @property
    def prefix(self) -> tuple[str, ...]:
        if POWERSHELL:
            return "powershell",
        elif WINDOWS:
            return "cmd", "/c"
        return f"{SHELL}", "-c"

    @property
    def interface(self) -> str:
        if POWERSHELL:
            return "PS >"
        elif WINDOWS:
            return "cmd >"
        return "$"

    @property
    def highlight(self) -> str:
        if POWERSHELL:
            return "ps"
        elif WINDOWS:
            return "cmd"
        return "console"


class RootShell(Root):
    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.active_shell_sessions: list[int] = []

    @root.command(name="shell", parent="dev", aliases=["sh", "cmd", "bash", "ps"])
    async def root_shell(
            self,
            ctx: commands.Context[types.Bot],
            *,
            script: clean_code  # type: ignore
    ) -> discord.Message | None:
        if ctx.author.id in self.active_shell_sessions:
            return await send(ctx, "A shell session is already active, please close it before starting a new one.")
        else:
            self.active_shell_sessions.append(ctx.author.id)
        shell = ShellSession()
        with shell(script) as process:  # type: ignore
            await send(ctx, shell.format_process(process).replace(Settings.PATH_TO_FILE, "~"), SigKill(shell))
            await process.run_until_complete(ctx, first=True)

        def check(msg: discord.Message) -> bool:
            return (
                    msg.author == ctx.author
                    and msg.channel == ctx.channel
                    and msg.content.startswith(shell.interface.lower())
            )

        while not shell.terminate and not process.is_alive:
            try:
                message: discord.Message = await self.bot.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                self.active_shell_sessions.remove(ctx.author.id)
                return await send(
                    ctx,
                    shell.set_exit_message(f"Return code: `{process.close_code}`").replace(Settings.PATH_TO_FILE, "~")
                )
            with shell(message.content[len(shell.interface):].strip()) as process:
                await process.run_until_complete(ctx)
        await send(
            ctx,
            shell.set_exit_message(f"Return code: `{process.close_code}`").replace(Settings.PATH_TO_FILE, "~")
        )
        self.active_shell_sessions.remove(ctx.author.id)
