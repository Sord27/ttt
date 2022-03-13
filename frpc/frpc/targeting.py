
"""Module containing algorithms for MAC list generation."""

import logging
import configparser
import csv
import time
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, List, NamedTuple, Tuple

import boto3
from requests import RequestException
from sumologic import SumoLogic

from .interface import InterfaceFactory
from . import compute
from . import template


MAC_FIELDNAMES = ["mac", "macs"]
SUMO_DEFAULT_CONFIG = ".sumo_config.ini"

S3_BUCKET_NAMES = {
    "circle1": "sc-corp-circle-vpc",
    "circle2": "sc-corp-circle-vpc",
    "dev21": "siq-dev-dev-vpc",
    "dev22": "siq-dev-dev-vpc",
    "dev23": "siq-dev-dev-vpc",
    "dev24": "siq-dev-dev-vpc",
    "ops21": "siq-dev-ops-vpc",
    "prod": "zepp-prod-vpc",
    "qa21": "siq-dev-qa-vpc",
    "qa22": "siq-dev-qa-vpc",
    "qa23": "siq-dev-qa-vpc",
    "stage": "sc-corp-stage-vpc",
    "test": "sc-corp-test-vpc",
}

logger = logging.getLogger(__name__)


def select_mac_fieldname(fieldnames):
    """Select a mac fieldname from a list of Sumo query field names.

    Selects a fieldname from `fieldnames` that is also in `MAC_FIELDNAMES`.
    """
    fieldnames = list(fieldnames)

    for fieldname in MAC_FIELDNAMES:
        try:
            index = [key.lower() for key in fieldnames] \
                    .index(fieldname)

            return fieldnames[index]
        except ValueError:
            continue

    return None


class TargetingError(Exception):
    """Generic targeting error."""


class SumoConfigError(TargetingError):
    """Sumo config failure."""


class MissingDeviceRegistryError(TargetingError):
    """Failure finding latest device registry."""


class SumoConfig(NamedTuple):
    """Sumo config data container."""

    access_id: str
    access_key: str


def sumo_read_config(path: str = SUMO_DEFAULT_CONFIG) -> SumoConfig:
    """Read local sumo config."""
    try:
        parser = configparser.ConfigParser()
        parser.read(path)
        config_args = [
                parser.get("sumo_credentials", field)
                for field in SumoConfig._fields
                ]

        return SumoConfig(*config_args)
    except configparser.Error as err:
        raise SumoConfigError(str(err)) from err


def parse_bool(string: str):
    """Convert a string into a boolean."""
    string = string.lower()

    if string == "true":
        return True

    if string == "false":
        return False

    raise ValueError(f"invalid boolean `{string}`")


class SumoWrapper:
    """Wrapper for fetching MACs from SumoLogic queries."""

    session: SumoLogic

    STATE_GATHERING_RESULTS = "GATHERING RESULTS"
    LIMIT_RPM = 240 / 2  # actual is 240, but I don't want to go that far

    SUMOQL_LIST = None

    def __init__(self, config: SumoConfig = None):
        """Class constructor.

        Arguments:
            config: credentials, pulled from `SUMO_DEFAULT_CONFIG` if None.

        Throws:
            SumoConfigError: config error.
        """
        if config is None:
            config = sumo_read_config()

        self.session = SumoLogic(config.access_id, config.access_key)
        self.__last_mono = time.monotonic() - 60

    def add_job(self, query: str, time_offset: float, end_time: float = None):
        """Queue a sumo query job.

        Arguments:
            query: Sumo query body.
            time_offset: if `end_time` is set, this is a UNIX timestamp,
                         positive time offset in seconds otherwise
            end_time: UNIX timestamp for the end of the query time range.
        """
        time_offset = int(time_offset * 1000)

        if end_time is None:
            end_time = int(time.time() * 1000)
            start_time = end_time - time_offset
        else:
            start_time = time_offset
            end_time = int(end_time * 1000)

        if start_time >= end_time:
            raise ValueError("invalid time range")

        try:
            return self.session.search_job(query, start_time, end_time)
        except RequestException as err:
            raise TargetingError("sumo request failed") from err

    def wait_job(self, job):
        """Wait for a SumoLogic job."""
        wait_secs = 1
        max_wait_secs = 32
        state = self.STATE_GATHERING_RESULTS

        while state == self.STATE_GATHERING_RESULTS:
            time.sleep(wait_secs)

            try:
                status = self.session.search_job_status(job)
                state = status["state"]

                logger.debug(f"sumo query job {job} state = `{state}`")

                if wait_secs == max_wait_secs:
                    logger.info(f"sumo query running, state = {state}")
            except RequestException:
                logger.exception("query state update failed")

            wait_secs = min(wait_secs * 2, max_wait_secs)

        job["__status"] = status

    def get_job_results(self, job, pull_messages: bool = None):
        """Retrieve Sumo query results.

        Arguments:
            job: job dictionary returned by `add_job()`.
            pull_messages: if `False` pull only records,
                           if `True` pull messages as well,
                           if `None` let the function decide.
        """
        # pylint: disable=line-too-long
        # According to https://help.sumologic.com/APIs/Search-Job-API/About-the-Search-Job-API#paging-through-the-records-found-by-a-search-job # noqa: E501
        # The `records` and `messages` endpoint returns only 10k items at time.
        # Since `SumoLogic` is a dumb wrapper around SumoLogic HTTP endpoints
        # we have to take care of this on our side.

        message_count = job["__status"]["messageCount"]
        record_count = job["__status"]["recordCount"]
        records = self.__pull(job, False, record_count)

        logger.debug(f"query message_count = {message_count}, \
record_count = {record_count}")

        if pull_messages is True:
            messages = self.__pull(job, True, message_count)

            return messages, records

        if pull_messages is False:
            return [], records

        if record_count > 0:
            return records

        return self.__pull(job, True, message_count)

    def fetch_query(self, *args, pull_messages: bool = None, **kwargs):
        """Create a sumo query job and retrieve the results.

        Arguments:
            See `get_job_results()` and `add_job()`.
        """
        job = self.add_job(*args, **kwargs)
        self.wait_job(job)

        return self.get_job_results(job, pull_messages=pull_messages)

    def fetch_macs(self, *args, **kwargs) -> List[str]:
        """Create a sumo query job and retrieve the results.

        The query must either parse or aggregate data into one of the
        field names in `MAC_FIELDNAMES`.

        Arguments:
            See `get_job_results()` and `add_job()`.
        """
        results = self.fetch_query(*args, pull_messages=False, **kwargs)
        results = results[1]

        if not results:
            return []

        key = select_mac_fieldname(results[0].keys())

        if key is None:
            raise TargetingError("No valid mac fieldnames in query result")

        return fix_macs(map(lambda result: result[key], results))

    def fetch_macs_template(self, template_name: str,
                            *args, **kwargs) -> List[str]:
        """Create a sumo job from a template sumoql and retrieve the results.

        The query must either parse or aggregate data into one of the
        field names in `MAC_FIELDNAMES`.

        Arguments:
            template_name: sumoql filename in the `templates` folder.

            See `get_job_results()` and `add_job()` for more.
        """
        query = template.load_template(self.get_sumoql_path(template_name))

        return self.fetch_macs(query, *args, **kwargs)

    def __limit_rate(self):
        # According to SumoLogic API we have the following rate limits:
        #   - 240 requests per minute
        #   - 10 concurrent API requests
        #   - 200 active search jobs within the organizaiton

        mono = time.monotonic()
        diff = mono - self.__last_mono
        period = 60 / self.LIMIT_RPM

        if period > diff:
            delay = period - diff

            logger.debug(f"delay request for {delay:.3f}s")
            time.sleep(delay)

        self.__last_mono = mono

    def __pull(self, job, messages: bool, length, limit=10000):
        # tweak this function to run several requests in parallel

        if length <= 0:
            return []

        func, response_key = [
                (self.session.search_job_records, "records"),
                (self.session.search_job_messages, "messages"),
                ][int(messages)]

        self.__limit_rate()
        response = func(job, limit=limit)
        field_convertors = self.__mk_field_convertors(response)
        results = []

        def process(response):
            try:
                results.extend([
                        {key: field_convertors[key](value)
                            for key, value in item["map"].items()}
                        for item in response[response_key]
                        ])

                return len(response[response_key])
            except KeyError as err:
                raise TargetingError(f"Unexpected {response_key} format") \
                        from err

        offset = process(response)

        while offset < length:
            response = func(job, limit=limit, offset=offset)
            offset += process(response)

        return results

    @staticmethod
    def __mk_field_convertors(response):
        type_convertors = {
                "int": int,
                "long": int,
                "string": str,
                "double": float,
                "boolean": parse_bool,
                }

        field_convertors = {}

        try:
            for field in response["fields"]:
                field_type = field["fieldType"]

                if field_type not in type_convertors:
                    raise TargetingError(f"Unknown field type `{field_type}`")

                field_convertors[field["name"]] = type_convertors[field_type]
        except KeyError as err:
            raise TargetingError("Invalid `fields` format") from err

        return field_convertors

    @staticmethod
    def get_sumoql_path(name: str = "") -> str:
        """Get a path for embedded sumoql file."""
        return os.path.join("sumoql", name)

    @classmethod
    def get_sumoql_list(cls) -> List[str]:
        """Get a list of embedded sumoql files."""
        return cls.SUMOQL_LIST


SumoWrapper.SUMOQL_LIST = template.list_templates(
        SumoWrapper.get_sumoql_path())


def device_registry_select(device_registry: List[str], macs: List[str]):
    """Select a list of macs common between `device_registry` and `macs`."""
    return list(set(device_registry) & set(macs))


class DeviceRegistryTargeting:
    """Implementations for selecting device lists from sumo and boson."""

    def __init__(self, device_registry: List[str],
                 sumo_config: SumoConfig = None,
                 boson_factory: InterfaceFactory = None):
        """Construct a targeting class.

        Arguments:
            device_registry: a list of MACs. Output from every funtion of
                             this class will be filtered to macs in this list.
            sumo_config: SumoConfig to use when creating `SumoWrapper`.
                         Leave as `None` if you want `SumoWrapper` to load
                         out local config file.
            boson_factory: `BosonInterface` factory. Used to fetch the list
                           of pumps w/o boson connection. This argument is
                           required if you want `self.fetch_no_boson()`
                           to work properly.
        """
        self.device_registry = device_registry
        self.time_range = (86400, None)
        self._sumo = SumoWrapper(config=sumo_config)
        self.boson_factory = boson_factory

    def select(self, macs: List[str]) -> List[str]:
        """Select common macs in `self.device_registry` and `macs`."""
        return device_registry_select(self.device_registry, macs)

    def fetch_sumo(self, template_name: str,
                   time_range: Tuple[float, float] = None) -> List[str]:
        """Select macs from sumo query common with device registry.

        Arguments:
            template_name: template name containing sumo query.
            time_range: override default class time_range.
        """
        if time_range is None:
            time_range = self.time_range

        logger.info(f"fetching macs for `{template_name}` @ {time_range}")

        macs = self._sumo.fetch_macs_template(template_name,
                                              time_range[0],
                                              end_time=time_range[1])

        qlen = len(macs)
        macs = self.select(macs)
        perc = compute.perc(len(macs), len(self.device_registry))

        logger.info(f"`{template_name}` returned {qlen} \
MACs, out of which {len(macs)} ({perc:.2f}%) are in device registry")

        return macs

    def fetch_no_boson(self) -> List[str]:
        """Select macs w/o boson connection common with device registry."""
        if self.boson_factory is None:
            raise RuntimeError("`boson_factory` is None")

        logger.info("fetching macs connected to boson")

        with self.boson_factory(self.device_registry) as interface:
            online_macs = interface.get_online()

        macs = list(set(self.device_registry) - set(online_macs))
        current = len(macs)
        perc = compute.perc(current, len(self.device_registry))

        logger.info(f"{current} ({perc:.2f}%) devices w/o boson connection")

        return macs


class ParseError(Exception):
    """General parsing error."""


class CsvFieldnameError(ParseError):
    """No valid fieldname in csv."""

    def __init__(self, filename, fieldnames):
        """Error constructor.

        Note that the arguments differ from standard `Exception` constructor.
        """
        self.fieldnames = ", ".join(MAC_FIELDNAMES)

        super().__init__(f"no valid fieldnames found in {filename}, \
expected one of {self.fieldnames}; got {', '.join(fieldnames)}")


def fix_mac(mac: str):
    """Convert MAC string to default format.

    Throws:
        ParseError: one of the macs has invalid format.
    """
    mac_length = 12

    if len(mac) != mac_length:
        raise ParseError(f"mac `{mac}` length has to be {mac_length}")

    try:
        int(mac, 16)
    except ValueError as err:
        raise ParseError(f"mac `{mac}` has invalid format") from err

    return mac.lower()


def fix_macs(iterable: Iterable[str]):
    """Fix duplicate macs in an iterable of strings.

    Throws:
        ParseError: one of the macs has invalid format.
    """
    macs = set()

    for mac in iterable:
        macs.add(fix_mac(mac))

    return list(macs)


def generate_s3_bucket_prefix(environment: str) -> str:
    """Generate s3 bucket prefix for latest device registry file.

    Arguments:
        environment: environment name.

    Throws:
        KeyError: no device registry file location for selected env.
    """
    if environment not in S3_BUCKET_NAMES:
        raise KeyError(f"There is no device registry file \
location defined for {environment} environment yet")

    now = datetime.now(tz=timezone.utc) - timedelta(seconds=15)
    return f"{environment}/device-registry/\
DR_{now.month:02d}-{now.day:02d}-{now.year}-{now.hour:02d}:"


def get_s3_bucket_name(environment: str) -> str:
    """Get a name of s3 bucket that contains device registry file.

    Arguments:
        environment: environment name.

    Throws:
        KeyError: no s3 bucket name for selected env.
    """
    name = S3_BUCKET_NAMES.get(environment)
    if name is None:
        raise KeyError(f"There is no s3 bucket name \
defined for {environment} environment yet")
    return name


def load_dg_device_registry(path: Path) -> List[str]:
    """Load a list of devices from a device registry file.

    Throws:
        OSError: if there was an error opening the file.
        ParseError: if there was unexpected parsing error.
    """
    with path.open() as dr_file:
        line = dr_file.readline()

        if not line.startswith("macAddress"):
            raise ParseError("expected first line to contain a header")

        return fix_macs(line.lstrip().split()[0] for line in dr_file)


def load_latest_device_registry(env: str) -> List[str]:
    """Load a list of devices from an S3 device registry.

    Arguments:
        env: environment name.

    Throws:
        MissingDeviceRegistryError: if there is no DR file for the past hour.
        botocore.exceptions.ClientError: if there was an error retrieving file
                                         from S3.
    """
    s3_client = boto3.client("s3")

    bucket = get_s3_bucket_name(env)
    prefix = generate_s3_bucket_prefix(env)

    file_list = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in file_list:
        raise MissingDeviceRegistryError(f"No recent device registry file for \
{env} in s3://{bucket}/prefix")

    latest = max(file_list["Contents"], key=lambda x: x["LastModified"])

    logger.info(f"Using {latest['Key']} device registry")

    with tempfile.NamedTemporaryFile(mode="w+b", buffering=0) as tmp_fp:
        s3_client.download_fileobj(bucket, latest["Key"], tmp_fp)
        device_registry = load_dg_device_registry(Path(tmp_fp.name))

    return device_registry


def load_csv(path: Path) -> List[str]:
    """Load a list of devices from a CSV file.

    The file may be produces by SUMO or created manually.

    Throws:
        OSError: there was an error opening the file.
        ParseError: there was an unexpected parsing error.
        CsvFieldnameError: no valid fieldnames found in the csv file.
    """
    with path.open(mode="r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        key = select_mac_fieldname(reader.fieldnames)

        if key is None:
            raise CsvFieldnameError(path, reader.fieldnames)

        return fix_macs(map(lambda row: row[key], reader))
