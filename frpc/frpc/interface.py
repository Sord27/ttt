
"""Module for the base interface class."""

from abc import ABC, abstractmethod
import logging
from typing import List, NamedTuple
from threading import Lock
from .command import CommandBuffer
from . import compute


logger = logging.getLogger(__name__)


class ExecutionResult(NamedTuple):
    """Execution result on a single device."""

    mac: str
    returncode: int
    success: bool
    stdout: str
    stderr: str


class InterfaceError(Exception):
    """Generic interface error."""


class FatalInterfaceError(InterfaceError):
    """Generic interface error."""


class InterfaceProgress:
    """Thread-safe execution progress container."""

    def __init__(self, total: int):
        """Construct progress container.

        Arguments:
            total: maximum counter value.
        """
        self.__current = 0
        self.total = total
        self.__lock = Lock()

    def update(self, increment: int):
        """Increment progress counter."""
        self.__lock.acquire()

        current = self.__current + increment
        self.__current = current

        self.__lock.release()

        return current

    @property
    def current(self) -> int:
        """Current progress."""
        self.__lock.acquire()
        current = self.__current
        self.__lock.release()

        return current


class Interface(ABC):
    """Base interface class, every RPC interface should inherit this."""

    def __init__(self, macs: List[str], progress: InterfaceProgress = None):
        """Base class constructor.

        Arguments:
            macs (:list:`str`): pump MACs to connect to.
        """
        self.macs = macs
        self.is_open = False
        self.__progress = InterfaceProgress(len(macs)) \
            if progress is None else progress

    def __enter__(self):
        """Context manager entrance point."""
        self.open()

        return self

    def __exit__(self, *_):
        """Context manager exit point."""
        self.close()

    @abstractmethod
    def open(self):
        """Open a connection over the interface."""
        raise NotImplementedError("Implement your connection here")

    def close(self):
        """Close the connection over the interface."""
        self.is_open = False

    def execute(self, _: CommandBuffer) -> List[ExecutionResult]:
        """Execute the list of commands stored in the command_buffer."""
        if not self.is_open:
            raise RuntimeError("An interface should be opened before \
executing anything")

    def get_online(self) -> List[str]:
        """Return list of active devices in `self.mac`."""
        raise NotImplementedError("method not implemented")

    def _progress(self, increment: int):
        current = self.__progress.update(increment)
        total = self.__progress.total
        step = total // 10

        if step <= 0:
            step = 1

        if current % step == 0:
            perc = compute.perc(current, total)

            logger.info(f"progress {perc:.1f}%: {current} / {total}")


class InterfaceFactory:
    """Factory to create an interface with default argument `macs`."""

    interface_cls = Exception

    def __init__(self, *args, **kwargs):
        """Construct a factory class.

        Simply passes on arguments to interface constructor.
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, macs: List[str], progress: InterfaceProgress = None):
        """Create an interface class."""
        return self.create(macs, progress)

    def create(self, macs: List[str], progress: InterfaceProgress = None):
        """Create an interface instance."""
        return self.interface_cls(macs, *self.args, progress=progress,
                                  **self.kwargs)
