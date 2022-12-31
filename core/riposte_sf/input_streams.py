import itertools
from pathlib import Path
from typing import Callable, Generator

from .exceptions import StopRiposteException


def prompt_input(prompt: Callable, _input: Callable) -> Generator[Callable, None, None]:
    """ Unexhaustible generator yielding `input` function forever. """
    yield from itertools.repeat(lambda: _input(prompt()))


def any_input(_input: Callable) -> Generator[Callable, None, None]:
    """ Unexhaustible generator yielding `input` function forever. """
    yield from itertools.repeat(lambda: _input())


def cli_input(inline_commands: str) -> Generator[Callable, None, None]:
    """ Translate inline command provided via '-c' into input stream. """
    yield lambda: inline_commands


def file_input(path: Path) -> Generator[Callable, None, None]:
    """ Read file and translate it into input stream """
    try:
        with open(path, "r") as file_handler:
            for line in file_handler:
                yield lambda: line
    except Exception:
        raise StopRiposteException(f"Problem with reading the file: {path}")
