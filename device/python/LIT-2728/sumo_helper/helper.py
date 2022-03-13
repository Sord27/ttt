import configparser
import csv
from settings import CONFIG


def read_config(ini_file: str, section: str) -> dict:
    """ Read configuration file and return a dictionary object
    :param ini_file: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    config = configparser.ConfigParser()
    config.read(CONFIG)

    # get section, default to mysql
    config_ini = {}
    if config.has_section(section):
        items = config.items(section)
        for item in items:
            config_ini[item[0]] = item[1]
    else:
        print(ini_file)
        raise Exception('{0} section not found in the {1} file'.format(section, ini_file))

    return config_ini


def read_sumoql(file: str) -> str:
    """ Read *.sumoql file and return a string object
    :param sumoql_file: name of file with query
    :return: a string of query
    """
    with open(file, 'r') as file:
        data = file.read().replace('\n', '')
    return data


def write_csv_file(file: str, fields: list, records: list):
    with open(file, 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames=fields)

        # writing headers (field names)
        writer.writeheader()

        # writing data rows
        writer.writerows(records)
