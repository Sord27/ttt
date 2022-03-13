
"""Utilities for remote script execution from a local file."""


import logging
from os import path
from typing import List
from .command import CommandBuffer
from .interface import ExecutionResult
from . import template


logger = logging.getLogger(__name__)


def _get_script_path(name: str = ""):
    return path.join("scripts", name)


__SCRIPTS = template.list_templates(_get_script_path())


def get_scripts():
    """Return the list of available built-in scripts."""
    return __SCRIPTS


class ScriptExecutor:
    """Executor that executed bash scripts.

    Whenever script returns code 0 it is interpret as a successful execution.
    """

    def __init__(self, script_bodies: List[str]):
        """Construct an script-file executor.

        Arguments:
            script_bodies: List[str]: script bodies list to execute
                                      on the interface.
        """
        self.script_bodies = script_bodies

    def __call__(self, interface) -> List[ExecutionResult]:
        """Execute `script_bodies` on an interface."""
        with CommandBuffer() as buf:
            for script_body in self.script_bodies:
                buf.add_exec(script_body)

            return interface.execute(buf)

    @classmethod
    def get_script_body(cls, script: str):
        """Return script body that corresponds to `script`.

        Arguments:
            script: either script name or file path to read the script from.

        Throws:
            OSError
        """
        if script in get_scripts():
            return template.load_template(_get_script_path(script))

        with open(script) as script_file:
            return script_file.read()
