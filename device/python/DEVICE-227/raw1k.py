#! /usr/bin/env python3
"""
Script to parse raw1k files and output data
"""
import argparse
import datetime
import gzip
import io
import itertools
import json
import logging
import multiprocessing
import shutil
import struct
import sys

import progress_bar
import pytz

LOG = logging.getLogger()
LOG_HANDLE = logging.StreamHandler()
LOG_FORMAT = logging.Formatter(
    "%(asctime)s %(name)-8s %(levelname)-8s "
    "%(message)s", "%Y-%m-%d %H:%M:%S")
LOG_HANDLE.setFormatter(LOG_FORMAT)
LOG.addHandler(LOG_HANDLE)
DEFAULT_TAGS = "tags.json"
SIDE_LOOKUP = {"keep": -1, "left": 1, "right": 0, "both": 2}
DEFAULT_SIDE_OPTION = "keep"
DEFAULT_SIDE_VALUE = SIDE_LOOKUP[DEFAULT_SIDE_OPTION]
TIME_METAVAR = "HH:MM:SS"
UNSUPPORTED = "UNSUPPORTED"


def main():
    """ Main function for raw1k parsing """
    args = argument_parsing()
    set_log_level(args.verbosity)
    tags = import_json_tags(args.tags)

    if args.filter:
        tags = filter_tags(tags, args)

    if args.subcommand == "modify":
        LOG.info("Duplicating %s", args.input)
        shutil.copyfile(args.input, args.output)
        LOG.info("Finding and changing timestamps")
        modify_raw1k_file(args.input,
                          args.output,
                          tags,
                          date=args.date,
                          time=args.time,
                          start_time=args.start,
                          end_time=args.end,
                          side=args.side)
        LOG.info("Timestamps changed. Modified file saved as %s", args.output)
    elif args.subcommand == "raw":
        LOG.info("Parsing %s", args.input)
        parsed_raw_file = parse_raw1k_file(args.input, tags)
        export_raw_pressure_data(parsed_raw_file, args.output)
    elif args.subcommand == "dump":
        LOG.info("Parsing %s", args.input)
        parsed_raw_file = parse_raw1k_file(args.input, tags, bool(args.filter), raw=args.raw)
        export_raw1k_json_file(parsed_raw_file, args.output)
    sys.exit(0)


####################
# ARGUMENT PARSING #
####################


def argument_parsing():
    """ Parse the command line arguments """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(dest="subcommand")
    # sub parser for json output
    dump_description = "Dump raw1k to JSON"
    dump_parser = subparsers.add_parser(
        "dump",
        description=dump_description,
        help=dump_description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    dump_parser.add_argument("-i",
                             "--input",
                             required=True,
                             help="input raw1k file")
    dump_parser.add_argument("-o",
                             "--output",
                             required=True,
                             help="output json file")
    dump_parser.add_argument("-t",
                             "--tags",
                             default=DEFAULT_TAGS,
                             help="tags json file used for parsing")
    dump_parser.add_argument("--raw",
                             action="store_true",
                             default=False,
                             help="Add raw pressure values to json file")
    dump_parser.add_argument("-v", "--verbosity", action="count", default=0)

    dump_parser.add_argument("-f",
                             "--filter",
                             nargs='*',
                             help="Filter output tags")

    # sub parser for raw pressure output
    raw_description = "Dump raw pressure values to a single file"
    raw_parser = subparsers.add_parser(
        "raw",
        description=raw_description,
        help=raw_description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    raw_parser.add_argument("-i",
                            "--input",
                            required=True,
                            help="input raw1k file")
    raw_parser.add_argument("-o",
                            "--output",
                            required=True,
                            help="output raw pressure file")
    raw_parser.add_argument("--tags",
                            default=DEFAULT_TAGS,
                            help="tags json file used for parsing")
    raw_parser.add_argument("-v", "--verbosity", action="count", default=0)

    # sub parser for raw1k output
    raw1k_description = "Modify aspects of a raw1k file"
    modify_parser = subparsers.add_parser(
        "modify",
        description=raw1k_description,
        help=raw1k_description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        conflict_handler="resolve")
    modify_parser.add_argument("-i",
                               "--input",
                               required=True,
                               help="input raw1k file")
    modify_parser.add_argument("-o",
                               "--output",
                               required=True,
                               help="output raw pressure file")
    modify_parser.add_argument("-t",
                               "--tags",
                               default=DEFAULT_TAGS,
                               help="tags json file used for parsing")
    modify_parser.add_argument("--side",
                               choices=SIDE_LOOKUP,
                               default=DEFAULT_SIDE_OPTION,
                               help="Set the sleeper to a specific side")
    modify_parser.add_argument("-v", "--verbosity", action="count", default=0)
    time = modify_parser.add_argument_group("Time Modification")
    time.add_argument("-d",
                      "--date",
                      type=validate_date,
                      required=False,
                      metavar="YYYY-MM-DD",
                      help="desired date")
    time.add_argument("-t",
                      "--time",
                      type=validate_time,
                      required=False,
                      metavar=TIME_METAVAR,
                      help="change timestamp start time")

    truncate = modify_parser.add_argument_group("Truncate")
    truncate.add_argument("-s",
                          "--start",
                          type=validate_time,
                          metavar=TIME_METAVAR,
                          help="Specify start time of truncated sample")
    truncate.add_argument("-e",
                          "--end",
                          type=validate_time,
                          metavar=TIME_METAVAR,
                          help="Specify end time of truncated sample")
    # Parse the arguments
    args = parser.parse_args()
    return args


def validate_date(in_string):
    """ Validate the entered date from the command line """
    try:
        return datetime.datetime.strptime(in_string, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Date must be entered as "YYYY-MM-DD"')


def validate_time(in_string):
    """ Validate the entered time from the command line """
    try:
        return datetime.datetime.strptime(in_string, "%H:%M:%S").time()
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Time must be entered as "{}"'.format(TIME_METAVAR))


def set_log_level(verbosity):
    """ Set the log level of the application """
    if verbosity == 0:
        LOG.setLevel(logging.WARNING)
    elif verbosity == 1:
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.DEBUG)
        return


###########################
# RAW1K PARSING FUNCTIONS #
###########################


def import_json_timezones(input_file_path):
    """ Import timezones as a json file into a dictionary for parsing """
    with open(input_file_path) as tags_json:
        return json.load(tags_json)


def import_json_tags(input_file_path):
    """ Import tags as a json file into a dictionary for parsing """
    with open(input_file_path) as tags_json:
        return json.load(tags_json)


def parse_raw1k_file(input_file_path, tags, filter_input=False, raw=True, show_bar=True):
    """ Read in the raw1k file and parse it into a dictionary"""
    packet_parsers = create_packet_parser_lookup(tags)
    tag_lookup_dict = create_tag_lookup_dict(tags)
    packets_to_parse = {}
    with open(input_file_path, "rb") as raw1k:
        if show_bar:
            file_read_bar = progress_bar.InitBarForInfile(input_file_path)
        # Get and parse header
        file_header = parse_file_header(file=raw1k,
                                        tags=tags,
                                        packet_parsers=packet_parsers,
                                        filter_input=filter_input)
        packets = {"header": file_header}
        # Get rest of packets
        for packet_id, packet in enumerate(packets_in_file(raw1k)):
            packet["data"] = read_raw_bytes(raw1k, packet["packet_size"])
            raw_data_size = read_short(raw1k)  # Length of compressed data
            packet["compressed_data"] = read_raw_bytes(raw1k, raw_data_size)
            packets_to_parse[packet_id] = packet
            if show_bar:
                file_read_bar(raw1k.tell())
        if show_bar:
            del file_read_bar
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        if show_bar:
            bar_size = len(packets_to_parse)
            parse_bar = progress_bar.InitBar(title="Parsing", size=bar_size)
        parse_packet_tasks = {}
        # Set up multi processing tasks for parsing each packet
        for packet_id, packet in packets_to_parse.items():
            parse_packet_tasks[packet_id] = pool.apply_async(
                parse_packet, (
                    packet,
                    tags,
                    packet_parsers,
                    tag_lookup_dict,
                    raw,
                    filter_input,
                ))
        # Get the parsed tags for each packet
        for packet_id, parsed_packet in parse_packet_tasks.items():
            packets[packet_id] = parsed_packet.get()
            if show_bar:
                parse_bar(packet_id)
    return packets


def parse_packet(packet, tags, packet_parsers, tag_lookup_dict, raw, filter_input):
    """ Parse tags in a packet"""
    with io.BytesIO(packet["data"]) as packet_data:
        repeat_tags = {}
        parsed_tags = {
            "time_stamp": packet["time_stamp"],
            "packet_size": packet["packet_size"]
        }
        for tag_id in packet_tag_ids(packet_data, tags):
            tag_name = tag_lookup_dict.get(tag_id, UNSUPPORTED)
            if filter_input and tag_name == UNSUPPORTED:
                continue
            packet_parser = packet_parsers.get(tag_id, default_parser)
            if tag_name in parsed_tags:
                repeat_tags[tag_id] = repeat_tags.get(tag_id, 0) + 1
                tag_name = "{}-{}".format(tag_name, repeat_tags[tag_id])
            parsed_tag = parse_tag(packet_data, tag_id, packet_parser)
            parsed_tags[tag_name] = parsed_tag
        # Parse Raw Data/compressed section
        raw_tags = parse_compressed_data(packet["compressed_data"], tags,
                                         packet_parsers, raw)
        for tag_name, tag_data in raw_tags.items():
            if filter_input and tag_name == UNSUPPORTED:
                continue
            parsed_tags[tag_name] = tag_data
    return parsed_tags


BYTES_IN_PACKET_HEADER = 10
SIZE_BYTES = 2
SENSOR_SERIAL_NUMBER_TAG = 331
TIME_ZONE_TAG = 202
TIME_TAGS = {350, 351}  # DSP and RAWDATA timestamps


def modify_raw1k_file(input_file_path, output_file_path, tags, **kwargs):
    """ Change time stamp in raw1k file """
    show_bar = LOG.getEffectiveLevel() < logging.WARNING
    with open(input_file_path, "rb") as raw1k, open(output_file_path,
                                                    "r+b") as output_file:
        if show_bar:
            current_progress_bar = progress_bar.InitBarForInfile(
                input_file_path)
        # Truncate Arguments
        start_time = kwargs.pop("start_time")
        end_time = kwargs.pop("end_time")
        truncate = bool(start_time and end_time) and start_time != end_time
        # Time modification arguments
        date = kwargs.pop("date")
        time = kwargs.pop("time")
        modify_time = bool(date or time)
        time_offset = 0
        # Header modifications
        timezone = get_time_zone(raw1k, tags)
        modify_file_header(raw1k, output_file, tags, **kwargs)
        end_of_header = raw1k.tell()
        for packet_header in packets_in_file(raw1k):
            if modify_time:
                if not time_offset:
                    time_offset = get_time_stamp_offset(
                        packet_header["time_stamp"], date, time, timezone)
                location = raw1k.tell() - BYTES_IN_PACKET_HEADER
                update_timestamp(output_file, location, time_offset)
            # Find beginning of time slice
            if truncate and is_matching_packet(
                    start_time, packet_header["time_stamp"], timezone):
                LOG.debug("Found start of time slice offset: %d", raw1k.tell())
                start_offset = raw1k.tell() - BYTES_IN_PACKET_HEADER
            # Parse all tags in packet
            for tag_id in packet_tag_ids(raw1k, tags):
                # Update the timestamps
                if modify_time and tag_id in TIME_TAGS:
                    location = raw1k.tell() + SIZE_BYTES
                    update_timestamp(output_file, location, time_offset)
                parse_tag(raw1k, tag_id, default_parser)
            # Skip reading the raw data section
            raw_data_size = read_short(raw1k)
            skip_bytes(raw1k, raw_data_size)
            # Find end of time slice
            if truncate and is_matching_packet(
                    end_time, packet_header["time_stamp"], timezone):
                LOG.debug("Found end of time slice offset: %d", raw1k.tell())
                end_offset = raw1k.tell()
                raw1k.seek(0, 2)  # Seek to the end of the file
                break
            if show_bar:
                current_progress_bar(raw1k.tell())
        if show_bar:
            current_progress_bar(raw1k.tell())  # Update progress one last time
            del current_progress_bar
    if truncate:
        truncate_raw1k(end_of_header, start_offset, end_offset,
                       output_file_path)


BYTES_IN_FILE_HEADER = 34


def get_time_zone(input_file, tags):
    """ Get the timezone from the header """
    skip_bytes(input_file, BYTES_IN_FILE_HEADER)
    for tag_id in packet_tag_ids(input_file, tags):
        if tag_id == TIME_ZONE_TAG:
            parsed_tag = parse_tag(input_file, tag_id, time_zone, packed=True)
            timezone = parsed_tag["m_time_zone"]
            input_file.seek(0)
            return timezone
        parse_tag(input_file, tag_id, default_parser, packed=True)
    raise TypeError("File does not contain time zone information")


def modify_file_header(input_file, output_file, tags, **kwargs):
    """ Parse raw1k file header """
    side = kwargs.pop("side")
    edit_side = side in SIDE_LOOKUP and side != DEFAULT_SIDE_OPTION
    side = SIDE_LOOKUP.get(side, DEFAULT_SIDE_VALUE)
    skip_bytes(input_file, BYTES_IN_FILE_HEADER)  # Skip file header values
    for tag_id in packet_tag_ids(input_file, tags):
        if edit_side and tag_id == SENSOR_SERIAL_NUMBER_TAG:
            location = input_file.tell() + SIZE_BYTES
            update_side(output_file, location, side)
        parse_tag(input_file, tag_id, default_parser, packed=True)


def packet_tag_ids(file, tags):
    """ Generator for packet ids to allow for use in a for loop"""
    while True:
        tag_id = read_short(file)
        if tag_id == get_tag_id("TAG_END_OF_LIST", tags, tag_not_found=0):
            break
        yield tag_id


def packets_in_file(file):
    """ Generator for packet ids to allow for use in a for loop"""
    while True:
        try:
            time_stamp = read_long(file)
            packet_size = read_short(file)
            packet_header = {
                'time_stamp': time_stamp,
                'packet_size': packet_size
            }
            yield packet_header
        except struct.error:
            # Got to the end of the file
            break


def create_tag_lookup_dict(tags):
    """ Create a dict of tags keyed on tag_id with values being the string """
    tag_lookup = {}
    for tag in tags:
        if tag not in tag_lookup:
            tag_lookup[tags[tag]['tag']] = tag
    return tag_lookup


def parse_tag(file, tag_id, packet_parser, packed=False):
    """
    Parses a given tag_id from a file. Returns a dict with parsed information
    """
    byte_length = read_short(file)
    word_length = (byte_length + 3) >> 2
    byte_padding_length = (word_length * 4 - byte_length)
    # Get the correct packet parser
    to_return = packet_parser(file=file, tag=tag_id, byte_length=byte_length)
    if byte_padding_length and not packed:
        skip_bytes(file, byte_padding_length)
    return to_return


def parse_compressed_data(compressed, tags, packet_parsers, raw):
    """ Parse the compressed data at the end of the data packet"""
    tag_lookup_dict = create_tag_lookup_dict(tags)
    decompressed = gzip.decompress(compressed)
    parsed_tags = {}
    with io.BytesIO(decompressed) as uncompressed:
        for tag_id in packet_tag_ids(uncompressed, tags):
            tag_name = tag_lookup_dict.get(tag_id, UNSUPPORTED)
            packet_parser = packet_parsers.get(tag_id, default_parser)
            if not raw and tag_name == "TAG_A2D_CH_DATA_32":
                parse_tag(uncompressed, tag_id, default_parser,
                          packed=True)  # Skip reading in the raw data
            else:
                parsed_tags[tag_name] = parse_tag(uncompressed,
                                                  tag_id,
                                                  packet_parser,
                                                  packed=True)
    return parsed_tags


def export_raw1k_json_file(raw1k_dict, output_file_path):
    """ Export a JSON file of the parsed raw file"""
    LOG.info("Dumping json data to %s", output_file_path)
    write_bar = progress_bar.InitBar(title=output_file_path,
                                     size=len(raw1k_dict))
    with open(output_file_path, "w+") as raw1k_json:
        raw1k_json.write("{\n")
        for packet_id, parsed_packet in enumerate(raw1k_dict.items()):
            packet, data = parsed_packet
            if packet_id < len(raw1k_dict) - 1:  # Correct for 0 based indexing
                raw1k_json.write("  \"{}\": {},\n".format(
                    packet, json.dumps(data)))
            else:  # omit comma for last packet
                raw1k_json.write("  \"{}\": {}\n".format(
                    packet, json.dumps(data)))
            write_bar(packet_id)
        raw1k_json.write("}\n")
    LOG.info("JSON data dumped to %s", output_file_path)


def export_raw_pressure_data(raw1k_dict, output_file_path):
    """ Export a binary file with only raw pressure data """
    LOG.info("Exporting raw pressure data to %s", output_file_path)
    with open(output_file_path, "wb+") as raw_pressure:
        for entry in raw1k_dict:
            if 'TAG_A2D_CH_DATA_32' not in raw1k_dict[entry].keys():
                continue
            samples = raw1k_dict[entry]['TAG_A2D_CH_DATA_32']['m_samples']
            for sample in samples:
                raw_pressure.write(struct.pack('i', sample))
    LOG.info("Raw pressure data exported to %s", output_file_path)


def get_time_stamp_offset(time_stamp, set_date, set_time, timezone):
    """ Calculate the offset of the between the original raw1k timestamp and the
        desired timestamp.
    """
    base_datetime = datetime.datetime.fromtimestamp(time_stamp / 1000)
    base_date = base_datetime.date()
    base_time = base_datetime.time()
    if set_date is None:
        set_date = base_date
    if set_time is None:
        set_time = base_time
    set_datetime = datetime.datetime.combine(set_date, set_time)
    set_datetime = pytz.timezone(timezone).localize(set_datetime)
    set_time_stamp = datetime.datetime.timestamp(set_datetime) * 1000
    LOG.debug("Timestamp derived from given date and time is %d",
              set_time_stamp)
    LOG.debug("Raw1k timestamp starts at %d", time_stamp)
    offset = set_time_stamp - time_stamp
    LOG.debug("Timestamp offset is %d", offset)
    return offset


def is_matching_packet(goal_time, time_stamp, timezone):
    """ determine if the current packet is the starting packet of the desired
        sample.
    """
    base_datetime = datetime.datetime.fromtimestamp(time_stamp / 1000)
    base_datetime = pytz.timezone(timezone).localize(base_datetime)
    goal_datetime = datetime.datetime.combine(base_datetime.date(), goal_time)
    goal_datetime = pytz.timezone(timezone).localize(goal_datetime)
    return base_datetime == goal_datetime


##################
# FILE UTILITIES #
##################


def read_short(file):
    """ Read 2 bytes and then unpack and return as a short"""
    return struct.unpack("h", file.read(2))[0]


def read_int(file):
    """ Read 4 bytes, unpack, return as an integer"""
    return struct.unpack("i", file.read(4))[0]


def read_byte(file):
    """ Read in 1 byte"""
    return int.from_bytes(file.read(1), byteorder='little')


def read_long(file):
    """ Read 8 bytes, unpack, return as a long long """
    return struct.unpack("q", file.read(8))[0]


def read_boolean(file):
    """ Read 1 byte, unpack and return as a boolean """
    return struct.unpack("?", file.read(1))[0]


def read_string(file, length):
    """ Read a string of characters from binary file, return string"""
    return file.read(length).decode('utf-8')


def read_raw_bytes(file, length):
    """ Read raw bytes and return them """
    return file.read(length)


def skip_bytes(file, bytes_to_skip=1):
    """ Skip bytes in file """
    file.seek(file.tell() + bytes_to_skip)


def write_int(file, value):
    """ Write an integer to a file """
    to_write = struct.pack("i", int(value))
    file.write(to_write)


def write_long(file, value):
    """ Write a long to a file """
    to_write = struct.pack("q", int(value))
    file.write(to_write)


###############
# TAG PARSERS #
###############


def create_packet_parser_lookup(tags):
    """ Match a tag to the appropriate packet parser. Return packet parser for tag """
    # yapf: disable
    packet_parsers = {
        get_tag_id("TAG_AVG_RAW_DATA", tags): avg_raw_data,
        get_tag_id("TAG_PROCESSED_AVG_THRESHOLD_DATA", tags): processed_avg_threshold_data,
        get_tag_id("TAG_PROCESSED_PAD_ANGLE", tags): processed_pad_angle,
        get_tag_id("TAG_PROCESSED_PRESENCE", tags): processed_presence,
        get_tag_id("TAG_DEVICE_COMMAND", tags): device_command,
        get_tag_id("TAG_PUMP_STATUS", tags): pump_status,
        get_tag_id("TAG_PUMP_STATUS_2", tags): pump_status_2,
        get_tag_id("TAG_BIOMETRICS", tags): biometrics,
        get_tag_id("TAG_PROCESSED_DRIFT", tags): processed_drift,
        get_tag_id("TAG_PROCESSED_SNR", tags): processed_snr,
        get_tag_id("TAG_ALGO_INIT", tags): algo_init,
        get_tag_id("TAG_PROCESSED_DATA", tags): processed_data,
        get_tag_id("TAG_SMART_ALARM", tags): smart_alarm,
        get_tag_id("TAG_XPORT_RAW_DATA_FOOTER", tags): xport_raw_data_footer,
        get_tag_id("TAG_PROCESSED_ALERT", tags): processed_alert,
        get_tag_id("TAG_ALGO_VERSION", tags): algo_version,
        get_tag_id("TAG_OUT_BYEDGEDETECT", tags): out_byedgedetect,
        get_tag_id("TAG_ALL_FFT_POWER", tags): all_fft_power,
        get_tag_id("TAG_A2D_OFFSET", tags): a2d_offset,
        get_tag_id("TAG_INFO_FOR_ALGO", tags): info_for_algo,
        get_tag_id("TAG_DSP_SEQ_NUM", tags): dsp_seq_number,
        get_tag_id("TAG_RAWDATA_SEQ_NUM", tags): rawdata_seq_number,
        get_tag_id("TAG_RDP_SEQ_NUM", tags): rdp_seq_num,
        get_tag_id("TAG_RDP_VERSION", tags): rdp_version,
        get_tag_id("TAG_DSP_TIMESTAMP", tags): dsp_timestamp,
        get_tag_id("TAG_RAWDATA_TIMESTAMP", tags): rawdata_timestamp,
        get_tag_id("TAG_DEVICE_ID", tags): device_id,
        get_tag_id("TAG_USER_ID", tags): user_id,
        get_tag_id("TAG_START_TIME", tags): parse_start_time,
        get_tag_id("TAG_END_TIME", tags): parse_end_time,
        get_tag_id("TAG_A2D_N_CHANNELS", tags): a2d_channels,
        get_tag_id("TAG_A2D_SAMPLES_CH", tags): a2d_samples_channel,
        get_tag_id("TAG_A2D_SAMPLE_PERIOD", tags): a2d_sample_period,
        get_tag_id("TAG_DEVICE_CONFIG", tags): device_config,
        get_tag_id("TAG_TIME_ZONE", tags): time_zone,
        get_tag_id("TAG_IS_COMPRESSED", tags): is_compressed,
        get_tag_id("TAG_HARDWARE_VER", tags): hardware_version,
        get_tag_id("TAG_HEADER_ALGO_VERSION", tags): header_algo_version,
        get_tag_id("TAG_HEADER_ATM_PRESSURE_OFFSET", tags): header_atm_pressure_offset,
        get_tag_id("TAG_HEADER_ALGO_RUNNINGON", tags): header_algo_running_on,
        get_tag_id("TAG_HEADER_INFO_FOR_ALGO", tags): header_info_for_algo,
        get_tag_id("TAG_LAST_PACKET_POSITION", tags): last_packet_position,
        get_tag_id("TAG_A2D_CH_DATA_32", tags): a2d_ch_data_32,
        get_tag_id("TAG_SENSOR_VERSION", tags): sensor_version,
        get_tag_id("TAG_ACCEL_XYZ", tags): accel_xyz,
        get_tag_id("TAG_IW_STATS_QUAL", tags): iw_stats_qual,
        get_tag_id("TAG_DEVICE_STATUS", tags): device_status,
        get_tag_id("TAG_SENSOR_SER_NO", tags): sensor_ser_no,
        get_tag_id("TAG_HRV", tags): hrv,
        get_tag_id("TAG_BED_THERMAL_SETTINGS", tags): bed_thermal_settings
    }
    # yapf: enable
    return packet_parsers


def get_tag_id(tag_name, tags, tag_not_found=-1):
    """ Get the tag_id given a tag name """
    return tags.get(tag_name, {}).get("tag", tag_not_found)


def parse_file_header(file, tags, packet_parsers, filter_input):
    """ Parse raw1k file header """
    m_file_version = read_byte(file)
    m_endian = read_byte(file)
    m_last_packet_p1 = read_long(file)
    m_last_packet_p2 = read_long(file)
    m_eof1 = read_long(file)
    m_eof2 = read_long(file)
    header = {
        "m_file_version": m_file_version,
        "m_endian": m_endian,
        "m_last_packet_p1": m_last_packet_p1,
        "m_last_packet_p2": m_last_packet_p2,
        "m_eof1": m_eof1,
        "m_eof2": m_eof2
    }
    tag_lookup_dict = create_tag_lookup_dict(tags)
    repeat_tags = {}
    for tag_id in packet_tag_ids(file, tags):
        tag_name = tag_lookup_dict.get(tag_id, UNSUPPORTED)
        packet_parser = packet_parsers.get(tag_id, default_parser)
        if tag_name in header:
            repeat_tags[tag_id] = repeat_tags.get(tag_id, 0) + 1
            tag_name = "{}-{}".format(tag_name, repeat_tags[tag_id])

        parsed_tag = parse_tag(file, tag_id, packet_parser, packed=True)
        if filter_input and tag_name == UNSUPPORTED:
            continue
        header[tag_name] = parsed_tag
    return header


def avg_raw_data(**kwargs):
    """ Parse average raw data """
    samples = int(kwargs["byte_length"] / 4)
    m_avg_raw_data = []
    for _ in itertools.repeat(None, samples):
        m_avg_raw_data.append(read_int(kwargs["file"]))
    return {
        'tag': kwargs["tag"],
        'samples': samples,
        'm_avg_raw_data': m_avg_raw_data
    }


def processed_avg_threshold_data(**kwargs):
    """ Parse processed average threshold data """
    samples = int(kwargs["byte_length"] / 4)
    m_avg_threshold_data = []
    for _ in itertools.repeat(None, samples):
        m_avg_threshold_data.append(read_int(kwargs["file"]))
    return {
        'tag': kwargs["tag"],
        'samples': samples,
        'm_avg_threshold_data': m_avg_threshold_data
    }


def processed_pad_angle(**kwargs):
    """ Parse processed pad angle """
    m_accel_angle = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_accel_angle': m_accel_angle}


def processed_presence(**kwargs):
    """ Parse processed presence """
    m_is_in_bed = read_byte(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_is_in_bed': m_is_in_bed}


def device_command(**kwargs):
    """ Parse device command"""
    m_device_command = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_device_command': m_device_command}


def pump_status(**kwargs):
    """ Parse pump status """
    m_serial = read_int(kwargs["file"])
    m_pump_status = read_byte(kwargs["file"])
    m_foundation_status = read_byte(kwargs["file"])
    m_sleep_number = read_byte(kwargs["file"])
    skip_bytes(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_pump_status': m_pump_status,
        'm_foundation_status': m_foundation_status,
        'm_sleep_number': m_sleep_number,
        'm_serial': m_serial
    }


def pump_status_2(**kwargs):
    """ Parse pump status 2 """
    m_serial = read_int(kwargs["file"])
    m_pump_status = read_byte(kwargs["file"])
    m_foundation_status = read_byte(kwargs["file"])
    m_sleep_number = read_byte(kwargs["file"])
    m_foot_angle = read_byte(kwargs["file"])
    m_head_angle = read_byte(kwargs["file"])
    skip_bytes(kwargs["file"], 3)
    return {
        'tag': kwargs["tag"],
        'm_pump_status': m_pump_status,
        'm_foundation_status': m_foundation_status,
        'm_sleep_number': m_sleep_number,
        'm_foot_angle': m_foot_angle,
        'm_head_angle': m_head_angle,
        'm_serial': m_serial
    }


def biometrics(**kwargs):
    """ Parse biometrics """
    m_heart_rate = read_byte(kwargs["file"])
    m_respiration_rate = read_byte(kwargs["file"])
    m_figure_of_merit = read_long(kwargs["file"])
    skip_bytes(kwargs["file"], 2)
    return {
        'tag': kwargs["tag"],
        'm_heart_rate': m_heart_rate,
        'm_respiration_rate': m_respiration_rate,
        'm_figure_of_merit': m_figure_of_merit
    }


def processed_drift(**kwargs):
    """ parse processed drift """
    m_drift = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_drift': m_drift}


def processed_snr(**kwargs):
    """ Parse processed signal to noise ratio """
    m_snr = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_snr': m_snr}


def algo_init(**kwargs):
    """ Parse algorithm initialization """
    if kwargs["byte_length"]:
        skip_bytes(kwargs["file"], kwargs["byte_length"])
    return {'tag': kwargs["tag"], 'm_is_algo_init': True}


def processed_data(**kwargs):
    """ Parse processed data """
    m_version = read_int(kwargs["file"])
    packet = {'tag': kwargs["tag"]}
    if m_version == 3:
        packet['m_snr'] = read_int(kwargs["file"])
        packet['m_drift'] = read_int(kwargs["file"])
        packet['m_dyy_sum'] = read_int(kwargs["file"])
        packet['m_area_2_to_5Hz'] = read_int(kwargs["file"])
        packet['m_area_10_to_15Hz'] = read_int(kwargs["file"])
        packet['m_area_5_to_10Hz'] = read_int(kwargs["file"])
        packet['m_mse'] = read_int(kwargs["file"])
        packet['m_sum_diff_ac'] = read_int(kwargs["file"])
        packet['m_threshold_from_centroid'] = read_int(kwargs["file"])
        packet['m_on_off_from_delta_minus_drift'] = read_int(kwargs["file"])
        packet['m_delayed_on_off_by_fft_difference'] = read_int(kwargs["file"])
        packet['m_armed_timer_for_auto_correct'] = read_int(kwargs["file"])
        packet['m_on_off_from_pressure'] = read_int(kwargs["file"])
        if kwargs["byte_length"] == 66:
            packet['m_ra_status'] = read_byte(kwargs["file"])
            packet['m_processed_pressure'] = read_int(kwargs["file"])
            packet['m_fw_level'] = read_byte(kwargs["file"])
            packet['m_fast_presence'] = read_byte(kwargs["file"])
            packet['m_snore_presence'] = read_byte(kwargs["file"])
            packet['m_snore_level'] = read_short(kwargs["file"])
    else:
        skip_bytes(kwargs["file"], kwargs["byte_length"] - 4)
    return packet


def smart_alarm(**kwargs):
    """ Parse smart alarm """
    m_smart_alarm_seq_num = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_smart_alarm_seq_num': m_smart_alarm_seq_num
    }


def xport_raw_data_footer(**kwargs):
    """ Parse xport raw data footer """
    packet = {
        'tag': kwargs["tag"],
        'm_smart_alarm_countdown_timer': read_short(kwargs["file"])
    }
    if kwargs["byte_length"] >= 3:
        packet['m_do_fast_presence'] = read_boolean(kwargs["file"])
    if kwargs["byte_length"] >= 4:
        packet['m_snore_enabled'] = read_byte(kwargs["file"])
    return packet


def processed_alert(**kwargs):
    """ Parse processed alert"""
    m_alert = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_alert': m_alert}


def algo_version(**kwargs):
    """ Parse algo version """
    m_algo_version = read_int(kwargs["file"])
    m_algo_running_on = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_algo_version': m_algo_version,
        'm_algo_running_on': m_algo_running_on
    }


def out_byedgedetect(**kwargs):
    """ Parse out by edge dectect """
    m_out_by_edge_detect = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_out_by_edge_detect': m_out_by_edge_detect}


def all_fft_power(**kwargs):
    """ Parse all fft power """
    m_all_fft_power = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_all_fft_power': m_all_fft_power}


def a2d_offset(**kwargs):
    """ Parse a2d offset """
    m_atm_pressure_offset = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_atm_pressure_offset': m_atm_pressure_offset
    }


def info_for_algo(**kwargs):
    """ Parse information for algo """
    m_birth_year = read_int(kwargs["file"])
    m_height = read_short(kwargs["file"])
    m_weight = read_short(kwargs["file"])
    m_bed_type = read_byte(kwargs["file"])
    m_person_type = read_byte(kwargs["file"])
    m_a2d_mode = read_byte(kwargs["file"])
    m_chamber_type = read_byte(kwargs["file"])
    m_head_angle_from_wedge = read_byte(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_birth_year': m_birth_year,
        'm_height': m_height,
        'm_weight': m_weight,
        'm_bed_type': m_bed_type,
        'm_person_type': m_person_type,
        'm_a2d_mode': m_a2d_mode,
        'm_chamber_type': m_chamber_type,
        'm_head_angle_from_wedge': m_head_angle_from_wedge
    }


def dsp_seq_number(**kwargs):
    """ Parse DSP sequence number """
    m_seq_number_dsp = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_seq_number_dsp': m_seq_number_dsp}


def rawdata_seq_number(**kwargs):
    """ Parse Raw Data sequence number """
    m_seq_number_raw = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_seq_number_raw': m_seq_number_raw}


def rdp_seq_num(**kwargs):
    """ Parse RDP sequence number """
    m_seq_number = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_seq_number': m_seq_number}


def rdp_version(**kwargs):
    """ Parse RDP version """
    m_rdp_version = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_rdp_version': m_rdp_version}


def dsp_timestamp(**kwargs):
    """ Parse DSP timestamp """
    m_time_stamp_dsp = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_time_stamp_dsp': m_time_stamp_dsp}


def rawdata_timestamp(**kwargs):
    """ Parse Raw Data Timestamp """
    m_time_stamp_raw = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_time_stamp_raw': m_time_stamp_raw}


def device_id(**kwargs):
    """ Parse Device ID """
    m_device_id = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_device_id': m_device_id}


def user_id(**kwargs):
    """ Parse User ID """
    m_user_id = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_user_id': m_user_id}


def parse_start_time(**kwargs):
    """ Parse Start Time """
    m_start_time = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_start_time': m_start_time}


def parse_end_time(**kwargs):
    """ Parse End Time """
    m_end_time = read_long(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_end_time': m_end_time}


def a2d_channels(**kwargs):
    """ Parse Number of A2D Channels """
    m_a2d_channels = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_a2d_channels': m_a2d_channels}


def a2d_samples_channel(**kwargs):
    """ Parse A2D samples channel """
    m_a2d_samples_ch = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_a2d_samples_ch': m_a2d_samples_ch}


def a2d_sample_period(**kwargs):
    """ Parse A2D sample period """
    m_a2d_sample_period = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_a2d_sample_period': m_a2d_sample_period}


def device_config(**kwargs):
    """ Parse Device Configuration """
    m_device_config = read_short(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_device_config': m_device_config}


def time_zone(**kwargs):
    """ Parse time zone """
    m_time_zone = read_string(kwargs["file"], kwargs["byte_length"])
    return {'tag': kwargs["tag"], 'm_time_zone': m_time_zone}


def is_compressed(**kwargs):
    """ Parse is compressed """
    m_is_compressed = read_byte(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_is_compressed': m_is_compressed}


def hardware_version(**kwargs):
    """ Parse Hardware Version """
    m_hardware_version = read_int(kwargs["file"])
    return {'tag': kwargs["tag"], 'm_hardware_version': m_hardware_version}


def header_algo_version(**kwargs):
    """ Parse header algorithm version """
    m_header_algo_version = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_header_algo_version': m_header_algo_version
    }


def header_algo_running_on(**kwargs):
    """ Parse header algorithm running on """
    m_header_algo_running_on = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_header_algo_running_on': m_header_algo_running_on
    }


def header_atm_pressure_offset(**kwargs):
    """ Parse header atmospheric pressure offset """
    m_header_atm_pressure_offset = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_header_atm_pressure_offset': m_header_atm_pressure_offset
    }


def header_info_for_algo(**kwargs):
    """ Parse header information for algorithm """
    m_birth_year = read_int(kwargs["file"])
    m_height = read_short(kwargs["file"])
    m_weight = read_short(kwargs["file"])
    m_bed_type = read_byte(kwargs["file"])
    m_person_type = read_byte(kwargs["file"])
    m_a2d_mode = read_byte(kwargs["file"])
    m_chamber_type = read_byte(kwargs["file"])
    m_head_angle_from_wedge = read_byte(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_birth_year': m_birth_year,
        'm_height': m_height,
        'm_weight': m_weight,
        'm_bed_type': m_bed_type,
        'm_person_type': m_person_type,
        'm_a2d_mode': m_a2d_mode,
        'm_chamber_type': m_chamber_type,
        'm_head_angle_from_wedge': m_head_angle_from_wedge
    }


def last_packet_position(**kwargs):
    """ Parse last packet position """
    m_last_packet_position = read_long(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_last_packet_position': m_last_packet_position
    }


def a2d_ch_data_32(**kwargs):
    """ Parse A2D channel data """
    m_channel_number = read_int(kwargs["file"])
    m_number_of_samples = int((kwargs["byte_length"] - 4) / 4)
    if m_number_of_samples <= 0:
        raise ValueError("TAG_A2D_CH_DATA_32: number of samples not set")
    m_samples = []
    for _ in itertools.repeat(None, m_number_of_samples):
        m_samples.append(read_int(kwargs["file"]))
    return {
        'tag': kwargs["tag"],
        'm_channel_number': m_channel_number,
        'm_number_of_samples': m_number_of_samples,
        'm_samples': m_samples
    }


def sensor_version(**kwargs):
    """ Parse sensor version """
    types = {
        4: 'xyz',
        256: 'SP1',
        512: 'SP2',
        257: 'GVB',
        258: '360',
        -1: 'Unknown'
    }
    m_sensor_version = read_short(kwargs["file"])
    if m_sensor_version in types:
        return {
            'tag': kwargs["tag"],
            'm_sensor_version': m_sensor_version,
            'name': types[m_sensor_version]
        }
    return {'tag': kwargs["tag"], 'm_sensor_version': m_sensor_version}


def accel_xyz(**kwargs):
    """ Parse Accelerometer data """
    accel_samples = int(kwargs["byte_length"] / 4)
    samples = {}
    for sample in range(0, accel_samples):
        accel_sample = read_int(kwargs["file"])
        accel_x = (accel_sample >> 20) & 0x03FF
        accel_y = (accel_sample >> 10) & 0x03FF
        accel_z = (accel_sample >> 00) & 0x03FF
        samples[sample] = {
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
        }
    return {
        'tag': kwargs["tag"],
        'm_number_of_samples': accel_samples,
        'samples': samples
    }


def iw_stats_qual(**kwargs):
    """ Parse wifi quality """
    m_wifi_quality = read_short(kwargs["file"])
    m_wifi_level = read_short(kwargs["file"])
    m_wifi_noise = read_short(kwargs["file"])
    m_set_wifi_updated = read_short(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'm_wifi_quality': m_wifi_quality,
        'm_wifi_level': m_wifi_level,
        'm_wifi_noise': m_wifi_noise,
        'm_set_wifi_updated': m_set_wifi_updated
    }


def device_status(**kwargs):
    """ Parse device status """
    fields = [
        "PS_PUMP_STATUS", "PS_FND_STATUS", "PS_SLEEP_NUMBER", "PS_FOOT_ANGLE",
        "PS_HEAD_ANGLE", "PS_DUAL_TEMP_STATUS", "PS_DUAL_TEMP_BLOWER",
        "PS_HEIDI_HEATER", "PS_HEIDI_FAN", "PS_HEIDI_DIRECTION",
        "PS_HEIDI_TEMPERATURE", "PS_HEIDI_HEATER_NTS", "PS_HEIDI_FAN_NTS",
        "PS_HEIDI_DIRECTION_NTS", "PS_HEIDI_TEMPERATURE_NTS",
        "PS_HEIDI_MODE", "PS_HEIDI_MODE_NTS"
    ]
    fields_index = read_byte(kwargs["file"])
    value = read_byte(kwargs["file"])
    if fields_index < len(fields):
        return {'tag': kwargs["tag"], fields[fields_index]: value}
    return {'tag': kwargs["tag"], 'field_index': fields_index, 'value': value}


def sensor_ser_no(**kwargs):
    """ Parse sensor serial number """
    serial_numbers = {0: "right", 1: "left", 2: "both"}
    serial_number = read_int(kwargs["file"])
    side = serial_numbers.get(serial_number, "invalid")
    return {'tag': kwargs["tag"], 'sensor_serial': serial_number, 'side': side}


def hrv(**kwargs):
    """ Parse Heart Rate Variability """
    dsp_seq_numb = read_int(kwargs["file"])
    number_heart_beats = read_int(kwargs["file"])
    sum_of_b2b = read_int(kwargs["file"])
    sum_of_square_b2b = read_long(kwargs["file"])
    dsp_time_stamp_gmt = read_long(kwargs["file"])
    sensor_serial_number = read_int(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'dsp_seq_number': dsp_seq_numb,
        'number_heart_beats': number_heart_beats,
        'sum_of_b2b': sum_of_b2b,
        'sum_of_square_b2b': sum_of_square_b2b,
        'dsp_time_stamp_gmt': dsp_time_stamp_gmt,
        'sensor_serial_number': sensor_serial_number
    }


def bed_thermal_settings(**kwargs):
    """ Parse Temperature Data """
    serial_number = read_int(kwargs["file"])
    index =  read_byte(kwargs["file"])
    value = read_short(kwargs["file"])
    reason = read_byte(kwargs["file"])
    timestamp = read_long(kwargs["file"])
    return {
        'tag': kwargs["tag"],
        'serial_number': serial_number,
        'index': index,
        'value': value,
        'reason': reason,
        'timestamp': timestamp
    }


def default_parser(**kwargs):
    """ Skip unsupported tags """
    skip_bytes(kwargs["file"], kwargs["byte_length"])
    return {
        'tag': kwargs["tag"],
        'skipped': True,
        'bytes': kwargs["byte_length"]
    }


def filter_tags(tags, args):
    """ Filter necessary tag for further parsing """
    return {k: v for k, v in tags.items() if str(v['tag']) in args.filter}


##################
# FILE MODIFIERS #
##################


def truncate_raw1k(end_of_header, start_offset, end_offset, output_file_path):
    """ Truncate a raw1k file """
    with open(output_file_path, "r+b") as out_file:
        LOG.info("Truncating to specified times.")
        out_file.truncate(end_offset)
        out_file.seek(start_offset)
        section = out_file.read()
        out_file.truncate(end_of_header)
        out_file.seek(end_of_header)
        out_file.write(section)


def update_timestamp(output_file, location, time_offset):
    """ Update the time stamp of a file """
    output_file.seek(location)
    new_time_stamp = read_long(output_file) + time_offset
    output_file.seek(location)
    write_long(output_file, new_time_stamp)


def update_side(output_file, location, value):
    """ Update side """
    output_file.seek(location)
    write_int(output_file, value)


if __name__ == "__main__":
    main()
