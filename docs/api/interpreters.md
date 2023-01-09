# interpreters

In addition to providing helper functions and classes, this extension also includes a public API of interpreters.
As of right now, the only interpreters that are available are Python and system shell evaluators.

***

### `class` *async for ... in* dev.interpreters.Execute(code, global_locals, args)

Evaluate and execute Python code.

If the last couple of lines are expressions, yields are automatically prepended.

#### Parameters
- code([str](https://docs.python.org/3/library/stdtypes.html#str)) – The code that should be evaluated and executed.
- global_locals([GlobalLocals](https://github.com/Lee-matod/dev/wiki/utils#class-devhandlersgloballocals__globalsnone-__localsnone-)) –
The scope that will get updated once the given code has finished executing.
- args(Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]) – An additional mapping of values that
  will be forwarded to the scope of the evaluation.

#### Examples

```py
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
```

***

### `class` *with* dev.interpreters.Process(session, cwd, cmd, /)

A class that wraps a [subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen) process

It is not recommended to instantiate this class. You should instead get an instance
through [ShellSession.\_\_call\_\_](https://github.com/Lee-matod/dev/wiki/api#__call__script).
It is also recommended to use this class as a context manager to ensure proper process killing handling.

#### Parameters

- session([ShellSession](https://github.com/Lee-matod/dev/wiki/api#class-devinterpretersshellsession)) – The current
  session that this process will be bound to.
- cwd([str](https://docs.python.org/3/library/stdtypes.html#str)) – The current working directory that this process will
  be in.
- cmd([str](https://docs.python.org/3/library/stdtypes.html#str)) – The command that should get executed in a
  subprocess.

#### Attributes

- close_code(Optional[[int](https://docs.python.org/3/library/functions.html#int)]) – The exit code that the process
  obtains upon it being finished.
- cmd([str](https://docs.python.org/3/library/stdtypes.html#str)) – The command string that was passed to the
  constructor of this class.
- errput(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of exceptions that occurred during
  the lifetime of this process.  
  This list is dynamically populated and exhausted, so it shouldn't be directly accessed.
- force_kill([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether the process should be forcefully
  terminated.
- output(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of lines that have been outputted by
  the subprocess.  
  This list is dynamically populated and exhausted, so it shouldn't be directly accessed.
- process([subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen)) – The actual
  subprocess.

> ### *await* run_until_complete(context=None, /)
> Continues executing the current subprocess until it has finished or is forcefully terminated.
> #### Parameters
> - context(Optional[[discord.ext.commands.Context](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context)]) –
The invocation context in which the function should send the output to. If not given, it will return the output as a
string when the subprocess is completed.
> #### Returns
> Tuple[[discord.Message](https://discordpy.readthedocs.io/en/stable/api.html#discord.Message),
> Optional[[Paginator](https://github.com/Lee-matod/dev/wiki/api#class-devpaginationpaginator)]] –
> If *context* is given, then the message that was sent and paginator are returned. These are the return values from
> [send](https://github.com/Lee-matod/dev/wiki/interactions#await-devutilsfunctssendctx-args-options).  
> Usually, you shouldn't need these objects  
> Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)] –
> If *context* was not given, then the full output of the subprocess is returned.

> ### get_next_line()
> Tries to get the output of the subprocess within a 60-second time frame.
>
> You should let this function get called automatically
by [run_until_complete](https://github.com/Lee-matod/dev/wiki/api#await-run_until_completecontextnone---firstfalse).
> #### Returns
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The current lines that were outputted by the subprocess.
> #### Raises
> - [InterruptedError](https://docs.python.org/3/library/exceptions.html#InterruptedError) – The subprocess was
    forcefully killed.
> - [TimeoutError](https://docs.python.org/3/library/exceptions.html#TimeoutError) – The subprocess did not output
    anything in the last 60 seconds.

> ### `property` is_alive
> [bool](https://docs.python.org/3/library/functions.html#bool) – Whether the current process is active or has pending
output to get formatted.

***

### `class` dev.interpreters.ShellSession

A system shell session.

To create a process, you must call an instance of this class with the command that you want to execute.
This will return
a [Process](https://github.com/Lee-matod/dev/wiki/api#class-with-devinterpretersprocesssession-cwd-cmd-) object which
you can use inside a context manager to handle the subprocess.  
It is recommended that you always use the process class inside a context manager so that it can be properly handled.

#### Attributes

- cwd([str](https://docs.python.org/3/library/stdtypes.html#str)) – The current working directory of this session.
  Defaults to the current working directory of the program.

#### Notes

Terminated sessions should not and cannot be reinitialized. If you try to reinitialize
it, [ConnectionError](https://docs.python.org/3/library/exceptions.html?highlight=timeouterror#ConnectionError) will be
raised.

#### Examples

```py
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
```

> ### \_\_call\_\_(script)
> Creates a new subprocess and returns it.
>
> This is the equivalent of executing a command in the system's shell.
> #### Parameters
> - script([str](https://docs.python.org/3/library/stdtypes.html#str)) – The command that should be executed in the
    subprocess.
> #### Returns
> [Process](https://github.com/Lee-matod/dev/wiki/api#class-with-devinterpretersprocesssession-cwd-cmd-) – The process
that wraps the executed command.
> #### Raises
> - [ConnectionRefusedError](https://docs.python.org/3/library/exceptions.html?highlight=timeouterror#ConnectionRefusedError) –
    The current session has already been terminated.

> ### add_line(line)
> Appends a new line to the current session's interface.
> #### Parameters
> - line([str](https://docs.python.org/3/library/stdtypes.html#str)) – The line that should get added to the interface.
> #### Returns
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The full formatted message.

> ### set_exit_message(msg, /)
> This is a shorthand to [add_line](https://github.com/Lee-matod/dev/wiki/api#add_lineline) followed by
setting [terminated](https://github.com/Lee-matod/dev/wiki/api#property-terminated) to `True`.
> #### Parameters
> - msg([str](https://docs.python.org/3/library/stdtypes.html#str)) – The last message that should get added to the
    interface of the current session.
> #### Returns
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The full formatted message.

> ### `property` paginator
> Optional[[Paginator](https://github.com/Lee-matod/dev/wiki/api#class-devpaginationpaginator)] – The current paginator
instance that is being used for this session, if any.

> ### `property` terminated
> [bool](https://docs.python.org/3/library/functions.html#bool) – Whether this session has been terminated.

> ### `property` raw
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The full formatted interface message of the current
session.

> ### `property` suffix
> [str](https://docs.python.org/3/library/stdtypes.html#str) – Gets the current working directory command depending on
the OS.

> ### `property` prefix
> Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str)] – Gets the executable that will be used to process
commands.

> ### `property` interface
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The prefix in which each new command should start with in
this session's interface.

> ### `property` highlight
> [str](https://docs.python.org/3/library/stdtypes.html#str) – The highlight language that should be used in the
codeblock.