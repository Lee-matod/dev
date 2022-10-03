# dev API – utils

These are some utility functions and classes that didn't fall under any other category, so they were placed here 
(much like a miscellaneous section of this documentation).

> ### `class` dev.handlers.GlobalLocals(__globals=None, __locals=None, /)
> Allows variables to be stored within a class instance, instead of a global scope or a dictionary.
>> #### Parameters
>> - __globals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – Global scope 
>> variables. Acts the same way as [globals](https://docs.python.org/3/library/functions.html#globals). Defaults to `None`
>> - __locals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – Local scope variables. 
>> Acts the same way as [locals](https://docs.python.org/3/library/functions.html#locals). Defaults to `None`
>
>> ### Supported Operations
>>> #### bool(x)
>>> Whether both global and local dictionaries are empty.
>>
>>> #### len(x)
>>> Returns the added length of both global and local dictionaries.
>>
>>> #### del x[y]
>>> Deletes `y` from the global scope, local scope, or both.  
>>> Raises [KeyError](https://docs.python.org/3/library/exceptions.html#KeyError) if no global or local variable was 
>>> found
>>
>>> #### x[y]
>>> Gets the global and/or local value of `y`.  
>>> Raises [KeyError](https://docs.python.org/3/library/exceptions.html#KeyError) if no global or local variable was 
>>> found
> 
>> ### get(item, default=None)
>> Get an item from either the global scope or the locals scope.
>> Global scope will be searched first, then local scope and if no item is found, the default will be returned.  
>> It's best to use this when you are just trying to get a value without worrying about the scope.
>>> #### Parameters
>>> - item([str](https://docs.python.org/3/library/stdtypes.html#str)) – The item that should be searched for in the 
>>> scopes.
>>> - default(Any) – An argument that should be returned if no value was found. Defaults to ``None``
>>
>>> #### Returns
>>> Any – The value of the item that was found, if it was found.
>
>> ### items()
>> Returns a tuple of all global and local scopes with their respective key-value pairs.
>>> #### Returns
>>> Tuple[Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str), ...], List[Any, ...]] – A joined tuple of 
>>> global and local variables from the current scope.
> 
>> ### keys()
>> Returns a tuple of keys of all global and local scopes.
>>> #### Returns
>>> Tuple[Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str), ...], Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]] – 
>>> A tuple containing the list of global and local keys from the current scope.
> 
>> ### update(__new_globals=None, __new_locals=None, /)
>> Update the current instance of variables with new ones.
>>> #### Parameters
>>> - __new_globals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – New instances of 
>>> global variables.
>>> - __new_locals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – New instances of 
>>> local variables.
>
>> ### values()
>> Returns a tuple of values of all global and local scopes.
>>> #### Returns
>>> Tuple[Tuple[Any, ...], Tuple[Any, ...]] – A tuple containing the list of global and local values from the current 
>>> scope.

> ### dev.utils.functs.all_commands(command_list)
> Retrieve all commands that are currently available from a given set.
> Unlike [discord.ext.commands.Bot.commands](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.commands), 
> group subcommands are also returned.
>> #### Parameters
>> - command_list(Set[types.Command]) – A set of commands, groups or both.
>
>> #### Returns
>> List[types.Command] – 
>> The full list of all the commands that were found within `command_list`.

> ### dev.utils.functs.flag_parser(string, delimiter)
> Converts a string into a dictionary. 
> This works similarly to [discord.ext.commands.FlagConverter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.FlagConverter), 
> only that it can take an arbitrary number of flags and prefixes aren't supported.
>> #### Example Usage
>> ```python
>> >>> my_string = 'key=value abc=foo bar'
>> >>> flag_parser(my_string, '=')
>> {'key': 'value', 'abc': 'foo bar'}
>> ```
>
>> #### Parameters
>> - string([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be converted.
>> - delimiter([str](https://docs.python.org/3/library/stdtypes.html#str)) – The character(s) that separate keys and 
>> values.
>
>> #### Returns
>> - Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any] – The parsed string dictionary.

> ### *await* dev.utils.functs.generate_ctx(ctx, author, channel, **kwargs)
> Create a custom context with changeable attributes.
>> #### Parameters
>> - ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – 
>> The invocation context in which the command was invoked.
>> - kwargs – Any attributes that the generated context should have.
>
>> #### Returns
>> [discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context) – 
>> A newly created context with the given attributes.

> ### dev.utils.utils.plural(amount, singular, include_amount=True)
> A helper function that returns a plural form of the word given if the amount isn't 1 (one).
> 
>> #### Parameters
>> - amount([int](https://docs.python.org/3/library/functions.html#int)) – The amount of things that should be 
>> taken into consideration.
>> - singular([str](https://docs.python.org/3/library/stdtypes.html#str)) – The singular form of the word.
>> - include_amount([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether to return a string with the 
>> included amount.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The formatted string with its plural/singular form.