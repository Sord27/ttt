
"""Module containing base-class for CLI implementation."""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
import csv
from enum import Enum, unique
from functools import partial
import logging
from pathlib import Path
import sys
from typing import Callable, Dict, List
import time

from botocore.exceptions import ClientError

from . import argparse_type
from .boson_interface import BosonInterface, BosonInterfaceFactory
from .executor import RemoteExecutor, ParallelExecutor, ExecutionResult
from .interface import InterfaceFactory
from . import targeting
from . import rpc_interface


logger = logging.getLogger(__name__)


@unique
class Interfaces(Enum):
    """List of available interfaces."""

    BOSON = "boson"
    RPC = "rpc"

    def __str__(self):
        """Translate enum into readable string for argparse."""
        return str(self.value)


class FRPCFormatter(logging.Formatter):
    """FRPC colored logging formatter."""

    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"
    RESET = "\033[0m"
    FORMAT = "%(asctime)s: {}%(levelname)s{}: %(name)s: %(message)s"

    COLORS = {
        logging.DEBUG: BOLD_WHITE,
        logging.INFO: BOLD_GREEN,
        logging.WARNING: BOLD_YELLOW,
        logging.ERROR: BOLD_RED,
        logging.CRITICAL: BOLD_CYAN,
    }

    def format(self, record):
        """Format a logging record."""
        try:
            escapes = (self.COLORS[record.levelno], self.RESET)
        except KeyError:
            escapes = ("",) * 2

        fmt = self.FORMAT.format(*escapes)

        return logging.Formatter(fmt).format(record)


class CriticalHandler(logging.Handler):
    """Custom logging handler that calls `exit(1)` on critical log events."""

    def createLock(self):
        """Stub. No lock required for this handler."""
        self.lock = None

    def emit(self, record):
        """Crash the application on a critical event."""
        if record.levelno == logging.CRITICAL:
            sys.exit(1)


class BaseFRPC(ABC):
    """Base class for fRPC command-line front-end."""

    DEVICES_LIMIT = 32

    argparser: ArgumentParser
    args: Namespace
    macs: List[str]
    interface_factory: InterfaceFactory
    factories: Dict[Interfaces, Callable[[], InterfaceFactory]]

    def __init__(self, default_argparser: bool = True):
        """CLI implementation base class constructor.

        Arguments:
            default_argparser: when `True` tells the constructor to add
                               default parameters to `self.argparser`.
        """
        self.__targeting_handlers = {
                "no_boson": self.__get_no_boson_macs,
                "no_boson_m2": partial(
                    self.__get_no_boson_macs,
                    dr_filter=lambda x: x.startswith("64dba0f"))
                }

        if default_argparser:
            self._argparser_add_targeting()
            self._argparser_add_interface()
            self._argparser_add_exec()

        self.argparser.add_argument("-v", "--verbose", action="store_true",
                                    help="show debug messages")

        self.argparser.add_argument("--force", action="store_true",
                                    help="bypass the limit on {} devices"
                                         .format(self.DEVICES_LIMIT))

        self.__setup_logging()

        self.factories = {
                Interfaces.BOSON: self.create_boson_factory,
                Interfaces.RPC: self.create_rpc_factory,
                }

    def load(self):
        """Parse args and prepare for program execution."""
        self.args = self.argparser.parse_args()

        if self.args.verbose:
            self.__stream_handler.setLevel(logging.DEBUG)

        self.macs = self.__process_targeting() \
            if hasattr(self.args, "targeting") else None

        if hasattr(self.args, "interface"):
            self.interface_factory = self.create_interface_factory()

    @abstractmethod
    def exec(self):
        """Main program codepath."""
        raise NotImplementedError("Implement program codepath here")

    def create_boson_factory(self):
        """Create boson interface factory from `self.args`."""
        if self.args.boson_index is not None:
            if self.args.boson_range is not None:
                logger.critical("\
either --boson-index or --boson-range may be specified, not both")

            boson_index = self.args.boson_index
        elif self.args.boson_range is not None:
            if len(self.args.boson_range) != 2 or \
                    self.args.boson_range[0] >= self.args.boson_range[1]:

                logger.critical("\
expected --boson-range to have two increasing values")

            boson_index = self.args.boson_range
        else:
            boson_index = None

        return BosonInterfaceFactory(boson_index=boson_index)

    def create_rpc_factory(self):
        """Create RPC factory from `self.args`."""
        try:
            rpc_creds = rpc_interface.load_creds_file(self.args.rpc_env,
                                                      self.args.rpc_creds)
        except (OSError, ValueError):
            logger.exception("failed to load credentials")
            logger.critical("can't continue without credentials")

        return rpc_interface.RPCInterfaceFactory(rpc_creds)

    def create_interface_factory(self):
        """Create interface factory from `self.args`."""
        return self.factories[self.args.interface]()

    @classmethod
    def run(cls):
        """Execute the CLI-program."""
        try:
            frpc = cls()
            frpc.load()
            frpc.exec()
        except KeyboardInterrupt:
            logger.warning("got interrupt")
            sys.exit(130)

    def _argparser_add_targeting(self):
        sumoql_files = ", ".join(targeting.SumoWrapper.get_sumoql_list())
        targeting_strings = ", ".join(
                f"tageting:{key}" for key in self.__targeting_handlers)

        self.argparser.add_argument("targeting",
                                    type=str,
                                    help=f"\
either a csv file exported from sumo (with a `mac' field), \
a local sumoql file, an embedded sumoql file ({sumoql_files}), \
{targeting_strings}")

        self.argparser.add_argument("--devices-limit",
                                    type=argparse_type.irange(start=0),
                                    default=self.DEVICES_LIMIT,
                                    help="overwrite devices limit")

        self.argparser.add_argument("--truncate",
                                    action="store_true",
                                    help="reduce targets amount \
to fit into devices limit")

        self.argparser.add_argument("--sumo-time-offset",
                                    type=argparse_type.irange(start=0),
                                    help="query time offset, \
positive value in seconds, minimum 300")

        timestamp = int(time.time())
        year = 365 * 86400

        self.argparser.add_argument("--sumo-time",
                                    type=argparse_type.irange(
                                        timestamp - year, timestamp + year),
                                    nargs=2,
                                    help="query start and end time, \
in UNIX timestamp")

    def _argparser_add_interface(self):
        self.argparser.add_argument("--interface", type=Interfaces,
                                    choices=list(Interfaces),
                                    default=Interfaces.BOSON,
                                    help="interface to send remote commands")

        self._argparser_add_boson()
        self._argparser_add_rpc()

    def _argparser_add_boson(self):
        self.argparser.add_argument("--boson-index",
                                    type=BosonInterface.validate_index,
                                    help="boson server index to use")

        self.argparser.add_argument("--boson-range", nargs=2,
                                    default=None,
                                    type=BosonInterface.validate_index,
                                    help="randomly generate boson index from \
the specified range for every mac")

    def _argparser_add_rpc(self):
        self.argparser.add_argument("--rpc-creds", type=str, help="OPS portal \
credentials file in JSON format")

        self.argparser.add_argument("--rpc-env", type=str, default="circle1",
                                    choices=rpc_interface.ENVIRONMENTS,
                                    help="Cloud envoronment to use")

    def _argparser_add_exec(self):
        self.argparser.add_argument("--exec-processes",
                                    type=BosonInterface.validate_index,
                                    help="\
number of executors to run in parallel")

        self.argparser.add_argument("--exec-output",
                                    type=Path,
                                    help="write execution results to a .csv")

    def _exec(self, executor: RemoteExecutor,
              output_suffix: str = None) -> List[ExecutionResult]:
        """Main program codepath.

        `self.macs` and `self.interface_factory` must be set before calling
        this function. `BaseFRPC` does this under certain `self.argparser`
        configurations. In other cases, the caller must take care of this.

        Arguments:
            executor: a callable that accepts an `Interface`.
        """
        if self.args.exec_processes is not None:
            executor = ParallelExecutor(
                    self.macs,
                    interface_factory=self.interface_factory,
                    executor=executor,
                    processes=self.args.exec_processes)

            results = executor.run()
        else:
            with self.interface_factory(self.macs) as interface:
                results = executor(interface)

        logger.debug(results)

        if self.args.exec_output is not None and results:
            path = self.args.exec_output

            if output_suffix is not None:
                path = path.with_suffix("." + output_suffix + path.suffix)

            write_header = not path.exists()
            output_file = path.open(mode="a", newline="")

            logger.info(f"{'writing' if write_header else 'APPENDING'} \
execution results to `{path}`")

            writer = csv.DictWriter(output_file,
                                    fieldnames=results[0]._fields,
                                    dialect=csv.unix_dialect)

            if write_header:
                writer.writeheader()

            for result in results:
                writer.writerow(result._asdict())

            output_file.close()
            logger.info(f"done writing {len(results)} entries")

        return results

    def __setup_logging(self):
        self.__stream_handler = logging.StreamHandler()

        self.__stream_handler.setFormatter(FRPCFormatter(self))
        self.__stream_handler.setLevel(logging.INFO)

        critical_handler = CriticalHandler()

        logging.basicConfig(level=logging.DEBUG, handlers=[
            self.__stream_handler,
            critical_handler
            ])

    @staticmethod
    def __parse_csv(string: str):
        macs = None

        try:
            macs = targeting.load_csv(Path(string))
        except (OSError, targeting.ParseError) as err:
            logger.critical(err)

        return macs

    def __parse_sumoql(self, string: str):
        macs = None
        end_time = None

        if self.args.sumo_time is not None:
            if self.args.sumo_time_offset:
                logger.critical("--sumo-time-offset cannot be specified \
with --sumo-time")

            time_offset = self.args.sumo_time[0]
            end_time = self.args.sumo_time[1]
        elif self.args.sumo_time_offset is not None:
            time_offset = self.args.sumo_time_offset
        else:
            logger.critical("either --sumo-time-offset or \
--sumo-time have to be specified for SUMO queries")

        sumo = targeting.SumoWrapper()
        sumoql_path = Path(string)

        if sumoql_path.is_file():
            func = sumo.fetch_macs

            try:
                query = sumoql_path.read_text()
            except OSError as err:
                logger.critical(f"failed to load '{sumoql_path}': {err}")
        elif "/" in string:
            logger.critical(f"file '{string}' not found")
        else:
            func = sumo.fetch_macs_template
            query = string

        try:
            macs = func(query, time_offset, end_time=end_time)
        except OSError as err:
            logger.critical(f"cannot open '{query}': {err}")
        except ValueError as err:
            logger.critical(err)
        except targeting.TargetingError as err:
            logger.critical(f"targeting error: {err}")

        return macs

    def __get_no_boson_macs(
            self,
            dr_filter: Callable[[str], bool] = lambda x: True) -> List[str]:
        if self.args.interface is Interfaces.BOSON:
            logger.critical("cannot use boson interface on no_boson targets")

        try:
            device_registry = targeting.load_latest_device_registry(
                    self.args.rpc_env)
        except targeting.TargetingError as err:
            logger.critical(f"targeting error: {err}")
        except ClientError as err:
            logger.critical(f"S3 access error: {err}")

        device_registry = list(filter(dr_filter, device_registry))

        boson_factory = self.create_boson_factory()
        device_registry_targeting = targeting.DeviceRegistryTargeting(
                device_registry, boson_factory=boson_factory)

        tmp_macs = device_registry_targeting.fetch_no_boson()

        return tmp_macs

    def __process_targeting(self):
        string = self.args.targeting
        macs = []

        if string.startswith("targeting:"):
            target = string[len("targeting:"):]

            if target not in self.__targeting_handlers:
                logger.critical(
                    "other targeting methods haven't been implemented yet")

            macs = self.__targeting_handlers[target]()

        if string.endswith(".csv"):
            macs = self.__parse_csv(string)

        if string.endswith(".sumoql"):
            macs = self.__parse_sumoql(string)
        else:
            for key in ("sumo_time_offset",
                        "sumo_time"):

                args_key = "--" + key.replace("_", "-")

                if getattr(self.args, key) is not None:
                    logger.warning(f"{args_key} works only for SUMO queries")

        if self.args.truncate:
            macs = macs[:self.args.devices_limit]

        if len(macs) > self.args.devices_limit:
            message = f"\
whoaa, you're trying to affect more than {self.args.devices_limit} devices"

            if self.args.force:
                logger.warning(message)
            else:
                logger.critical(message)
        elif len(macs) == 0:
            logger.critical("no macs to process")

        return macs
