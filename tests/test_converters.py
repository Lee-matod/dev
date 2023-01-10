from typing import Literal

import pytest
from discord.ext.commands import BadBoolArgument
from unittest.mock import Mock

from dev import Settings
from dev.converters import CodeblockConverter, LiteralModes, str_bool, str_ints
from dev.handlers import replace_vars, GlobalLocals

mock_ctx = Mock()


async def send(*args, **kwargs):
    print(f"[1;33m\n{args} --- {kwargs}")


mock_ctx.send.side_effect = send


@pytest.mark.asyncio
async def test_codeblockconverter():
    # Check when single codeblock provided
    text = "```py\ncode\n```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument is None
    assert codeblock == codeblock

    # Check when argument and codeblock are provided
    text = "argument ```py\ncode\n```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == "argument"
    assert codeblock == "```py\ncode\n```"

    # Check when multiple arguments are provided
    text = "one two three ```py\ncode\n```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == "one two three"
    assert codeblock == "```py\ncode\n```"

    # Check when single argument is provided
    text = "argument"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == text
    assert codeblock is None

    # Check when code doesn't end in '\n```', instead just '```'
    text = "```py\ncode```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument is None
    assert codeblock == text

    # Check when code doesn't end in '\n```', instead just '```' and arguments
    text = "argument ```py\ncode```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == "argument"
    assert codeblock == "```py\ncode```"

    # Check for multiple instances of '`'
    text = "``` ` `` `````` ```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument is None
    assert codeblock == text

    # Check for multiple instances of '`', but first one does not start with 3 consecutive ones
    text = "`` ` `` `` ```"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == text
    assert codeblock is None

    # Check for multiple instances of '`', but last one does not finish with 3 consecutive ones
    text = "``` ` `` ``` ``"
    result = await CodeblockConverter().convert(mock_ctx, text)
    assert isinstance(result, tuple) and len(result) == 2

    argument, codeblock = result
    assert argument == text
    assert codeblock is None


@pytest.mark.asyncio
async def test_literalmodes():
    mode = "b"
    mode2 = "C"

    # Check standard use
    cls: LiteralModes = LiteralModes[Literal["a", "b", "c"]]  # type: ignore
    result = await cls.convert(mock_ctx, mode)
    result2 = await cls.convert(mock_ctx, mode2)
    assert result == mode
    assert result2 == mode2

    # Check case sensitivity
    cls: LiteralModes = LiteralModes[Literal["a", "b", "C"], True]  # type: ignore
    result = await cls.convert(mock_ctx, mode)
    result2 = await cls.convert(mock_ctx, mode2)

    assert result == mode
    assert result2 == mode2
    assert result.islower()
    assert result2.isupper()

    # Check item not found
    cls: LiteralModes = LiteralModes[Literal["1", "2", "3"]]  # type: ignore
    result = await cls.convert(mock_ctx, mode)
    result2 = await cls.convert(mock_ctx, mode2)
    assert result is None
    assert result2 is None

    # Check case-sensitive item not found
    cls: LiteralModes = LiteralModes[Literal["a", "B", "c"], True]  # type: ignore
    result = await cls.convert(mock_ctx, mode)
    result2 = await cls.convert(mock_ctx, mode2)
    assert result is None
    assert result2 is None

    # Check input types
    with pytest.raises(TypeError):
        LiteralModes[Literal["a", 1]]  # noqa
    with pytest.raises(TypeError):
        LiteralModes[Literal["a"], "a"]  # noqa
    with pytest.raises(TypeError):
        LiteralModes["a"]  # noqa
    with pytest.raises(TypeError):
        LiteralModes["a", False]  # noqa
    with pytest.raises(TypeError):
        LiteralModes[(1)]  # noqa
    with pytest.raises(TypeError):
        LiteralModes[("a", "b")]  # noqa


def test_str_bool():
    # True normal use case
    result = str_bool("true")
    result1 = str_bool("yes")
    result2 = str_bool("1")
    result3 = str_bool("ON")
    result4 = str_bool("ENABLED")
    assert all((result, result1, result2, result3, result4))

    # False normal use case
    result = str_bool("false")
    result1 = str_bool("no")
    result2 = str_bool("0")
    result3 = str_bool("OFF")
    result4 = str_bool("DISABLED")
    assert not all((result, result1, result2, result3, result4))

    # Default value tests
    result = str_bool("true", False)
    result1 = str_bool("any", True)
    assert result and result1

    # Bad bool raise
    with pytest.raises(BadBoolArgument):
        str_bool("any")
    with pytest.raises(BadBoolArgument):
        str_bool("tru")


def test_str_ints():
    # No numbers
    result = str_ints("abc def")
    assert result == []

    # Single number
    result = str_ints("1")
    assert result == [1]

    # Multiple numbers separated by a space
    result = str_ints("123 456 789")
    assert result == [123, 456, 789]

    # Multiple numbers in between a word
    result = str_ints("123 abc 456")
    assert result == [123, 456]

    # Letters and numbers mixed together
    result = str_ints("1a2b34c5")
    assert result == [1, 2, 34, 5]

    # Letters and numbers mixed together with spaces
    result = str_ints("1 ab3 4jf 56")
    assert result == [1, 3, 4, 56]


def test_replace_vars():
    scope = GlobalLocals({"key": "value", "one": "two", "3": "4", "||hidden||": "hidden"})
    Settings.VIRTUAL_VARS = "|%s|"

    # Normal use case
    result = replace_vars("abc |key|", scope)
    assert result == "abc value"

    # Nothing should be parsed
    result = replace_vars("||", scope)
    assert result == "||"

    # Surrounded by other characters
    result = replace_vars("(abc) |key| (def)", scope)
    assert result == "(abc) value (def)"

    # EOF
    result = replace_vars("| abc |one|", scope)
    assert result == "| abc two"

    # Make sure parsing doesn't get messed up
    result = replace_vars("|||hidden|||", scope)
    assert result == "hidden"

    # No variables in string
    result = replace_vars("abc", scope)
    assert result == "abc"

    # Only 1 variable in string
    result = replace_vars("|any|", scope)
    assert result == "|any|"

    # Check when only leading is given
    Settings.VIRTUAL_VARS = "-%s"
    result = replace_vars("-one two three", scope)
    assert result == "two two three"
    result = replace_vars("two -one three", scope)
    assert result == "two two three"
    result = replace_vars("-one one three", scope)
    assert result == "two one three"

    # Check when only tailing is given
    Settings.VIRTUAL_VARS = "%s-"
    result = replace_vars("one three one-", scope)
    assert result == "one three two"
    result = replace_vars("two three one-", scope)
    assert result == "two three two"
    result = replace_vars("two one- three", scope)
    assert result == "two two three"

    # Check when no additional character is given
    Settings.VIRTUAL_VARS = "%s"
    result = replace_vars("one two three", scope)
    assert result == "two two three"
    result = replace_vars("any value", scope)
    assert result == "any value"
    result = replace_vars("one two one", scope)
    assert result == "two two two"

