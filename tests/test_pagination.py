import pytest

from dev.pagination import Interface, Paginator


@pytest.mark.asyncio
async def test_page_setter():
    paginator = Paginator("x")
    paginator.add_line("a" * 1992)
    paginator.add_line("b" * 1992)
    paginator.add_line("c" * 1992)
    assert len(paginator.pages) == 3

    interface = Interface(paginator, 0)
    assert interface.current_page == 1
    assert interface.display_page == "```\n" + "a" * 1992 + "\n```"
    assert interface.current.label == "1"
    assert interface.first_page.disabled is True
    assert interface.previous_page.disabled is True
    assert interface.next_page.disabled is False
    assert interface.last_page.disabled is False

    interface.current_page += 1
    assert interface.current_page == 2
    assert interface.display_page == "```\n" + "b" * 1992 + "\n```"
    assert interface.current.label == "2"
    assert interface.first_page.disabled is False
    assert interface.previous_page.disabled is False
    assert interface.next_page.disabled is False
    assert interface.last_page.disabled is False

    interface.current_page += 1
    assert interface.current_page == 3
    assert interface.display_page == "```\n" + "c" * 1992 + "\n```"
    assert interface.current.label == "3"
    assert interface.first_page.disabled is False
    assert interface.previous_page.disabled is False
    assert interface.next_page.disabled is True
    assert interface.last_page.disabled is True

    interface.current_page -= 1
    assert interface.current_page == 2
    assert interface.display_page == "```\n" + "b" * 1992 + "\n```"
    assert interface.current.label == "2"
    assert interface.first_page.disabled is False
    assert interface.previous_page.disabled is False
    assert interface.next_page.disabled is False
    assert interface.last_page.disabled is False

    interface.current_page -= 1
    assert interface.current_page == 1
    assert interface.display_page == "```\n" + "a" * 1992 + "\n```"
    assert interface.current.label == "1"
    assert interface.first_page.disabled is True
    assert interface.previous_page.disabled is True
    assert interface.next_page.disabled is False
    assert interface.last_page.disabled is False

    interface.current_page = 3
    assert interface.current_page == 3
    assert interface.display_page == "```\n" + "c" * 1992 + "\n```"
    assert interface.current.label == "3"
    assert interface.first_page.disabled is False
    assert interface.previous_page.disabled is False
    assert interface.next_page.disabled is True
    assert interface.last_page.disabled is True

    interface.current_page = 1
    assert interface.current_page == 1
    assert interface.display_page == "```\n" + "a" * 1992 + "\n```"
    assert interface.current.label == "1"
    assert interface.first_page.disabled is True
    assert interface.previous_page.disabled is True
    assert interface.next_page.disabled is False
    assert interface.last_page.disabled is False


def test_paginator():
    paginator = Paginator("")
    paginator.add_line("_" * 2000)
    assert len(paginator.pages) == 2
    paginator.clear()
    assert len(paginator.pages) == 0
    paginator.add_line("_")
    assert len(paginator.pages) == 1
    paginator.add_line("_")
    assert len(paginator.pages) == 2

    paginator = Paginator(prefix="p", suffix="s", max_size=6000)
    paginator.add_line("x" * 100)
    assert len(paginator.pages) == 1
    assert paginator.pages[0][0] == "p" and paginator.pages[0][-1] == "s"
    paginator.add_line("x" * 3000)
    assert len(paginator.pages) == 2

