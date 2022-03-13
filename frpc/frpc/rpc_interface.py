
"""Module for the rpc interface class."""

import json
import logging
from os import path
from pathlib import Path
import threading
from typing import List, NamedTuple
import requests

try:
    from simplejson import JSONDecodeError
except ImportError:
    from json import JSONDecodeError

from .command import CommandBuffer, CommandType
from . import interface


logger = logging.getLogger(__name__)


OPS_CREDS_FILENAME = ".ops_creds.json"
OPS_ENDPOINTS = {
        "circle1": "https://circle1-admin-svc.circle.siq.sleepnumber.com/",
        "circle2": "https://circle2-admin-svc.circle.siq.sleepnumber.com/",
        "dev21": "https://dev21-admin-svc.dev.siq.sleepnumber.com/",
        "dev22": "https://dev22-admin-svc.dev.siq.sleepnumber.com/",
        "dev23": "https://dev23-admin-svc.dev.siq.sleepnumber.com/",
        "dev24": "https://dev24-admin-svc.dev.siq.sleepnumber.com/",
        "ops21": "https://ops21-admin-svc.dev.siq.sleepnumber.com/",
        "prod": "https://prod-admin-svc.sleepiq.sleepnumber.com/",
        "qa21": "https://qa21-admin-svc.dev.siq.sleepnumber.com/",
        "qa22": "https://qa22-admin-svc.dev.siq.sleepnumber.com/",
        "qa23": "https://qa23-admin-svc.dev.siq.sleepnumber.com/",
        "stage": "https://stage-admin-svc.stage.siq.sleepnumber.com/",
        "test": "https://test-admin-svc.test.siq.sleepnumber.com/",
        }

ENVIRONMENTS = OPS_ENDPOINTS.keys()


class OPSCredentials(NamedTuple):
    """Container for OPS portal credentials."""

    env: str
    login: str
    password: str


def _load_creds_file(filename: str, env: str) -> OPSCredentials:
    with open(filename) as fileobj:
        doc = json.load(fileobj)

        if not isinstance(doc, list):
            raise ValueError("credentials file is not an array of objects")

        try:
            for entry in doc:
                if entry["env"] != env:
                    continue

                if isinstance(entry["login"], str) and \
                        isinstance(entry["password"], str):
                    return OPSCredentials(env=entry["env"],
                                          login=entry["login"],
                                          password=entry["password"])

                raise ValueError("invalid file format")
        except KeyError as err:
            raise ValueError("invalid file format") from err

        raise ValueError(f"no creds for environment `{env}`")


def load_creds_file(env: str, filename: str = None):
    """Load OPS credentials from a file.

    Arguments:
        env: environment to use.
        filename: json file to load credentials from.

    Throws:
        OSError: no such file.
        ValueError: invalid file contents.
    """
    if filename is None:
        if path.exists(OPS_CREDS_FILENAME):
            filepath = OPS_CREDS_FILENAME
        elif path.exists(Path.home() / OPS_CREDS_FILENAME):
            filepath = Path.home() / OPS_CREDS_FILENAME
        else:
            raise OSError("no credentials file found")
    else:
        filepath = filename

    return _load_creds_file(filepath, env)


def _redact_dict(target, level=10):
    if level <= 0:
        raise ValueError("target is nested too deeply")

    target_copy = None

    for key, value in target.items():
        if key.lower() in ("password", "access_token") and \
                isinstance(value, str):
            if target_copy is None:
                target_copy = dict(target)

            target_copy[key] = "[REDACTED]"
        elif isinstance(value, dict):
            new_value = _redact_dict(value, level=(level - 1))

            if new_value is not value:
                if target_copy is None:
                    target_copy = dict(target)

                target_copy[key] = new_value

    if target_copy is None:
        return target

    return target_copy


class RPCInterface(interface.Interface):
    """OPS RPC interface implementation."""

    __cache: dict = {}  # using `NamedTuple.__hash__()` as hash
    __cache_cv = threading.Condition()

    def __init__(self, macs: List[str], ops_creds: OPSCredentials,
                 *args, **kwargs):
        """RPC interface constructor.

        Arguments:
            macs: pump MACs to connect to.
            ops_creds: credentials for the OPS portal.
        """
        super().__init__(macs, *args, **kwargs)

        self.__creds = ops_creds
        self.__access_token = None
        self.__session = requests.Session()

    def open(self):
        """Get access token for further OPS requests."""
        with self.__cache_cv:
            # producer is already up
            if self.__creds in self.__cache:
                self.__cache_cv.wait_for(
                        lambda: self.__creds in self.__cache and
                        self.__cache[self.__creds] is not None)

                if self.__creds in self.__cache:
                    logger.debug(f"got cached access token for \
{self.__creds.login}")

                    self.__access_token = self.__cache[self.__creds]
                else:
                    logger.debug("producer thread failed, becoming one")

                    self.__cache[self.__creds] = None
            else:
                logger.debug("we are the first thread, becoming a producer")

                self.__cache[self.__creds] = None

        if self.__cache[self.__creds] is None:
            # we are the producer
            request_body = {
                    "login": self.__creds.login,
                    "password": self.__creds.password,
                    }

            logger.debug(f"\
attempting to authenticate as {self.__creds.login} @ {self.__creds.env}")

            try:
                response = self.__put("authenticate",
                                      params={"details": True},
                                      json=request_body)

                self.__access_token = response["access_token"]

                logger.info(f"authenticated as {self.__creds.login}")

                with self.__cache_cv:
                    self.__cache[self.__creds] = self.__access_token
                    self.__cache_cv.notify_all()
            except (requests.RequestException, KeyError) as err:
                logger.error(f"network failure has occured: {err}")

                with self.__cache_cv:
                    del self.__cache[self.__creds]
                    self.__cache_cv.notify()

                raise interface.FatalInterfaceError("network failure") from err

        self.is_open = True

    def execute(self, command_buffer: CommandBuffer) \
            -> List[interface.ExecutionResult]:
        """Execute the list of commands stored in the command_buffer."""
        if not self.is_open:
            raise RuntimeError("An interface should be opened before \
executing anything")

        commands = command_buffer.flush()
        results = []

        for mac in self.macs:
            for command_type, *command_args in commands:
                if command_type is CommandType.EXEC:
                    try:
                        self.__send_rpc(mac, command_args[0])

                        success = True
                    except requests.RequestException:
                        logger.exception("rpc request failed")

                        success = False

                    result = interface.ExecutionResult(
                            mac=mac, returncode=None, success=success,
                            stdout=None, stderr=None)

                    results.append(result)

            self._progress(1)

        return results

    def __mkresturl(self, endpoint: str):
        return f"{OPS_ENDPOINTS[self.__creds.env]}bam/rest/sn/v1/{endpoint}"

    def __request(self, func, endpoint: str, **kwargs):
        url = self.__mkresturl(endpoint)

        logger.debug(f"\
{func} request to {url}, kwargs = {_redact_dict(kwargs)}")

        response = func(url, **kwargs)

        try:
            response_json = response.json()

            logger.debug(f"reponse code = `{response.status_code}`, \
response json = `{_redact_dict(response_json)}`")
        except JSONDecodeError as err:
            logger.debug(f"reponse code = `{response.status_code}`, \
response text = `{response.text}`")

            raise err

        response.raise_for_status()

        return response_json

    def __put(self, endpoint: str, **kwargs):
        return self.__request(self.__session.put, endpoint, **kwargs)

    def __post(self, endpoint: str, **kwargs):
        return self.__request(self.__session.post, endpoint, **kwargs)

    def __send_rpc(self, mac, command):
        request_body = {
                "macAddress": mac,
                "unixCommand": command,
                }

        return self.__post("deviceRPC",
                           params={"access_token": self.__access_token},
                           json=request_body)


class RPCInterfaceFactory(interface.InterfaceFactory):
    """RPC interface factory."""

    interface_cls = RPCInterface
