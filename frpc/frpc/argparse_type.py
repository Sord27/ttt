
"""This module contains various helpers for argparse type."""

from argparse import ArgumentTypeError
import math
from pathlib import Path
from typing import Callable, IO


def frange(start: float = -math.inf, end: float = math.inf,
           start_inc: bool = True,
           end_inc: bool = True) -> Callable[[str], int]:
    """Generate a function that parses a float in selected range.

    Arguments:
        start (:obj:`float`): start of the range.
        end (:obj:`float`): end of the range.
        start_inc (:obj:`bool`): include `start` into the range if `True`.
        end_inc (:obj:`bool`): include `end` into the range if `True`.

    """
    def parse(string):
        try:
            value = float(string)
            err = (value < start or value > end or
                   (value == start and not start_inc) or
                   (value == end and not end_inc))
        except ValueError:
            err = True

        if err:
            raise ValueError("expected a float value in range {}{};{}{}"
                             .format("[" if start_inc else "(",
                                     start, end,
                                     "]" if start_inc else ")"))

        return value

    return parse


def irange(start: float = -math.inf,
           end: float = math.inf) -> Callable[[str], int]:
    """Generate a function that parses an integer in range [start; end].

    Arguments:
        start (:obj:`int`): start of the range.
        end (:obj:`int`): end of the range.

    """
    def parse(string):
        try:
            value = int(string)
            err = value < start or value > end
        except ValueError:
            err = True

        if err:
            raise ValueError("expected an integer value in range [{};{}]"
                             .format(start, end))

        return value

    return parse


def file_type(**kwargs) -> Callable[[str], IO]:
    """Generate a function that parses filepath to a file.

    Arguments:
        See docs on the built-in `open()` function.
    """
    def parse(string):
        try:
            return open(string, **kwargs)
        except OSError as err:
            msg = "cannot open `{}`: {}".format(string, err)

            raise ArgumentTypeError(msg) from err

    return parse


def filepath_type() -> Callable[[str], Path]:
    """Generate a function that parses filepath into a Path and check.

    Checks for file existance as well.
    """
    def parse(string):
        path = Path(string)

        if not path.is_file():
            raise ArgumentTypeError(f"`{string}` is not a file")

        return path

    return parse
