
"""Module describing program behaviour for pre- and post-deploy activities."""

from argparse import ArgumentParser
from datetime import datetime, timezone
from enum import Enum, unique
import functools
import json
import logging
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Iterator
import time
import numpy
from .argparse_type import frange, irange, filepath_type
from .base_frpc import BaseFRPC
from . import compute
from . import executor
from .script_executor import ScriptExecutor
from . import targeting


logger = logging.getLogger(__name__)


class PersistentState(dict):
    """Dictionary-based container that can persist on disk."""

    path: Path

    def __init__(self, path=None, path_generator=None):
        """Class constructor.

        Arguments:
            path: path to a state file in JSON format.
                  If passed, the class will be constructed from it.
            path_generator: function that takes in a suffix and generates
                            a filename for it.
        """
        if path is None:
            path = path_generator("")
            i = 1

            while path.exists():
                if i > 10:
                    logger.critical("couldn't generate a state file name")

                path = path_generator(f".{i}")
                i += 1

        self.path = path

        super().__init__(self._load())

    def _load(self):
        if self.path.exists():
            try:
                with self.path.open() as state_file:
                    state = json.load(state_file)

                logger.info(f"recovering from a state file {self.path}")

                return state
            except OSError:
                logger.exception("failed to open existing state file")
            except json.JSONDecodeError:
                logger.exception("failed to parse existing state file")

            logger.critical("couldn't recover previous state")

        return {}

    def save(self):
        """Save the current state into the file."""
        try:
            state_exists = self.path.exists()

            with self.path.open("w") as state_file:
                json.dump(self, state_file, indent=4)

            if not state_exists:
                logger.info(f"created a new state file {self.path}")
        except OSError:
            logger.exception("failed to create a state file")
            logger.critical("proceeding without a state backup isn't safe")


@unique
class DeployType(Enum):
    """Enumeration of available deploy types."""

    FULL = "full"
    PTG = "ptg"

    def __str__(self):
        """Translate enum into readable string for argparse."""
        return str(self.value)


class TargetAction(NamedTuple):
    """Fix pumps based on sumo query."""

    name: str
    fetch_macs: Callable[[], List[str]]
    mk_executor: Callable[[], executor.RemoteExecutor]


class Generator:
    """Base generator class."""

    state: PersistentState

    def __init__(self, state: PersistentState, predeploy: bool = True):
        """Construct a generator. Every generator should call this.

        Arguments:
            state: state dictionary from `FRPCDeploy` class.
            predeploy: determines `_have_time()` behaviour,
                       if it's not a pre-deploy we always have time.
        """
        self.state = state
        self.predeploy = predeploy

    def __call__(self) -> Iterator[List[str]]:
        """Generate MACs lists."""

    def wait(self):
        """Time list generator."""

    def _have_time(self, start_time) -> bool:
        if not self.predeploy:
            return True

        diff = start_time - time.time()
        stb = self.state["safety_time_buffer"]

        if diff <= stb:
            logger.warning(f"{diff:.2f}s left until deploy, \
which is less than the specified safety time buffer of {stb}s")

            return False

        return True


class OTDeployGenerator(Generator):
    """MAC lists generator for full overtime deploy."""

    BUCKETS = 16384
    START_TIME_KEY = "ot_deploy_generator_start_time"

    buckets: List[List[str]]
    cutoff: int

    def __init__(self, state: PersistentState, predeploy: bool = True):
        """Prepare bucket lists."""
        super().__init__(state, predeploy)

        logger.info(
                f"prepairing {self.BUCKETS} buckets for overtime deploy")

        self.buckets = [[] for _ in range(self.BUCKETS)]

        for mac in state["device_registry"]:
            bucket = int(mac, 16) % self.BUCKETS

            self.buckets[bucket].append(mac)

        lengths = numpy.array([
            len(bucket) for bucket in self.buckets
            ])

        logger.info(f"bucket length max = {lengths.max()}, \
min = {lengths.min()}, std = {lengths.std():.2f}")

        self.__start_time_key = self.START_TIME_KEY + \
            ("_predeploy" if predeploy else "_postdeploy")

    def __call__(self) -> Iterator[List[str]]:
        """Mac lists generator."""
        if self.__start_time_key not in self.state:
            self.state[self.__start_time_key] = time.time()

        for cutoff in range(self.BUCKETS):
            self.cutoff = cutoff
            server_time = self.__calc_bucket_time(self.state["start_time"])

            if not self._have_time(server_time):
                return

            yield self.buckets[cutoff]

    def wait(self):
        """List generation timing."""
        delay = self.__calc_bucket_time() - time.time()

        if delay > 0:
            logger.debug(f"MACs list generation paused for {delay:.2f}s")
            time.sleep(delay)

    def __calc_bucket_time(self, start_time: float = None) -> float:
        if start_time is None:
            start_time = self.state[self.__start_time_key]

        return start_time + \
            self.cutoff * self.state["span_time"] * 60 / self.BUCKETS


class ImmediateDeployGenerator(Generator):
    """MAC lists generator for PTG deploy (simply returns the full list)."""

    def __call__(self) -> Iterator[List[str]]:
        """Return full MAC list."""
        if not self._have_time(self.state["start_time"]):
            return

        yield self.state["device_registry"]


def resize_generator(generator: Generator, min_size: int,
                     offset: int = None) -> Iterator[List]:
    """Resize lists generated by `generator` to lists of `min_size`."""
    chunk = []

    for item in generator():
        chunk.extend(item)

        if offset is not None:
            if len(chunk) <= offset:
                continue

            chunk = chunk[offset:]
            offset = None

        if len(chunk) >= min_size:
            generator.wait()
            yield chunk
            chunk = []

    if len(chunk) > 0:
        generator.wait()
        yield chunk


def _mk_se_creator(name: str) -> Callable[[], ScriptExecutor]:
    return lambda: ScriptExecutor([ScriptExecutor.get_script_body(name)])


class DeployActivity:
    """Container for pre-programmed deploy activities."""

    target_actions: List[TargetAction]
    state: PersistentState
    name: str

    def __init__(self, target_actions: List[TargetAction],
                 state: PersistentState,
                 name: str = "deploy_activity"):
        """Construct a container for deploy activities.

        Arguments:
            target_actions: list of `TargetAction` to execute.
        """
        self.target_actions = target_actions
        self.state = state
        self.name = name

        self.__state = state.get(name, {})
        state[name] = self.__state

        if "offset" not in self.__state:
            self.__state["offset"] = 0

    def fetch_targets(self):
        """Fetch MAC lists for target actions."""
        targets = self.__state.get("targets", {})
        failed_targets = self.__state.get("failed_targets", {})

        for target_action in self.target_actions:
            if target_action.name not in targets:
                targets[target_action.name] = target_action.fetch_macs()

            if target_action.name not in failed_targets:
                failed_targets[target_action.name] = []

        self.__state["targets"] = targets
        self.__state["failed_targets"] = failed_targets

    def mk_executors(self) -> Dict[str, executor.RemoteExecutor]:
        """Create executors for target actions."""
        if self.state["dry_run"]:
            nop_executor = _mk_se_creator("nop.sh")()

            return {
                    target_action.name: nop_executor
                    for target_action in self.target_actions
                }

        return {
                target_action.name: target_action.mk_executor()
                for target_action in self.target_actions
                }

    def exec(self, mac_lists_generator: Generator,
             macs_executor: Callable[[List[str], str,
                                      executor.RemoteExecutor],
                                     List[executor.ExecutionResult]]):
        """Execute deploy activities."""
        actions = ", ".join(i.name for i in self.target_actions)

        logger.info(f"starting {self.name}, the target actions are: {actions}")

        self.fetch_targets()
        executors = self.mk_executors()

        failed = 0
        total = len(self.state["device_registry"])

        self.state.save()

        for macs in resize_generator(mac_lists_generator,
                                     self.state["batch_size"],
                                     offset=self.__state["offset"]):
            for action_name, action_executor in executors.items():
                action_macs = targeting.device_registry_select(
                        self.__state["targets"][action_name], macs)

                results = macs_executor(action_macs, action_name,
                                        action_executor)

                for result in results:
                    if not result.success:
                        self.__state["failed_targets"][action_name] \
                            .append(result.mac)

            self.__state["offset"] += len(macs)

            failed = sum([
                len(macs) for macs in self.__state["failed_targets"].values()
                ])

            logger.info(f'{self.name} progress (processed / failed / total): \
{self.__state["offset"]} ({compute.perc(self.__state["offset"], total):.2f}%) \
/ {failed} ({compute.perc(failed, self.__state["offset"]):.2f}%) / \
{total}')

            self.state.save()


class FRPCDeploy(BaseFRPC):
    """CLI implementation for deploy activities.

    For more info see the program description in argparse.
    """

    # pylint: disable=too-many-instance-attributes

    EPILOG = """\
This is a program for running pre- and post-deploy activities. It recovers
devices that have connectivity issues and are likely to fail the update.
The approach this program uses doesn't work in 100% of the cases, but
it covers most of them. It is capable of accompanying an ETG, PTG or full
deploy.

Depending on the type of deploy, it may use your local AWS, OPS and boson
credentials so MAKE SURE to configure those beforehand.
"""

    state: PersistentState
    dr_targeting: targeting.DeviceRegistryTargeting
    mac_lists_generator: Callable[[], Iterator[List[str]]]
    predeploy_activity: DeployActivity
    postdeploy_activity: DeployActivity

    __wait_offset: float = 0.

    def __init__(self):
        """CLI implementation constructor."""
        self.argparser = ArgumentParser(
                description="Execute pre- and post-deploy activities.",
                epilog=self.EPILOG)

        self.argparser.add_argument("deploy_type", type=DeployType,
                                    choices=list(DeployType),
                                    help="deploy type that is being used")

        self.argparser.add_argument("device_registry", type=filepath_type(),
                                    help="\
file that represents a list of devices participating in the update. \
For a FULL deploy this should the device registry file. \
For PTG/ETG deploy this should a .csv file")

        super().__init__(default_argparser=False)

        self._argparser_add_boson()
        self._argparser_add_rpc()
        self._argparser_add_exec()

        self.argparser.add_argument("--state-file", type=Path, help="\
File to save to or load current state from")

        self.argparser.add_argument("--span-time", type=irange(1),
                                    help="full deploy span time in minutes")

        self.argparser.add_argument("--start-time",
                                    type=frange(time.time() - 86400),
                                    required=True,
                                    help="planned deploy time in UNIX \
timestamp")

        self.argparser.add_argument("--safety-time-buffer",
                                    type=irange(60),
                                    default=15 * 60,
                                    help="minimum possible time difference, \
in seconds, between the start of a pre-deploy activity on a device \
and the actual deploy")

        self.argparser.add_argument("--install-time",
                                    type=irange(60),
                                    default=16 * 60,
                                    help="maximum time it takes for the \
software to be fully installed")

        self.argparser.add_argument("--sumo-delay",
                                    type=irange(10),
                                    default=5 * 60,
                                    help="time it takes for a newly created \
to get from a device to SumoLogic")

        self.argparser.add_argument("--batch-size", type=irange(2),
                                    default=7500,
                                    help="minimum processing batch size")

        self.argparser.add_argument("--dry-run", action="store_true",
                                    help="send NOP instead of the fix")

    def load(self):
        """Parse args and prepare for program execution."""
        super().load()

        self._load_state()

        try:
            self.dr_targeting = targeting.DeviceRegistryTargeting(
                    self.state["device_registry"],
                    boson_factory=self.create_boson_factory())
        except targeting.SumoConfigError:
            logger.exception(
                    f"no valid config in `{targeting.SUMO_DEFAULT_CONFIG}`")

            logger.critical("can't continue without sumo access")

        predeploy_target_actions = [
                TargetAction(
                    "connectivity_issues",
                    functools.partial(self.dr_targeting.fetch_sumo,
                                      "connectivity-issues.sumoql"),
                    _mk_se_creator("reboot.sh")
                    ),
                TargetAction(
                    "no_boson",
                    self.dr_targeting.fetch_no_boson,
                    _mk_se_creator("tunnel_start.sh")
                    ),
                ]

        self.predeploy_activity = DeployActivity(predeploy_target_actions,
                                                 self.state,
                                                 name="predeploy_activity")

        postdeploy_target_actions = [
                TargetAction(
                    "bamio_not_ready",
                    self.__mk_fetch_sumo_st("bamio-not-ready.sumoql"),
                    _mk_se_creator("reboot.sh")
                    ),
                ]

        self.postdeploy_activity = DeployActivity(postdeploy_target_actions,
                                                  self.state,
                                                  name="postdeploy_activity")
        self.mac_lists_generator = {
                DeployType.FULL.name: OTDeployGenerator,
                DeployType.PTG.name: ImmediateDeployGenerator,
                }[self.state["deploy_type"]]

    def exec(self):
        """Main program codepath."""
        logger.info(f"executing a {self.state['deploy_type']} deploy")

        logger.info(f"\
device registry contains {len(self.state['device_registry'])} MACs")

        if self.state["deploy_type"] == DeployType.FULL.name:
            logger.info(f"span time is {self.state['span_time']} minutes")

        if self.state["finished"]:
            logger.info("current state says that we have already finished \
pre-deploy activities")

            return

        self.interface_factory = self.create_rpc_factory()

        self.predeploy_activity.exec(self.mac_lists_generator(self.state),
                                     self._exec_macs)

        self.__wait(0, "the deploy to begin")

        if self.state["deploy_type"] == DeployType.FULL.name:
            self.__wait(self.state["span_time"] * 60,
                        "the overtime deploy to finish")

        self.__wait(self.state["install_time"], "the binaries to be installed")
        self.__wait(self.state["sumo_delay"], "the sumo logs to be populated")

        self.postdeploy_activity.exec(
                self.mac_lists_generator(self.state, predeploy=False),
                self._exec_macs)

        self.state["finished"] = True
        self.state.save()

    def _generate_state_path(self, suffix):
        dtstr = datetime.now(tz=timezone.utc).strftime("%y%m%d%H%M")
        path = Path(f"\
state-file-{self.args.deploy_type}-deploy-{dtstr}{suffix}.json")

        return path

    def _load_state(self):
        self.state = PersistentState(self.args.state_file,
                                     path_generator=self._generate_state_path)

        self._args_populate_state(self.state)
        self.state.save()  # Test if we have the write permissions

    def _args_populate_state(self, state: PersistentState):
        args = self.args
        args_state = {
                "deploy_type": args.deploy_type.name,
                "span_time": args.span_time,
                "device_registry": self._args_load_device_registry(),
                "batch_size": args.batch_size,
                "start_time": args.start_time,
                "safety_time_buffer": args.safety_time_buffer,
                "install_time": args.install_time,
                "sumo_delay": args.sumo_delay,
                "finished": False,
                "dry_run": args.dry_run,
                }

        for key, value in args_state.items():
            if key not in state:
                state[key] = value

        if len(self.state["device_registry"]) <= 0:
            logger.critical("device registry is empty")

        if self.state["deploy_type"] == DeployType.FULL.name:
            if not isinstance(self.state["span_time"], int):
                logger.critical("--span-time is required for FULL deployment")
        elif self.state["deploy_type"] == DeployType.PTG.name:
            if self.state["span_time"] is not None:
                logger.warning("--span-time is not applicable for PTG deploy")
        else:
            raise NotImplementedError("No args validation for the deploy type")

    def _args_load_device_registry(self):
        try:
            return {
                    DeployType.FULL: targeting.load_dg_device_registry,
                    DeployType.PTG: targeting.load_csv,
                    }[self.args.deploy_type](self.args.device_registry)
        except OSError:
            logger.exception("failed to open device registry")
        except targeting.ParseError:
            logger.exception("invalid device registry format")

        logger.critical("failed to load device registry file")

        return None

    def _exec_macs(self, macs: List[str], suffix: str,
                   remote_exec: executor.RemoteExecutor):
        self.macs = macs

        return self._exec(remote_exec, output_suffix=suffix)

    def __wait(self, rel_ts: float, reason: str):
        """Wait until `rel_ts` seconds after the deploy start time."""
        self.__wait_offset += rel_ts
        delay = self.state["start_time"] - time.time() + self.__wait_offset

        if delay > 0:
            logger.info(f"waiting {delay:.2f}s for {reason}")
            time.sleep(delay)
            logger.info("done waiting")
        else:
            logger.warning(f"NOT waiting for {reason}, was {delay:.2f}s ago")

        self.state.save()

    def __mk_fetch_sumo_st(self, template_name):
        return lambda: self.dr_targeting.fetch_sumo(template_name,
                                                    (self.state["start_time"],
                                                     time.time()))
