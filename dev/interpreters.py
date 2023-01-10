# -*- coding: utf-8 -*-

"""
dev.interpreters
~~~~~~~~~~~~~~~~

Shell and Python interpreters.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import ast
import asyncio
import inspect
import os
import pathlib
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, IO, Literal, NoReturn, TypeVar, overload

from dev.pagination import Paginator
from dev.components.views import SigKill

from dev.utils.functs import send

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    import discord
    from discord.ext import commands

    from dev import types
    from dev.handlers import GlobalLocals

    P = ParamSpec("P")

T = TypeVar("T")

__all__ = (
    "Execute",
    "Process",
    "ShellSession"
)

CODE_TEMPLATE = """
async def _executor({0}):
    import asyncio

    import discord
    from discord.ext import commands

    import dev

    try:
        pass
    finally:
        _self_variables.update(locals())
    """

WINDOWS = sys.platform == "win32"
POWERSHELL = pathlib.Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe").exists() if WINDOWS else False
SHELL = os.getenv("SHELL") or "/bin/bash"


class Process:
    """A class that wraps a :class:`subprocess.Popen` process

    It is not recommended to instantiate this class. You should instead get an instance through
    :meth:`ShellSession.__call__`.
    It is also recommended to use this class as a context manager to ensure proper process killing handling.

    Parameters
    ----------
    session: :class:`ShellSession`
        The current session that this process will be bound to.
    cwd: :class:`str`
        The current working directory that this process will be in.
    cmd: :class:`str`
        The command that should get executed in a subprocess.

    Attributes
    ----------
    close_code: Optional[:class:`int`]
        The exit code that the process obtains upon it being finished.
    cmd: :class:`str`
        The command string that was passed to the constructor of this class.
    errput: List[:class:`str`]
        A list of exceptions that occurred during the lifetime of this process.
        This list is dynamically populated and exhausted, so it shouldn't be directly accessed.
    force_kill: :class:`bool`
        Whether the process should be forcefully terminated.
    output: List[:class:`str`]
        A list of lines that have been outputted by the subprocess.
        This list is dynamically populated and exhausted, so it shouldn't be directly accessed.
    process: :class:`subprocess.Popen`
        The actual subprocess.
    """

    __slots__ = (
        "__session",
        "_initial_command",
        "close_code",
        "cmd",
        "errput",
        "force_kill",
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

        self._initial_command: bool = False
        for a in cmd.split(";"):
            for b in a.split("&&"):
                if b.strip().startswith("exit"):
                    self.__session.terminated = True
                    break
        self.close_code: int | None = None

    def __repr__(self) -> str:
        return (f"<Process "
                f"cmd={self.cmd!r} "
                f"close_code={self.close_code} "
                f"force_kill={self.force_kill} "
                f"session={self.__session!r}>")

    def __enter__(self) -> Process:
        return self

    def __exit__(self, *_: Any) -> None:
        self.process.kill()
        self.process.terminate()
        self.close_code = self.process.wait(timeout=0.5)

    @overload
    async def run_until_complete(self, context: Literal[None], /) -> str | None:
        ...

    @overload
    async def run_until_complete(
            self,
            context: commands.Context[types.Bot],
            /
    ) -> tuple[discord.Message, Paginator | None]:
        ...

    async def run_until_complete(self, context: commands.Context[types.Bot] | None = None, /) -> Any:
        """Continues executing the current subprocess until it has finished or is forcefully terminated.

        Parameters
        ----------
        context: Optional[:class:`discord.ext.commands.Context`]
            The invocation context in which the function should send the output to. If not given, it will return the
            output as a string when the subprocess is completed.

        Returns
        -------
        Tuple[:class:`discord.Message`, Optional[:class:`Paginator`]]
            If *context* is given, then the message that was sent and paginator are returned. These are the return
            values from :meth:`send`.
            Usually, you shouldn't need these objects
        Optional[:class:`str`]
            If *context* was not given, then the full output of the subprocess is returned.
        """
        str_msg = ""
        while self.is_alive and not self.force_kill:
            if not self._initial_command:
                self._initial_command = True
                if context is None:
                    str_msg = self.__session.add_line(f"{self.__session.interface} {self.cmd.strip()}")
                else:
                    _, paginator = await send(
                        context,
                        self.__session.add_line(f"{self.__session.interface} {self.cmd.strip()}"),
                        SigKill(self),
                        paginator=self.__session.paginator,  # type: ignore
                        forced_pagination=False
                    )
                    if paginator is not None:
                        self.__session.paginator = paginator
            if self.__session.terminated:
                if context is None:
                    return
                return await send(
                    context,
                    self.__session.raw,
                    view=None,
                    paginator=self.__session.paginator,  # type: ignore
                    forced_pagination=False
                )
            try:
                line = await self.in_executor(self.get_next_line)
            except TimeoutError:
                if context is None:
                    return self.__session.set_exit_message("Timed out")
                return await send(
                    context,
                    self.__session.set_exit_message("Timed out"),
                    forced_pagination=False,
                    paginator=self.__session.paginator,  # type: ignore
                    view=None
                )
            except InterruptedError:
                if context is None:
                    return self.__session.raw
                message, paginator = await send(
                    context,
                    self.__session.raw,
                    forced_pagination=False,
                    paginator=self.__session.paginator,  # type: ignore
                    view=None
                )
                if paginator is not None:
                    self.__session.paginator = paginator
                    return message, paginator
                return message, paginator
            if line:
                if context is None:
                    str_msg = self.__session.add_line(line)
                    continue
                _, paginator = await send(
                    context,
                    self.__session.add_line(line),
                    forced_pagination=False,
                    paginator=self.__session.paginator,  # type: ignore
                    view=None
                )
            else:
                if context is None:
                    str_msg = self.__session.raw
                    continue
                _, paginator = await send(
                    context,
                    self.__session.raw,
                    forced_pagination=False,
                    paginator=self.__session.paginator,  # type: ignore
                    view=None
                )
            if paginator is not None:
                self.__session.paginator = paginator
            await asyncio.sleep(0)
        else:
            if context is None:
                return str_msg

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
        """Tries to get the output of the subprocess within a 60-second time frame.

        You should let this function get called automatically by :meth:`run_until_complete`.

        Returns
        -------
        :class:`str`
            The current lines that were outputted by the subprocess.

        Raises
        ------
        InterruptedError
            The subprocess was forcefully killed.
        TimeoutError
            The subprocess did not output anything in the last 60 seconds.
        """
        start = time.perf_counter()
        while not self.output and not self.errput:
            if self.force_kill:
                raise InterruptedError("Subprocess has been killed")
            if time.perf_counter() - start > 60:
                raise TimeoutError("No output in the last 60 seconds")
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
        """:class:`bool`
        Whether the current process is active or has pending output to get formatted.
        """
        return self.process.poll() is None or bool(self.output) or bool(self.errput)


class ShellSession:
    """A system shell session.

    To create a process, you must call an instance of this class with the command that you want to execute.
    This will return a :class:`Process` object which you can use inside a context manager to handle the subprocess.
    It is recommended that you always use the process class inside a context manager so that it can be properly handled.

    Attributes
    ----------
    cwd: :class:`str`
        The current working directory of this session. Defaults to the current working directory of the program.

    Notes
    -----
    Terminated sessions should not and cannot be reinitialized. If you try to reinitialize it, :class:`ConnectionError`
    will be raised.

    Examples
    --------
    .. codeblock:: python3
        shell = ShellSession()
        with shell("echo 'Hello World!'") as process:
            result = await process.run_until_complete()
        print(result)  # Hello World!

        with shell("pwd") as process:
            result = await process.run_until_complete()
        print(result)  # If on a unix system, it will print your current working directory.

        process = shell("cd Desktop")
        with process:
            result = await process.run_until_complete()
        print(result)  # Changes your current working directory to Desktop.

        process = shell("pwd")
        result = await process.run_until_complete()  # I do not recommend doing this!
        print(result)  # If on a unix system, it will print Desktop as your current working directory.
    """
    __slots__ = (
        "__terminate",
        "_previous_processes",
        "_paginator",
        "cwd"
    )

    def __init__(self) -> None:
        self.cwd: str = os.getcwd()
        self._paginator: Paginator | None = None
        self._previous_processes: list[str] = []
        self.__terminate: bool = False

    def __repr__(self) -> str:
        return (f"<ShellSession "
                f"cwd={self.cwd!r} "
                f"prefix={self.prefix!r} "
                f"highlight={self.highlight!r} "
                f"interface={self.interface!r} "
                f"terminated={self.terminated}>")

    @property
    def paginator(self) -> Paginator | None:
        """Optional[:class:`Paginator`]
        The current paginator instance that is being used for this session, if any.
        """
        return self._paginator

    @paginator.setter
    def paginator(self, value: Paginator | None) -> None:
        if value is not None:
            value.force_last_page = True
        self._paginator = value

    @property
    def terminated(self) -> bool:
        """:class:`bool`
        Whether this session has been terminated.
        """
        return self.__terminate

    @terminated.setter
    def terminated(self, value: bool) -> None:
        if self.__terminate and not value:
            raise ConnectionError("Cannot restart a shell session")
        self.__terminate = True

    def __call__(self, script: str) -> Process:
        """Creates a new subprocess and returns it.

        This is the equivalent of executing a command in the system's shell.

        Parameters
        ----------
        script: :class:`str`
            The command that should be executed in the subprocess.

        Returns
        -------
        :class:`Process`
            The process that wraps the executed command.

        Raises
        ------
        ConnectionRefusedError
            The current session has already been terminated.
        """
        if self.terminated:
            raise ConnectionRefusedError("Shell has been terminated. Initiate another shell session")
        return Process(self, self.cwd, script.removesuffix(";"))

    def add_line(self, line: str) -> str:
        """Appends a new line to the current session's interface.

        Parameters
        ----------
        line: :class:`str`
            The line that should get added to the interface.

        Returns
        -------
        :class:`str`
            The full formatted message.
        """
        self._previous_processes.append(line)
        if self.paginator is not None:
            return line.replace("`", "`\u200b")
        return (f"```{self.highlight}\n" + "\n".join(self._previous_processes) + "\n").strip("\n") + "```"

    def set_exit_message(self, msg: str, /) -> str:
        """This is a shorthand to :meth:`add_line` followed by setting :attr:`terminated` to
        `True`.

        Parameters
        ----------
        msg: :class:`str`
            The last message that should get added to the interface of the current session.

        Returns
        -------
        :class:`str`
            The full formatted message.
        """
        self.terminated = True
        if self.paginator is not None:
            return msg.replace("`", "`\u200b")
        return f"```{self.highlight}\n" + "\n".join(self._previous_processes) + f"```\n{msg}"

    @property
    def raw(self) -> str:
        """:class:`str`
        The full formatted interface message of the current session.
        """
        if self.paginator is not None:
            return ""
        return f"```{self.highlight}\n" + "\n".join(self._previous_processes) + f"```"

    @property
    def suffix(self) -> str:
        """:class:`str`
        Gets the current working directory command depending on the OS.
        """
        if WINDOWS:
            return "; cwd"
        return "; pwd"

    @property
    def prefix(self) -> tuple[str, ...]:
        """Tuple[:class:`str`, ...]
        Gets the executable that will be used to process commands.
        """
        if POWERSHELL:
            return "powershell",
        elif WINDOWS:
            return "cmd", "/c"
        return f"{SHELL}", "-c"

    @property
    def interface(self) -> str:
        """:class:`str`
        The prefix in which each new command should start with in this session's interface.
        """
        if POWERSHELL:
            return "PS >"
        elif WINDOWS:
            return "cmd >"
        return "$"

    @property
    def highlight(self) -> str:
        """:class:`str`
        The highlight language that should be used in the codeblock.
        """
        if POWERSHELL:
            return "ps"
        elif WINDOWS:
            return "cmd"
        return "console"


class Execute:
    """Evaluate and execute Python code.

    If the last couple of lines are expressions, yields are automatically prepended.

    Parameters
    ----------
    code: :class:`str`
        The code that should be evaluated and executed.
    global_locals: :class:`GlobalLocals`
        The scope that will get updated once the given code has finished executing.
    args: Dict[:class:`str`, Any]
        An additional mapping of values that will be forwarded to the scope of the evaluation.

    Examples
    --------
    .. codeblock:: python3
        code = "for _ in range(3): print(i)"
        #  Prints 'Hello World' 3 times
        async for expr in Execute(code, GlobalLocals(), {"i": "Hello World"}):
            print(expr)

        code = "1 + 1" \
               "2 + 2" \
               "3 + 3"
        #  Yields the result of each statement
        async for expr in Execute(code, GlobalLocals(), {}):
            print(expr)
    """
    __slots__ = (
        "args_name",
        "args_value",
        "code",
        "vars"
    )

    def __init__(self, code: str, global_locals: GlobalLocals, args: dict[str, Any]) -> None:
        self.code: str = code
        self.vars: GlobalLocals = global_locals
        self.args_name: list[str] = ["_self_variables", *args.keys()]
        self.args_value: list[Any] = [global_locals, *args.values()]

    @property
    def filename(self) -> str:
        return "<repl>"

    async def __aiter__(self) -> AsyncGenerator[Any, Any]:
        exec(compile(self.wrapper(), "<repl>", "exec"), self.vars.globals, self.vars.locals)
        func = self.vars.get("_executor")
        if inspect.isasyncgenfunction(func):
            async for result in func(*self.args_value):
                yield result
        else:
            yield await func(*self.args_value)

    def wrapper(self) -> ast.Module:
        code = ast.parse(self.code)
        template: ast.Module = ast.parse(CODE_TEMPLATE.format(", ".join(self.args_name), int(time.time())))
        function: ast.AsyncFunctionDef = template.body[-1]  # type: ignore

        ast_try: ast.Try = function.body[-1]  # type: ignore
        ast_try.body.extend(code.body)
        ast.fix_missing_locations(template)
        ast.NodeTransformer().generic_visit(ast_try)
        expressions: list[ast.stmt] = ast_try.body

        for index, expr in enumerate(reversed(expressions), start=1):
            if not isinstance(expr, ast.Expr):
                return template

            if not isinstance(expr.value, ast.Yield):
                yield_stmt = ast.Yield(expr.value)
                ast.copy_location(yield_stmt, expr)
                yield_expr = ast.Expr(yield_stmt)
                ast.copy_location(yield_expr, expr)
                ast_try.body[-index] = yield_expr
        return template