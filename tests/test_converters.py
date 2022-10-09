import pytest
from unittest.mock import Mock

from dev import CodeblockConverter


@pytest.mark.asyncio
async def test_codeblock():
    mock_ctx = Mock()

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

