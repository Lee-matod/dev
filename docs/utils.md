# dev API – utils

These are some utility functions and classes that didn't fall under any other category, so they were placed here 
(much like a miscellaneous section of this documentation).

> ### `class` dev.utils.baseclass.GlobalLocals(__globals=None, __locals=None, /)
> This allows variables to be stored within a class instance, instead of a global scope or dictionary.
> 
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
>>> Deletes a `y` from the global scope, local scope, or both.  
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
>> Items found in the global scope will be returned before checking locals.  
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
>> Returns a list of all global and local scopes with their respective key-value pairs.
>>> #### Returns
>>> Tuple[List[[str](https://docs.python.org/3/library/stdtypes.html#str)], List[Any]] – A joined list of global and 
> local variables from the current scope.
> 
>> ### keys()
>> Returns a list of keys of all global and local scopes.
>>> #### Returns
>>> Tuple[List[[str](https://docs.python.org/3/library/stdtypes.html#str)], List[[str](https://docs.python.org/3/library/stdtypes.html#str)]] – 
>>> A list of a global and local's keys from the current scope.
> 
>> ### update(__new_globals=None, __new_locals=None, /)
>> Update the current instance of variables with new ones.
>>
>>> #### Parameters
>>> - __new_globals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – New instances of 
>>> global variables.
>>> - __new_locals(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]]) – New instances of 
>>> local variables.
>
>> ### values()
>> Returns a list of values of all global and local scopes.
>>> #### Returns
>>> Tuple[List[Any], List[Any]] – A list of a global and local's values from the current scope.

> ### dev.utils.functs.all_commands(command_list)
> Retrieve all commands that are currently available. 
> Unlike [discord.ext.commands.Bot.commands](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.commands), 
> group subcommands are also returned.
> 
>> #### Parameters
>> - command_list(Set[Union[[Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command), [Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group)]]) – 
>> A set of commands, groups or both.
>
>> #### Returns
>> List[Union[[Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command), [Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group)]] – 
>> The full list of all the commands that were found within `command_list`.

> ### dev.utils.functs.flag_parser(string, delimiter)
> Converts a string into a dictionary. 
> This works similarly to [discord.ext.commands.FlagConverter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.FlagConverter), 
> only that it can take an arbitrary number of flags and prefix aren't supported.
> 
>> #### Example Usage
>> ```python
>> >>> my_string = 'key=value abc=foo bar'
>> >>> flag_parser(my_string, '=')
>> {'key': 'value', 'abc': 'foo bar'}
>> ```
>
>> #### Parameters
>> - string([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be converted.
>> - delimiter([str](https://docs.python.org/3/library/stdtypes.html#str)) – The characters that separate keys and 
>> values.
>
>> #### Returns
>> Union[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any], [str](https://docs.python.org/3/library/stdtypes.html#str)] – 
>> The parsed string dictionary or a string if [json.JSONDecodeError](https://docs.python.org/3/library/json.html#json.JSONDecodeError) 
> was raised during parsing.

> ### *await* dev.utils.functs.generate_ctx(ctx, author, channel, **kwargs)
> Create a custom context with changeable attributes such as author or channel.
>
>> #### Parameters
>> - ctx([Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – The 
>> invocation context in which the command was invoked.
>> - author([abc.User](https://discordpy.readthedocs.io/en/latest/api.html#discord.abc.User)) – The author that the 
>> generated context should have.
>> - channel([TextChannel](https://discordpy.readthedocs.io/en/latest/api.html#discord.TextChannel)) – The text channel 
>> that the generated context should have.
>> - kwargs – Any other additional attributes that the generated context should have.
>
>> #### Returns
>> [Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context) – A newly 
>> created context with the given attributes.

> ### dev.utils.utils.plural(amount, singular, include_amount=True)
> A helper function that returns a plural form of the word given if the amount isn't 1 (one).
> 
>> #### Parameters
>> - amount([int](https://docs.python.org/3/library/functions.html#int)) – The amount of things that should be taken into 
>> consideration.
>> - singular([str](https://docs.python.org/3/library/stdtypes.html#str)) – The singular form of the word.
>> - include_amount([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether to return a string with the 
>> included amount.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The formatted string with its plural/singular form.