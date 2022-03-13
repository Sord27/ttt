#! /usr/bin/env python3
""" SleepIQ Account generation, creation, and deletion using python """
import argparse
import datetime
import json
import random
import re
import string
import time
import typing

import faker
import requests
import yaml

import back_office

# Default Files
CONFIG_FILE = "config.yaml"
ACCOUNT_FILE = "account.json"
BAM_INIT_CONF = "bam-init.conf"
BAM_CONF = "bam.conf"

# Constants
SERVER_URLS = {
    "alpha": "https://alpha-admin-svc.bamlabs.com/",
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
DEFAULT_ENV = "circle1"
GENERATIONS = ("360", "legacy")
PROTECTED_ACCOUNTS = ("Backoffice", "ZeppBackoffice")
LATEST = "[latest]"
DEVICE_MODE = {
    "normal": None,
    "test": 2,
    "config": 4,
    "disabled": 8,
    "needs_calibration": 16,
    "force_back_in_bed": 32
}

FAKE = faker.Faker("en_US")  # Single instance of faker for entire application


def random_foundation(generation: str,
                      reference: str = "35632230815",
                      purchase_date: datetime.datetime = None,
                      zipcode: str = None) -> typing.Dict:
    """ Generate a foundation component
    :param generation: Generation of products.
    :param reference: Parent order reference number for generating other order
        items from
    :param purchase_date: Purchase date to associate with foundation order.
        Defaults to current date if not provided.
    :param zipcode: Zipcode to associate with foundation order. Defaults to a
        random zipcode if not provided.
    :return: Dictionary containing generated foundation information
    """
    if generation not in GENERATIONS:
        raise ValueError("generation must be in {}".format(GENERATIONS))
    if not purchase_date:
        purchase_date = datetime.datetime.now()
    if not zipcode:
        zipcode = FAKE.zipcode()
    # TODO: Actually Generate a random foundation
    foundation = {
        "type": "1",
        "base": "ADJUSTABLE",
        "bedsize": "KING",
        "chamber": "1",
        "code": "P5",
        "kidsbed": False,
        "purchaseDate": purchase_date.strftime("%Y-%m-%d"),
        "reference": "{reference}-1-AID".format(reference=reference),
        "parentBedComponent":
        "{reference}-1-AID-P".format(reference=reference),
        "serial": "",
        "sku": "KAP5",
        "version": "3",
        "zipcode": zipcode,
        "generation": generation
    }
    return foundation


def random_mac(generation: str) -> str:
    """ Generate a random, valid MAC address for a Sleep Number Smart Pump

    The top nibble of the 4th most significant bit is set to `F`, which should
    be an indication that the device is a using a Fake MAC address. This will
    generate a MAC address using the Sleep Number owned MAC Address ranges.

    Example output:

      - 360: 64:db:a0:fX:XX:XX
      - legacy: cc:04:b4:fX:XX:XX

    :param generation: generation of pump to generate for.
        Valid options: '360', 'legacy'
    :return: string of mac address, with the 4 MSB set to 'f' to indicate a
        fake pump
    :raises ValueError: `generation` isn't in the list of `GENERATIONS`
        supported
    :raises NotImplementedError: `generation` is in `GENERATIONS`, but support
        not added to `random_mac()`"""
    fake_suffix = FAKE.mac_address()[10:]
    if generation not in GENERATIONS:
        raise ValueError("generation must be in {}".format(GENERATIONS))
    if generation == "360":
        return "64:db:a0:f" + fake_suffix
    if generation == "legacy":
        return "cc:04:b4:f" + fake_suffix
    raise NotImplementedError("Support hasn't been added yet")


def normalize_mac_address(mac_address: str) -> str:
    """ Normalize a MAC Address
    :param mac_address: MAC address to normalize
    :return: A mac address with no colons or lowercase letters"""
    return mac_address.replace(":", "").upper()


def valid_mac(mac_address: str) -> bool:
    """ Check if a MAC address is valid.

    Valid MAC addresses can be in the following forms:
    64dba0022952
    64:db:a0:02:29:52
    64-db-a0-02-29-52

    MAC addresses are not case sensitive.

    :param mac_address: MAC address to check"""
    mac_address = mac_address.lower()
    if re.match(r"[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\1[0-9a-f]{2}){4}$",
                mac_address):
        return True
    return False


def random_pump(generation: str,
                reference: str = "35632230815",
                purchase_date: datetime.datetime = None,
                zipcode: str = None) -> typing.Dict:
    """ Generate a pump component
    :param generation: Generation of product.
    :param reference: Parent order reference number for generating other order
        items from
    :param purchase_date: Purchase date to associate with pump order. Defaults
        to current date if not provided.
    :param zipcode: Zipcode to associate with pump order. Defaults to a random
        zipcode if not provided.
    :return: Dictionary containing generated pump information """
    # TODO: Actually Generate a random pump
    if generation not in GENERATIONS:
        raise ValueError("generation must be in {}".format(GENERATIONS))
    if not purchase_date:
        purchase_date = datetime.datetime.now()
    if not zipcode:
        zipcode = FAKE.zipcode()
    pump = {
        "status": "INSTALLED",
        "type": "2",
        "base": None,
        "bedsize": None,
        "chamber": "0",
        "code": "Firmness Control, SleepIQ, Dual, Boxed",
        "kidsbed": False,
        "purchaseDate": purchase_date.strftime("%Y-%m-%d"),
        "reference": "{ref}-2-AID".format(ref=reference),
        "parentBedComponent": "{ref}-1-AID-P".format(ref=reference),
        "serial": "",
        "sku": "122613",
        "version": "",
        "zipcode": zipcode,
        "generation": generation
    }
    return pump


def random_address(street1: str = None,
                   street2: str = None,
                   city: str = None,
                   state: str = None,
                   country: str = None,
                   zipcode: str = None,
                   phone_number: str = None) -> dict:
    """ Generate random, valid address information for account creation
    :param street1: Number and Street for address.
    :param street2: Additional unit, suite, or department information. Random
        data is not generated for this field.
    :param city: City
    :param state: State. Must be the two letter abbreviation
    :param country: Country of address. Defaults to 'USA'
    :param zipcode: Zipcode. Generates a valid zipcode located in the defined
        state
    :param phone_number: Phone number for the account. Must only contain digits.
        Generates a random 11 digit number with a preceding 1 for the US
        country code.
    :return: A dictionary for input into the random_user function"""
    if not street1:
        street1 = FAKE.street_address()
    if not street2:
        street2 = ""
    if not city:
        city = FAKE.city()
    if not state:
        state = FAKE.state_abbr()
    if not country:
        country = "USA"
    if not zipcode:
        zipcode = FAKE.zipcode_in_state(state)
    if not phone_number:
        phone_number = str(random.randint(10000000000, 19999999999))
    address = {
        "street1": street1,
        "street2": street2,
        "city": city,
        "state": state,
        "country": country,
        "zipcode": zipcode,
        "phoneNumber": phone_number
    }
    return address


def check_address(address: typing.Dict) -> typing.Tuple[bool, str]:
    """ Check for a valid address dictionary
    :param address: Address to check:
    :return: True if valid, False if not
    """
    address_fields = {
        "street1", "street2", "city", "state", "country", "zipcode",
        "phoneNumber"
    }
    missing_keys = address_fields.difference(set(address))
    extra_keys = set(address).difference(address_fields)
    if not isinstance(address, dict):
        return False, "address must be a dict"
    if missing_keys:
        return False, "address does not contain all fields. Missing fields: {}".format(
            missing_keys)
    if extra_keys:
        return False, "address contains extra fields. Extra fields: {}".format(
            extra_keys)
    if not set(address) & address_fields:
        return False, "address must contain specific fields: [{}]".format(
            ", ".join(address_fields))
    return True, "Valid"


def random_user(name: typing.List[str] = None,
                gender: str = None,
                birth_year: str = None,
                email: str = None,
                email_domain: str = "example.com",
                address: typing.Dict = None,
                reference: str = "auto_generated",
                timezone: str = None) -> typing.Dict:
    """ Generate random user account information
    :param name: A list of two strings. [0] = First Name , [1] = Last Name.
        Will generate a random, gendered first and last name if this isn't
        provided.
    :param gender: Gender of the user. Used to generate first name. Randomly
        generated if not provided. Must be "M" or "F".
    :param birth_year: Birth year of the sleeper. Randomly generates a year 18
        to 100 years ago if not provided
    :param email: The email to associate with the generated account. If this
        isn't provided, an email will be generated based off of the first and
        last name.
    :param email_domain: The domain to generate the email with. If this isn't
        specified, the default is set to the safe `example.com` domain
    :param address: Dictionary containing address information. Randomly
        generates an address if not provided
    :param reference: Reference identifier for account. Defaults to
        "auto_generated" if not provided.
    :param timezone: Timezone of account. Must be in standard timezone format.
        "US/Pacific", "US/Eastern", etc. Randomly generates a common US timezone
        if a timezone is not provided
    :return: A dictionary with all of the information necessary to create a
        SleepIQ account
    """
    fields: typing.Dict[str, typing.Any] = {}
    # Gender Generation
    genders = ("M", "F")
    if not gender or gender not in genders:
        gender = random.choice(genders)
    fields["gender"] = gender

    # Name Generation
    if name is None:
        if gender == "M":
            first_name = FAKE.first_name_male()
        else:
            first_name = FAKE.first_name_female()
        last_name = FAKE.last_name()
    elif not isinstance(name, list) or len(name) != 2 or isinstance(
            name[0], str) or isinstance(name[1], str):
        raise TypeError("name must be a list of 2 strings")
    else:
        first_name, last_name = name
    fields["firstName"] = first_name.title()
    fields["lastName"] = last_name.title()

    # Birth Year Generation
    if not birth_year:
        birth_year = FAKE.date_time_between(start_date="-100y",
                                            end_date="-18y",
                                            tzinfo=None).strftime("%Y")
    elif not isinstance(
            birth_year,
            str) or len(birth_year) != 4 or not birth_year.isdigit():
        raise TypeError("birth_year must be a 4 digit, year string")
    fields["birthYear"] = birth_year

    # Email Generation
    if not email:
        email = "{}.{}@{}".format(first_name.lower().replace(" ", "_"),
                                  last_name.lower().replace(" ", "_"),
                                  email_domain)
    elif not isinstance(email, str):
        raise TypeError("email must be a string")
    fields["login"] = email

    # Address Generation
    if not address:
        address = random_address()
    valid, reason = check_address(address)
    if not valid:
        raise ValueError(reason)
    fields["address"] = address

    # Timezone Generation
    usa_timezones = [
        "US/Alaska",
        "US/Arizona",
        "US/Central",
        "US/Eastern",
        "US/Hawaii",
        "US/Michigan",
        "US/Mountain",
        "US/Pacific",
    ]
    if not timezone:
        timezone = random.choice(usa_timezones)
    elif not isinstance(timezone, str):
        raise TypeError("timezone must be a string")
    fields["timezone"] = timezone
    fields["reference"] = "{ref}{random:04}".format(ref=reference,
                                                    random=random.randint(
                                                        0, 9999))
    return fields


def random_fields(args: argparse.Namespace) -> typing.Dict:
    """ Generate random, valid data for account creation.

    If any invalid parameters are passed, random, valid data will be generated
    instead of using the invalid parameters.

    :param args: Command line arguments
    :return: Dictionary """
    if args.verbose:
        print("Generating user account information")
    user = random_user(name=args.name,
                       email=args.email,
                       email_domain="sleepiqlabs.com")
    if args.verbose > 1:
        print(yaml.dump(user))
    user_zip = user["address"]["zipcode"]
    if args.verbose:
        print("Generating pump information")
    pump = random_pump(generation=args.generation, zipcode=user_zip)
    if args.verbose > 1:
        print(yaml.dump(pump))
    if args.mac and valid_mac(args.mac):
        user["mac_address"] = args.mac
    else:
        if args.verbose:
            print("Generating MAC Address")
        user["mac_address"] = random_mac(generation=args.generation)
    if args.internal_id and valid_mac(args.internal_id):
        user["internal_id"] = args.internal_id
    else:
        if args.verbose:
            print("Generating Internal MAC Address")
        internal_id = FAKE.mac_address()
        user["internal_id"] = normalize_mac_address(internal_id)
    if args.verbose:
        print("Generating foundation information")
    foundation = random_foundation(generation=args.generation,
                                   zipcode=user_zip)
    if args.verbose:
        print("Generating random password")
    user["password"] = generate_password()
    if args.verbose > 1:
        print(yaml.dump(foundation))
    user["components"] = [pump, foundation]
    return user


def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser()
    parser.description = """
    Script to create a SleepIQ account and perform all of the necessary steps to
    get a bed online. This script can also generate a 'bam-init.conf' file that
    can be used to get a real pump online, and a 'bam.conf' which is used by a
    virtualized pump to connect to cloud.
    """
    parser.epilog = """
    For more information on any of the above commands, check their specific
    help responses.
    """
    subparsers = parser.add_subparsers(dest="command")
    # Create a config file
    config = subparsers.add_parser(
        "config",
        help="Create a {} file to hold specific settings.".format(CONFIG_FILE))
    config.description = """
    Generate a configuration file for use with the account creation script.
    Information in this file can be configured directly from the arguments, or
    edited from the empty file.
    """
    config.add_argument(
        "-c",
        "--config",
        help="""Configuration file used to define environment and credentials.
            Defaults to '{}'""".format(CONFIG_FILE),
        type=argparse.FileType("w"),
        default=CONFIG_FILE)
    config.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=0,
                        help="Adjust verbosity")
    config.add_argument(
        "-e",
        "--environment",
        help="SleepIQ cloud environment to create account in. Defaults to '{}'"
        .format(DEFAULT_ENV),
        choices=SERVER_URLS,
        default=DEFAULT_ENV)
    config.add_argument(
        "-r",
        "--reference",
        help="Default Account Reference/Name. Defaults to 'auto_generated'",
        default="auto_generated")
    version = config.add_argument_group("Version")
    version.add_argument(
        "--app",
        help="Bammit Application Version to set for the device. Defaults to '{}'"
        .format(LATEST),
        default=LATEST)
    version.add_argument(
        "--rfs",
        help="Bammit RFS Version to set for the device. Defaults to '{}'".
        format(LATEST),
        default=LATEST)

    backoffice = config.add_argument_group("Backoffice")
    backoffice.add_argument("-u",
                            "--username",
                            help="Username for Backoffice account")
    backoffice.add_argument("-p",
                            "--password",
                            help="Password for Backoffice account")

    wifi = config.add_argument_group("WiFi")
    wifi.add_argument("--ssid", help="WiFi network SSID", metavar="SSID")
    wifi.add_argument("--psk",
                      help="WiFi network Password",
                      metavar="PASSWORD")

    # Generate an account generation configuration parser
    generate = subparsers.add_parser("generate",
                                     help="Generate a configuration file")
    generate.description = """
    Generate a configuration file for use with this script. If any of these
    values are not defined, they are randomly generated.
    """
    generate.add_argument(
        "-c",
        "--config",
        help="""Configuration file used to define environment and credentials.
            Defaults to '{}'""".format(CONFIG_FILE),
        type=argparse.FileType("r"),
        default=CONFIG_FILE)
    generate.add_argument("-v",
                          "--verbose",
                          action="count",
                          default=0,
                          help="Adjust verbosity")

    account = generate.add_argument_group("Account Details")
    account.add_argument("-n",
                         "--name",
                         help="First and Last name of user to create",
                         nargs=2,
                         metavar=("FIRST", "LAST"))
    account.add_argument("-e",
                         "--email",
                         help="Email to use for the generated account.",
                         metavar="XXXXXX@XXXX.XXX")
    account.add_argument("-p",
                         "--password",
                         help="Password to create account with")

    orders = generate.add_argument_group("Order Details")
    orders.add_argument("-m",
                        "--mac",
                        help="MAC Address of Pump to create",
                        metavar="XX:XX:XX:XX:XX:XX")
    orders.add_argument(
        "--internal_id",
        help=
        "MAC Address to use for the Internal ID. Defaults to '00:11:de:ad:be:ef'",
        metavar="XX:XX:XX:XX:XX:XX",
        default="00:11:de:ad:be:ef")
    orders.add_argument("--generation",
                        help="Product Generation. Defaults to '360'",
                        choices=("legacy", "360"),
                        default="360")
    # TODO: Currently not used, but is fully implemented in argument parsing
    # orders.add_argument(
    #     "-f",
    #     "--foundation",
    #     help="Foundation to associate with pump. Defaults to 'None'",
    #     choices=(None, "FF1", "FF2", "FF3"),
    #     default=None)
    # orders.add_argument("--size",
    #                     help="Size of mattress. Defaults to 'King'",
    #                     choices=("Twin", "Full", "Queen", "King", "Split King",
    #                              "Flextop King"),
    #                     default="King")
    # orders.add_argument("--mattress",
    #                     help="Mattress type. Defaults to 'i8'",
    #                     choices=("c2", "c4", "p5", "p6", "i7", "i8", "i10"),
    #                     default='i8')
    # orders.add_argument("--chambers",
    #                     help="Number of chambers. Defaults to '2'",
    #                     choices=(1, 2),
    #                     default=2)

    wifi = generate.add_argument_group("WiFi")
    wifi.add_argument("--ssid", help="WiFi network SSID", metavar="SSID")
    wifi.add_argument("--psk",
                      help="WiFi network Password",
                      metavar="PASSWORD")
    generate.add_argument(
        "-o",
        "--output",
        type=argparse.FileType('w', encoding='UTF-8'),
        help="Output File. Defaults to '{}'".format(ACCOUNT_FILE),
        default=ACCOUNT_FILE)

    # Create account subparser
    create = subparsers.add_parser(
        "create", help="Create an account using pregenerated information")
    create.description = """
    Create an account in the SleepIQ backend to get a pump online with the
    necessary information. This will create all of the necessary objects to get
    a 360 pump online with a sleeper in the bed.
    """
    create.add_argument(
        "-c",
        "--config",
        help="""Configuration file used to define environment and credentials.
            Defaults to '{}'""".format(CONFIG_FILE),
        type=argparse.FileType("r"),
        default=CONFIG_FILE)
    create.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=0,
                        help="Adjust verbosity")
    create.add_argument(
        "-i",
        "--input",
        type=argparse.FileType("r"),
        help="""Account information used to create account in the backend.
        Defaults to '{}'""".format(ACCOUNT_FILE),
        default=ACCOUNT_FILE)
    create.add_argument(
        "--init",
        type=argparse.FileType("w", encoding="UTF-8"),
        help="Where to store bam-init.conf file. Defaults to {}".format(
            BAM_INIT_CONF),
        default=BAM_INIT_CONF,
        metavar="BAM_INIT")
    create.add_argument("-o",
                        "--output",
                        type=argparse.FileType("w", encoding="UTF-8"),
                        help="Output File. Defaults to '{}'".format(BAM_CONF),
                        default=BAM_CONF,
                        metavar="BAM_CONF")

    # Delete account subparser
    delete = subparsers.add_parser("delete", help="Delete an account")
    delete.description = "Delete SleepIQ account using Account ID"
    delete.add_argument(
        "-c",
        "--config",
        help="""Configuration file used to define environment and credentials.
            Defaults to '{}'""".format(CONFIG_FILE),
        type=argparse.FileType("r"),
        default=CONFIG_FILE)
    delete.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=0,
                        help="Adjust verbosity")

    delete.add_argument("account",
                        help="SleepIQ Account ID to delete. Can pass multiple "
                        "IDs to delete more than one ID at a time.",
                        nargs="+",
                        type=int)
    args = parser.parse_args()
    return args


class SleepIQAccount:
    """
    Object that interacts with the SleepIQ backend to manage account information
    """
    def __init__(self,
                 admin_username: str,
                 admin_password: str,
                 environment: str,
                 account_id: str = None,
                 verbosity: typing.SupportsInt = 0,
                 timeout: typing.SupportsInt = 5):
        """ Initialize a class with the credentials needed to log in to and
        create new accounts in a SleepIQ Backoffice Admin server
        :param admin_username: Username used to log in to the Backoffice
            administrator page
        :param admin_password: Password used to log in to the Backoffice
            administrator page
        :param environment: Backoffice environment to log in to
        :param account_id: account_id of the the account to be controlled.
            Defaults to None if not specified
        :param verbosity: Verbosity level of messages. Defaults to 0
        :param timeout: Timeout for requests. Defaults to 5 seconds"""
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.access_token = {"access_token": None, "expiration_timestamp": 0}
        if environment not in SERVER_URLS:
            raise ValueError("Environment not in list of environments")
        self.environment = environment
        self.account_id = account_id
        self.sn_rest_endpoint = "{server}bam/rest/sn/".format(
            server=SERVER_URLS[self.environment])
        if isinstance(verbosity, int) and verbosity >= 0:
            self.verbosity = verbosity
        else:
            self.verbosity = 0
        self.request_headers = {"Content-Type": "application/json"}
        self.timeout = timeout

    def get_access_token(self):
        """Gets existing access token or fetches a new one if the current
        one is expired. The access token is valid for 30 minutes.
        :returns:
            dictionary containing access token:
            ```
            {
                "access_token": "<ACCESS_TOKEN>"
            }
            ```
        """
        if time.time() > self.access_token["expiration_timestamp"]:  # expired
            self.access_token = {
                "access_token": {
                    "access_token": self.authenticate()
                },
                "expiration_timestamp": time.time() + 30 * 60  # 30 minutes
            }
        return self.access_token["access_token"]

    def authenticate(self, app_version=4.3, platform="ios"):
        """Authenticates to server and gets an access token
        :param app_version: Mobile app version
        :param platform: Mobile platform (ios, android)
        :returns: access token as a string
        """
        request_url = "{endpoint}v1/authenticate".format(
            endpoint=self.sn_rest_endpoint)

        params = {"appVersion": app_version, "platform": platform}

        data = {"login": self.admin_username, "password": self.admin_password}

        response = requests.put(request_url,
                                headers=self.request_headers,
                                params=params,
                                json=data)
        response.raise_for_status()

        return response.json()["access_token"]

    def set_account_id(self, account_id: str) -> None:
        """ Set the account ID of the account to be controlled
        :param account_id: Account ID of SleepIQ Account"""
        self.account_id = account_id

    def create_account(self, reference: str, login: str, password: str,
                       firstName: str, lastName: str, timezone: str,
                       address: str, components: str,
                       **kwargs: typing.Dict) -> str:
        """ Create a SleepIQ account in the environment
        :param reference: A unique identifier for use in the system. Defaults
            to an empty string. Maximum length of 30 characters
        :param login: Username of the account. Max length of 255 characters
        :param password: Password to create the account with
        :param firstName: First Name of the account owner. Maximum length of 12
            characters
        :param lastName: Last Name of the account owner. Maximum length of 25
            characters
        :param timezone: Timezone the account is in. Maximum length of 30
        :param address: Address of the account. A dictionary of all of the
            elements of an address
        :param components: List of all components associated with the account.
            This includes beds, pump, foundations, and footwarmers
        :returns: Account ID
        """
        # Input Validation
        if not reference or len(reference) > 30:
            raise ValueError("reference must be 30 characters or less")
        if not login or len(login) > 255:
            raise ValueError("login must be 255 characters or less")
        if not firstName or len(firstName) > 12:
            raise ValueError("firstName must be 12 characters or less")
        if not lastName or len(lastName) > 25:
            raise ValueError("lastName must be 25 characters or less")
        if not timezone or len(timezone) > 30:
            raise ValueError("timezone must be 30 characters or less")
        if not address or not isinstance(address, dict):
            raise TypeError("address must be a dictionary")
        valid_address, reason = check_address(address)
        if not valid_address:
            raise ValueError(reason)
        if not isinstance(components, list):
            raise TypeError("components must be a list")
        if not components:
            raise ValueError("components must not be empty")
        if not valid_password(password):
            raise ValueError("password must be a valid password")

        # Create Account
        account_payload = {
            "reference": reference,
            "login": login,
            "firstName": firstName,
            "lastName": lastName,
            "timezone": timezone,
            "address": address,
            "components": components
        }
        if self.verbosity:
            print("Creating Account")
            if self.verbosity > 1:
                print(yaml.dump(account_payload))
        request_url = "{endpoint}v1/account/".format(
            endpoint=self.sn_rest_endpoint)
        account_response = requests.post(url=request_url,
                                         headers=self.request_headers,
                                         params=self.get_access_token(),
                                         json=account_payload,
                                         allow_redirects=False,
                                         timeout=self.timeout)
        if self.verbosity > 1:
            print("Account generation response:\n{}".format(
                yaml.dump(account_response)))
        account_info = json.loads(account_response.content)
        if account_response.status_code != 201:
            message = account_info["message"]
            raise requests.HTTPError(
                "Command did not complete. {}".format(message))
        account_id = account_info["accountId"]
        if self.verbosity:
            print("Account ID: {}".format(account_id))

        # Set Password
        password_payload = {
            "login": login,
            "password": password,
            "token": account_info["token"],
            "reason": "2"
        }
        request_url = "{endpoint}v1/account/setPasswordAndActivate".format(
            endpoint=self.sn_rest_endpoint)
        if self.verbosity:
            print("Setting Password")
            if self.verbosity > 1:
                print(yaml.dump(password_payload))
        password_response = requests.post(url=request_url,
                                          params=self.get_access_token(),
                                          json=password_payload,
                                          allow_redirects=False,
                                          timeout=self.timeout)
        if self.verbosity > 1:
            print("Set password response\n{}".format(
                yaml.dump(password_response)))
        if password_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")

        # Accept EULA
        if self.verbosity:
            print("Accepting End User License Agreement")
        request_url = "{endpoint}v1/license?appVersion=3.2".format(
            endpoint=self.sn_rest_endpoint)
        license_number_request = requests.get(url=request_url,
                                              headers=self.request_headers,
                                              timeout=self.timeout)
        license_number = json.loads(
            license_number_request.content)["licenseVersion"]
        license_put_payload = {
            'login': login,
            'password': password,
            'licenseNumber': license_number
        }
        request_url = "{endpoint}v1/account/acceptLicense".format(
            endpoint=self.sn_rest_endpoint)
        request_return = requests.put(url=request_url,
                                      json=license_put_payload,
                                      timeout=self.timeout)
        if request_return.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        if self.verbosity > 1:
            "Accept License Response:\n{}".format(yaml.dump(request_return))
        return account_id

    def delete_account(self) -> bool:
        """ Delete an account """
        # Check Protections
        if not self.account_id:
            raise ValueError("Account ID must be set")
        if self.environment == "prod":
            raise ValueError("Cannot delete accounts on prod")
        if self.verbosity:
            print("Check permissions on {}".format(self.account_id))
        if self._check_if_admin_is_self():
            raise ValueError("Cannot Delete Admin Account")
        account_uri = "{endpoint}v1/account/{account}".format(
            endpoint=self.sn_rest_endpoint, account=self.account_id)
        account_information_response = requests.get(
            url=account_uri,
            headers=self.request_headers,
            params=self.get_access_token(),
            timeout=self.timeout)
        if self.verbosity > 1:
            print("Account Information:\n{}".format(
                yaml.dump(account_information_response)))

        account_information = json.loads(account_information_response.content)
        if "accountName" not in account_information:
            raise ValueError("Account doesn't exist")
        if account_information["accountName"] in PROTECTED_ACCOUNTS:
            raise ValueError("Not allowed to delete {}".format(
                account_information["accountName"]))
        delete_account_response = requests.delete(
            url=account_uri,
            params=self.get_access_token(),
            timeout=self.timeout)
        if self.verbosity > 1:
            print("Account Delete Request:\n{}".format(
                yaml.dump(delete_account_response)))
        if delete_account_response.status_code == 200:
            return True
        return False

    def search_account_id(self, query: str) -> dict:
        """ Search for an account using a search query
        :param query: string to get a list of accounts from
        :return: Account IDs"""
        if len(query) < 3:
            raise ValueError("Search term must be at least 3 characters")
        if self.verbosity:
            print("Searching for account ID {}".format(self.account_id))
        search_url = "{endpoint}v1/filteredUsers/?filterByString={query}"
        search_url = search_url.format(endpoint=self.sn_rest_endpoint,
                                       query=query)
        account_search_response = requests.get(url=search_url,
                                               headers=self.request_headers,
                                               params=self.get_access_token(),
                                               timeout=self.timeout)
        if self.verbosity > 1:
            print("Search results:\n{}".format(
                yaml.dump(account_search_response)))
        if account_search_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        accounts = json.loads(account_search_response.content)
        return accounts

    def _check_if_admin_is_self(self) -> bool:
        """ Check if trying to delete the current admin account """
        accounts = self.search_account_id(query=self.admin_username)
        return self.account_id in accounts

    def get_devices(self) -> list:
        """ Get a list of all of the SleepIQ devices attached to an account """
        if self.verbosity:
            print("Get list of all devices")
        devices_url = "{endpoint}v1/account/{account_id}/devices".format(
            endpoint=self.sn_rest_endpoint, account_id=self.account_id)
        devices_request_response = requests.get(url=devices_url,
                                                headers=self.request_headers,
                                                params=self.get_access_token(),
                                                timeout=self.timeout)
        if self.verbosity > 1:
            print("Device List Request Response:\n{}".format(
                yaml.dump(devices_request_response)))
        if devices_request_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        devices = json.loads(devices_request_response.content)
        return devices["results"]

    def get_pump_device_id(self) -> str:
        """ Get the first device ID associated with a smart pump """
        devices = self.get_devices()
        if not devices:
            raise ValueError("No devices returned for account")
        pump_id = devices[0]["deviceId"]
        return pump_id

    def get_sleeper_information(self) -> dict:
        """ Get Sleeper information about the created account """
        if not self.account_id:
            raise ValueError("Account ID must be set")
        if self.verbosity:
            print("Get Sleeper Information for account {}".format(
                self.account_id))
        sleepers_url = "{endpoint}v1/account/{account_id}/sleepers"
        sleepers_url = sleepers_url.format(endpoint=self.sn_rest_endpoint,
                                           account_id=self.account_id)
        sleepers_request_response = requests.get(
            url=sleepers_url,
            headers=self.request_headers,
            params=self.get_access_token(),
            timeout=self.timeout)
        if self.verbosity > 1:
            print("Sleeper Information Request Response:\n{}".format(
                yaml.dump(sleepers_request_response)))
        if sleepers_request_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        sleepers = json.loads(sleepers_request_response.content)
        return sleepers["sleeperList"]

    def set_sleeper(self, sleeper_id: str, device_id: str, side: str):
        """ Set which side of the bed the sleeper is associated with
        :param sleeper_id: Sleeper Account ID to configure
        :param device_id: Device ID of the bed to put the sleeper in
        :param side: Side of the bed the account is configured for"""
        sides = {"left": {"side": "L"}, "right": {"side": "R"}}
        if side not in sides:
            raise ValueError("Side is not a valid side. Must be {}.".format(
                " or ".join(sides)))
        data = sides[side]
        data.update(self.get_access_token())
        if self.verbosity:
            print(
                "Setting sleeper[{sleeper_id}] on device[{device_id}] to {side}"
                .format(sleeper_id=sleeper_id, device_id=device_id, side=side))
        sleeper_url = "{endpoint}v1/account/{account_id}/sleeper/{sleeper_id}/device/{device_id}"
        sleeper_url = sleeper_url.format(endpoint=self.sn_rest_endpoint,
                                         account_id=self.account_id,
                                         sleeper_id=sleeper_id,
                                         device_id=device_id)
        sleeper_request = requests.put(url=sleeper_url,
                                       params=data,
                                       timeout=self.timeout)
        if self.verbosity > 1:
            print("Set Sleeper Response:\n{}".format(
                yaml.dump(sleeper_request)))
        if sleeper_request.status_code != 200:
            raise requests.HTTPError("Command did not complete")

    def set_mac_address(self, device_id: str, mac: str):
        """ Set the MAC address of the bed associated with the account
        :param device_id: Target Device
        :param mac: MAC address to set the device to """
        if self.verbosity:
            print("Set MAC address of device[{device}] to {mac}".format(
                device=device_id, mac=mac))
        # Normalize MAC address
        mac = normalize_mac_address(mac)
        data = {"macAddress": mac}
        data.update(self.get_access_token())
        mac_url = "{endpoint}v1/account/{account_id}/device/{device_id}/updateMacAddress"
        mac_url = mac_url.format(endpoint=self.sn_rest_endpoint,
                                 account_id=self.account_id,
                                 device_id=device_id)
        mac_request_response = requests.put(url=mac_url,
                                            params=data,
                                            timeout=self.timeout)
        if self.verbosity > 1:
            print("Set Mac Address Response:\n{}".format(
                yaml.dump(mac_request_response)))
        if mac_request_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")

    def add_wifi_network(self, ssid: str, psk: str):
        """ Add a WiFi network to the account
        :param ssid: WiFi Network SSID to add to account
        :param psk: WiFi Preshared Key for network"""
        if self.verbosity:
            print(
                "Add WiFi network to account. SSID: {ssid} PSK: {psk}".format(
                    ssid=ssid, psk=psk))
        data = {"name": ssid, "password": psk}
        wifi_url = "{endpoint}v1/account/{account_id}/wifi".format(
            endpoint=self.sn_rest_endpoint, account_id=self.account_id)
        wifi_response = requests.post(url=wifi_url,
                                      params=self.get_access_token(),
                                      json=data,
                                      timeout=self.timeout)
        if self.verbosity > 1:
            print("Add WiFi Response:\n{}".format(yaml.dump(wifi_response)))
        if wifi_response.status_code != 201:
            raise requests.HTTPError("Command did not complete")

    def configure_raw_data(self, device_id: str, enable: bool):
        """ Configure raw data collection for account
        :param device_id: Device to configure
        :param enable: Enable or disable configuration setting"""
        if self.verbosity:
            if enable:
                print("Enable Raw Data for device.")
            else:
                print("Disable Raw Data for device.")
        data = {"config_send_raw_data": enable}
        config_mode_url = "{endpoint}v1/account/{account_id}/device/{device_id}/configMode"
        config_mode_url = config_mode_url.format(
            endpoint=self.sn_rest_endpoint,
            account_id=self.account_id,
            device_id=device_id)
        config_mode_response = requests.put(url=config_mode_url,
                                            params=self.get_access_token(),
                                            json=data,
                                            timeout=self.timeout)
        if self.verbosity > 1:
            print("Raw Data Response:\n{}".format(
                yaml.dump(config_mode_response)))
        if config_mode_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")

    def configure_write_data_to_file(self, device_id: str, enable: bool):
        """ Configure writing data to raw1k files for account
        :param device_id: Device to configure
        :param enable: Enable or disable configuration setting"""
        if self.verbosity:
            if enable:
                print("Enable Write to File for device.")
            else:
                print("Disable Write to File for device.")
        data = {"config_write_to_file": enable}
        config_mode_url = "{endpoint}v1/account/{account_id}/device/{device_id}/configMode"
        config_mode_url = config_mode_url.format(
            endpoint=self.sn_rest_endpoint,
            account_id=self.account_id,
            device_id=device_id)
        config_mode_response = requests.put(url=config_mode_url,
                                            params=self.get_access_token(),
                                            json=data,
                                            timeout=self.timeout)
        if self.verbosity > 1:
            print("Write Data to File Response:\n{}".format(
                yaml.dump(config_mode_response)))
        if config_mode_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")

    def get_device_config(self, device_id: str) -> dict:
        """ Get the device configuration for a pump.
        :param device_id: Device ID of pump associated to account
        :return: Dictionary containing the configuration setting and the boolean
            value"""
        if self.verbosity:
            print("Getting configuration for device.")
        config_mode_url = "{endpoint}v1/account/{account_id}/device/{device_id}/configMode"
        config_mode_url = config_mode_url.format(
            endpoint=self.sn_rest_endpoint,
            account_id=self.account_id,
            device_id=device_id)
        config_mode_response = requests.get(url=config_mode_url,
                                            headers=self.request_headers,
                                            params=self.get_access_token(),
                                            timeout=self.timeout)
        if config_mode_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        config = json.loads(config_mode_response.content)
        if self.verbosity > 1:
            print("Write Data to File Response:\n{}".format(yaml.dump(config)))
        clean_config = {}
        for setting in config["config"]:
            clean_config[setting["id"].lstrip("config_")] = setting["setting"]
        return clean_config

    def get_usb_configuration_file(self) -> dict:
        """Get the bam-init.conf file used to configure a pump on first boot"""
        if self.verbosity:
            print("Get USB configuration file")
        bam_init_url = "{endpoint}v1/account/{account_id}/wifi/generateUsbFile"
        bam_init_url = bam_init_url.format(endpoint=self.sn_rest_endpoint,
                                           account_id=self.account_id)
        bam_init_request_return = requests.get(url=bam_init_url,
                                               headers=self.request_headers,
                                               params=self.get_access_token(),
                                               timeout=self.timeout)
        if self.verbosity > 1:
            print("Get USB configuration file response:\n{}".format(
                yaml.dump(bam_init_request_return)))
        if bam_init_request_return.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        bam_init = bam_init_request_return.content.decode().splitlines(True)
        return bam_init

    def get_bam_conf(
            self,
            conf_url: str,
            mac_address: str,
            internal_id: str,
            platform_version: int = 500,
            hardware_version: typing.SupportsInt = 175) -> typing.List[str]:
        """ Get bam.conf file used by smart pumps to get one and set up
        communication with the server

        :param conf_url: URL to get bam.conf from. Taken from bam-init.conf
        :param mac_address: MAC address of pump
        :param internal_id: Internal MAC Address
        :param platform_version: Software Platform Version. Defaults to 500 for
            Sleep Number Smart Pumps
        :param hardware_version: Hardware Version. Set to 175 for all devices
        :return: bam.conf file contents"""
        if valid_mac(internal_id) and valid_mac(mac_address):
            internal_id = normalize_mac_address(internal_id).lower()
            mac_address = normalize_mac_address(mac_address).lower()
        else:
            raise ValueError(
                "mac_address and internal_id must be valid MAC address'")
        if self.verbosity:
            print("Getting bam.conf")
        payload = {
            "deviceId": mac_address,
            "deviceId2": internal_id,
            "deviceVersion": platform_version,
            "accountNumber": self.account_id,
            "hardwareVersion": hardware_version,
        }
        conf_response = requests.post(url=conf_url,
                                      data=payload,
                                      timeout=self.timeout)
        if self.verbosity > 1:
            print("Configuration Request Response:\n{}".format(
                yaml.dump(conf_response)))
        if conf_response.status_code != 200:
            raise requests.HTTPError("Command did not complete")
        file_contents = conf_response.content.decode().splitlines(True)
        return file_contents


def generate_account(args: argparse.Namespace):
    """
    Generate the configuration file needed to use the "create" command
    :param args: Command line arguments
    """
    generated_user = random_fields(args)
    args.output.write(json.dumps(generated_user, indent=4))


def create_account(args: argparse.Namespace):
    """ Create a SleepIQ Account with the provided information
    :param args: Command line arguments
    """
    config = yaml.load(args.config, Loader=yaml.FullLoader)
    account_info = json.load(args.input)
    if args.verbose > 1:
        print(
            "Configuration:\n{config}\nAccount Information:\n{account}".format(
                config=yaml.dump(config), account=yaml.dump(account_info)))
    account = SleepIQAccount(admin_username=config["backoffice"]["username"],
                             admin_password=config["backoffice"]["password"],
                             environment=config["environment"],
                             verbosity=args.verbose)
    # User Password
    if "password" not in account_info or not valid_password(
            account_info["password"]):
        account_info["password"] = generate_password()
    account_id = account.create_account(**account_info)
    account.set_account_id(account_id)
    device_id = account.get_pump_device_id()
    pump_generation = account_info["components"][0]["generation"]
    if "mac_address" not in account_info:
        mac_address = random_mac(generation=pump_generation)
    else:
        mac_address = account_info["mac_address"]
    if "internal_id" not in account_info:
        internal_id = FAKE.random_mac()
    else:
        internal_id = account_info["internal_id"]
    account.set_mac_address(device_id=device_id, mac=mac_address)
    sleepers = account.get_sleeper_information()
    # Set sleeper to left side
    left_sleeper_id = sleepers[0]["sleeperId"]
    account.set_sleeper(sleeper_id=left_sleeper_id,
                        device_id=device_id,
                        side="right")
    account.add_wifi_network(ssid=config["wifi"]["ssid"],
                             psk=config["wifi"]["psk"])
    account.configure_raw_data(device_id=device_id, enable=True)
    account.configure_write_data_to_file(device_id=device_id, enable=True)
    # Set software version
    back_office_obj = back_office.BackOffice(
        admin_username=config["backoffice"]["username"],
        admin_password=config["backoffice"]["password"],
        environment=config["environment"],
        verbosity=args.verbose)
    back_office_obj.login()
    back_office_obj.save_software_by_login(
        login=account_info["login"],
        app_version=config["version"]["app"],
        rfs_version=config["version"]["rfs"],
        device_mode="")
    # Get output files
    bam_init = account.get_usb_configuration_file()
    args.init.write("".join(bam_init))
    bam_conf_url = None
    for line in bam_init:
        if "bam-conf" in line:
            _, bam_conf_url = line.split("=")
            bam_conf_url = bam_conf_url.strip()
            break
    if not bam_conf_url:
        raise ValueError("'bam-conf' entry not in 'bam-init.conf'")
    bam_conf = account.get_bam_conf(conf_url=bam_conf_url,
                                    mac_address=mac_address,
                                    internal_id=internal_id)
    args.output.write("".join(bam_conf))
    print(
        "Account Created. Account ID: {id}; Account Name: {reference}".format(
            id=account_id, reference=account_info["reference"]))


def delete_account(args: argparse.Namespace):
    """ Delete a SleepIQ Account using the provided account ID
    :param args: Command line arguments"""
    config = yaml.load(args.config, Loader=yaml.FullLoader)
    if args.verbose > 1:
        print("Configuration:\n{}".format(yaml.dump(config)))
    account = SleepIQAccount(admin_username=config["backoffice"]["username"],
                             admin_password=config["backoffice"]["password"],
                             environment=config["environment"],
                             verbosity=args.verbose)
    for account_id in args.account:
        account.set_account_id(account_id)
        try:
            account.delete_account()
            print("{}: Deleted".format(account_id))
        except ValueError:
            print("{}: Failed to Delete".format(account_id))


def create_config(args: argparse.Namespace):
    """
    Create a configuration file for use by this program.
    :param args: Command line arguments
    """
    config = {
        "environment": args.environment,
        "reference": args.reference,
        "backoffice": {
            "username": args.username,
            "password": args.password
        },
        "wifi": {
            "ssid": args.ssid,
            "psk": args.psk
        },
        "version": {
            "app": args.app,
            "rfs": args.rfs
        }
    }
    yaml.dump(config, args.config, sort_keys=False)


def generate_password() -> str:
    """ Generate a random password that meets the SleepIQ Password Standards """
    special_char = "^$*.[]{}()?-\"!@#%&/\\,><':;|_~`"
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice(special_char)
    rest = random.choices("".join(
        [special_char, string.ascii_letters, string.digits]),
                          k=random.randint(4, 16))
    full = [*upper, *lower, *digit, *special, *rest]
    random.shuffle(full)
    return "".join(full)


def valid_password(password: str) -> bool:
    r""" Check to see if a password is valid
        1. Has to be at least 8 characters long.
        2. There must be at least one Uppercase letter.
        3. There must be at least one Lower case letter.
        4. There must be at least one digit.
        5. There must be at least one special charter from the following set:
              ^ $ * . [ ] { } ( ) ? - " ! @ # % & / \ , > < ' : ; | _ ~ `
    :param password: Password to check
    :return: True if valid, False if invalid
    """
    special_char = "^$*.[]{}()?-\"!@#%&/\\,><':;|_~`"
    checks = [
        string.digits, string.ascii_lowercase, string.ascii_uppercase,
        special_char
    ]
    if len(password) < 8:
        return False
    for check in checks:
        # Compares two sets using intersection. If the returned set is empty,
        # there are not intersections, which means the check failed, and the
        # password isn't valid
        if not set(password) & set(check):
            return False
    return True


def main():
    """ Main function """
    args = parse_arguments()
    if args.command == "config":
        create_config(args)
    if args.command == "generate":
        generate_account(args)
    if args.command == "create":
        create_account(args)
    if args.command == "delete":
        delete_account(args)


if __name__ == "__main__":
    main()
