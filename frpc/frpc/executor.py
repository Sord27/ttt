
"""Module containing base and utility classes for remote execution."""


import logging
import math
from multiprocessing.pool import ThreadPool
from typing import List, Callable
from .interface import ExecutionResult, InterfaceFactory, Interface, \
        InterfaceProgress


# pylint: disable=invalid-name

logger = logging.getLogger(__name__)
_progress = None


RemoteExecutor = Callable[[Interface], List[ExecutionResult]]


def _run_init(prog):
    global _progress  # pylint: disable=global-statement

    _progress = prog


def _run_executor(args):
    executor, interface_factory, macs = args

    with interface_factory(macs, progress=_progress) as interface:
        return executor(interface)


class ParallelExecutor:
    """Class to partition a mac list and execute parallel commands on them."""

    interface_factory: InterfaceFactory
    executor: RemoteExecutor
    macs: List[str]
    batch_size: int
    processes: int

    def __init__(self, macs: List[str], **kwargs):
        """Construct an executor that executes commands in parallel.

        Arguments:
            macs: MAC list.
            interface_factory: InterfaceFactory: a factory that creates
                                                 an interface from a MAC list.
            executor: RemoteExecutor: an executor that accepts interface.
            processes: int = None: number of processes to spawn that will
                                   execute remote commands on split partitions.
        """
        self.interface_factory = kwargs["interface_factory"]
        self.executor = kwargs["executor"]
        self.macs = macs
        self.processes = kwargs.get("processes")
        self.batch_size = math.ceil(len(self.macs) / self.processes)

        if self.batch_size < 2:
            self.batch_size = 2

            logger.warning(f"adjusted batch_size to {self.batch_size}, not \
all threads will be utilized")

        logger.debug(f"selected batch_size = {self.batch_size}")

    def run(self) -> List[ExecutionResult]:
        """Partition mac list and spawn workers for execution."""
        results = []
        progress = InterfaceProgress(len(self.macs))

        with ThreadPool(processes=self.processes, initializer=_run_init,
                        initargs=(progress,)) as pool:

            partitions = [
                    (self.executor,
                     self.interface_factory,
                     self.macs[i: i + self.batch_size])
                    for i in range(0, len(self.macs), self.batch_size)
                    ]

            logger.debug(f"processing {len(partitions)} partitions in \
parallel on {self.processes} processes")

            for res in pool.imap_unordered(_run_executor, partitions):
                results.extend(res)

        return results
