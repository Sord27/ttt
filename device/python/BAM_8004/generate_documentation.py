"""
Script used to automatically generate the documentation of the BAMKeys
"""
import argparse
import os
from datetime import datetime
import copy
import re

# Global constants
FILE_PATHS = {
              # Actors section headers
              "siq": "details/sections/siq.md",
              "dual-temp": "details/sections/dual-temp.md",
              "other": "details/sections/other.md",
              "pump": "details/sections/pump.md",
              "foundation": "details/sections/foundation.md",
              "outlet": "details/sections/outlet.md",
              "audio-in": "details/sections/audio-in.md",
              # Other section headers
              "introduction": "details/sections/introduction.md",
              "keys_list": "details/sections/keys_list.md",
              # Generation files
              "markdown_output": "markdown_output.md",
              "commit_log": "commitlog.tex",
              "debug": "debug.txt"}
DEBUG = None
DEBUG_FILE = None


def parse_mode(input_mode):
    return {
        'G': 'Getter',
        'S': 'Setter',
        'B': 'Both',
        'E': 'Executor'
    }.get(input_mode, 'n/a')


def parse_calling(input_calling):
    return {
        'B': 'bamio',
        'M': 'bammcr',
        'I': 'Internal',
        'U': 'Unused'
    }.get(input_calling, 'n/a')


def parse_actors(input_actors):
    return {
        'P': 'Pump',
        'F': 'Foundation',
        'O': 'Outlet',
        'S': 'SIQ',
        'T': 'Thump-pump',
        'A': 'Audio-in',
        'D': 'Dual-temp'
    }.get(input_actors, 'n/a')


def parse_supported_pump(input_sp_type):
    return {
        '1': 'SP1/SP3',
        '2': 'SP2',
        '3': 'SP360',
        'G': 'Genie'
    }.get(input_sp_type, 'All')


def parse_command_type(input_command_type):
    return {
        'L': 'Left',
        'R': 'Right',
        'X': 'Both Sides',
        'I': 'Information',
        'M': 'Multi-key macro',
        'A': 'rad',
        '-': 'n/a'
    }.get(input_command_type, 'n/a')


def parse_required(input_value):
    return {
        "00000001": "-SHELL",
        "00000002": "-ADC=",
        "00000004": "-BLE",
        "00000008": "-LED",
        "00000010": "-THUMP",
        "00000020": "=FWS",
        "00000040": "-EVT",
        "00000080": "=SOC",
        "00000100": "=SUP",
        "00000200": "=HWPWR",
        "00000400": "=UNIBOARD",
        "00000800": "=FS_PUMP",
        "00001000": "=RDO_CCA",
        "40000000": "=GENIE",
        "80000000": "=SP2",
        "0": 'n/a'
    }.get(input_value.strip(), 'Error: ' + input_value)


def parse_key_type(input_key):
    return{
        "F": "Foundation",
        "L": "Local",
        "M": "MCR",
        "P": "Pump",
        "S": "Sleep Expert"
    }.get(input_key.strip()[0].upper(), "Other")


def link_key(input_key):
    return "[`" + input_key + "`](#" + input_key + ")"


def link_key_description(input_key, keys_dictionary):
    output_description = keys_dictionary[input_key]["description"]
    return "[" + input_key + "](#" + "-".join(output_description.strip().lower().split()) + ")"


def clean_key_entry(key_entry):
    pump_types = key_entry.keys()
    pump_types = [*pump_types]

    labels = key_entry[pump_types[0]].keys()
    labels = [*labels]

    new = {'pump_types': pump_types}

    if pump_types.__len__() is not 1:
        for label in labels:
            compare = []
            for pump in pump_types:
                compare.append(key_entry[pump][label])
            if all(value == compare[0] for value in compare):
                new[label] = compare[0]
            else:
                new[label] = {}
                for pump in pump_types:
                    new[label][pump] = key_entry[pump][label]
    else:
        for label in labels:
            new[label] = key_entry[pump_types[0]][label]
    return new


def parse_bio(input_file_path):
    
    input_file = open(input_file_path, mode='r')
    test_for_bio = open(input_file_path, mode='r')
    test = test_for_bio.readline()
    if DEBUG:
        DEBUG_FILE.write("Starting to read through BIO\n")
    so_min_index = 0
    so_max_index = 0

    if test.startswith('\ufeff#!') or test.startswith('#!'):
        if DEBUG:
            DEBUG_FILE.write("Saw that the first line had a shebang, looking for \"LIST=(\"\n")
        test_for_bio.close()
        line = input_file.readline()
        while line.strip() != "readonly LIST=(":
            if line.__contains__("SO_MIN_INDEX"):
                so_min_index = line.strip().split("=")[1].strip()
            if line.__contains__("SO_MAX_INDEX"):
                so_max_index = line.strip().split("=")[1].strip()
            line = input_file.readline()
        if DEBUG:
            DEBUG_FILE.write("Found \"LIST=(\"\n")

    keys_dict = {}
    for line in input_file:
        if line.strip() == ')':
            break
        # Replace the variables
        if line.__contains__("$SO_MIN_INDEX"):
            line = line.replace("$SO_MIN_INDEX", so_min_index)
        if line.__contains__("$SO_MAX_INDEX"):
            line = line.replace("$SO_MAX_INDEX", so_max_index)

        parsed_and_split_line = line.strip().strip("\"").split("|")

        # Section 1
        key = parsed_and_split_line[0][0:4]
        mode = parsed_and_split_line[0][5]
        calling = parsed_and_split_line[0][6]
        actors = parsed_and_split_line[0][7]
        sp_type = parsed_and_split_line[0][8]
        command_type = parsed_and_split_line[0][9]
        required = parsed_and_split_line[0][10:18]
        args_type = parsed_and_split_line[0][18]

        # Section 2
        description = parsed_and_split_line[1].strip()

        # Section 3
        related_commands = parsed_and_split_line[2].split(" ")

        # Section 4
        help_text = parsed_and_split_line[3]

        entry_type = sp_type
        if entry_type not in ['1', '2', '3', 'G']:
            entry_type = 'X'

        if key not in keys_dict:
            entry = {entry_type: {'mode': mode, 'calling': calling, 'actors': actors, 'command_type': command_type,
                                  'required': required, 'args_type': args_type, 'description': description,
                                  'related_commands': related_commands, 'help_text': help_text}}
            keys_dict[key] = entry
        else:
            keys_dict[key][entry_type] = {'mode': mode, 'calling': calling, 'actors': actors,
                                          'command_type': command_type, 'required': required, 'args_type': args_type,
                                          'description': description, 'related_commands': related_commands,
                                          'help_text': help_text}

    # Clean up the duplicate keys
    for current_key in keys_dict.keys():
        keys_dict[current_key] = clean_key_entry(keys_dict[current_key])
    return keys_dict


def clean_description(description):
    if '(l)' in description:
        description = description.replace('(l)', ' - left')
    if '(r)' in description:
        description = description.replace('(r)', ' - right')
    if '(Genie)' in description:
        description = description.replace('(Genie)', '- Genie')
    if '(cold)' in description:
        description = description.replace('(cold)', '- cold')
    if '(warm)' in description:
        description = description.replace('(warm)', '- warm')
    if 'w/' in description:
        description = description.replace('w/', 'with')
    if 'W/' in description:
        description = description.replace('W/', 'with')
    if '&' in description:
        description = description.replace('&', 'and')
    if ',' in description:
        description = description.replace(',', ' -')
    if '(ms)' in description:
        description = description.replace('(ms)', ' - ms')
    if '(s)' in description:
        description = description.replace('(s)', 's')
    if '/' in description:
        description = description.replace('/', '-')
    return description


def get_actors_dict(input_dict):
    actors_dict = {}
    for key in input_dict.keys():
        actor = input_dict[key]["actors"]
        if actor in actors_dict.keys():
            actor_list = actors_dict[actor]
            actor_list.append(key)
            actors_dict[actor] = actor_list
        else:
            actors_dict[actor] = [key]
    return actors_dict


def get_detail_files(keys_dict, verbosity):
    key_detail_files = {}
    top_dir = "details"
    if not os.path.exists(top_dir):
        if verbosity:
            print("Creating details folder")
        os.makedirs(top_dir)
    if DEBUG:
        DEBUG_FILE.write("Getting details files from the details folder for each key\n")
    # Get the file for each key in the dictionary
    for key in keys_dict.keys():
        key_dir = "keys"
        folder_path = "/".join([top_dir, key_dir])
        if not os.path.exists(folder_path):
            if verbosity:
                print("Creating " + key_dir + " folder")
            os.makedirs(folder_path)
        if DEBUG:
            DEBUG_FILE.write("Checking " + key + " for the first and last letter and file path.\n")
        if key[1].isupper() and key[-1:].islower():
            if DEBUG:
                DEBUG_FILE.write("      Last letter is lower\n")
            key_path = "/".join([top_dir, key_dir, key]) + "_.md"
        else:
            if DEBUG:
                DEBUG_FILE.write("Regular command\n")
            key_path = "/".join([top_dir, key_dir, key]) + ".md"
        if not os.path.isfile(key_path):
            if DEBUG:
                DEBUG_FILE.write("      Can't find " + key_path + "\n")
            if verbosity:
                print("Creating " + key + ".md detail file")
            key_file = open(key_path, mode='w+')
        else:
            if DEBUG:
                DEBUG_FILE.write("Opening " + key_path + "\n")
            key_file = open(key_path, mode='r')
        key_detail_files[key] = key_file
    return key_detail_files


def heading(text, heading_level):
    return "#" * heading_level + " " + text + " " + "#" * heading_level + "\n\n"


def table_heading(heading_items):
    line_1 = "\n| " + " | ".join(heading_items) + " |"
    line_2 = "\n| " + "----- | " * heading_items.__len__()
    return "\n".join([line_1, line_2.strip()]) + "\n"


def table_row(row_items):
    return "| " + " | ".join(row_items) + " |\n"


def copy_file_to_current_file(to_file_object, heading_level, from_file_path=None, from_file_object=None):
    """
    This function takes a markdown file and copies it to the currently opened file.
    If there are header tags in the file, it will convert the header depth to the appropriate depth
    :param to_file_object: An already opened file object
    :param from_file_path: The file path of the file to be copied
    :param heading_level: The current heading level of the document
    :param from_file_object: An already opened file object to be copied into the to_file_object
    """
    if DEBUG:
        DEBUG_FILE.write("Copying file contents to a file\n")
    starting_level = heading_level
    if not from_file_path and not from_file_object:
        raise ValueError("A path or file object needs to be specified")
    elif from_file_path and from_file_object:
        raise ValueError("Cannot specify a path and an object.")
    if from_file_path:
        with open(from_file_path) as file:
            for line in file:
                heading_level = get_heading_level(line)
                if heading_level:
                    line = adjust_heading_level(line, starting_level + heading_level - 1)
                to_file_object.write(line)
    elif from_file_object:
        from_file_object.seek(0)
        for line in from_file_object:
            heading_level = get_heading_level(line)
            if heading_level:
                line = adjust_heading_level(line, starting_level + heading_level - 1)
            to_file_object.write(line)
    to_file_object.write('\n\n')


def get_heading_level(line):
    line = line.strip()
    if line.__len__():
        return line.split()[0].count('#')
    return 0


def adjust_heading_level(line, heading_level):
    return '#' * heading_level + " " + line.strip().strip('#').strip() + " " + '#' * heading_level + '\n'


def get_keys_starting_with(keys_dictionary, starts_with):
    return [key for key in keys_dictionary.keys() if key.startswith(starts_with.upper())]


def get_other_keys(keys_dictionary, supported_actors):
    return [key for key in keys_dictionary.keys() if keys_dictionary[key]["actors"] not in supported_actors]


def create_single_markdown(output_file_path, keys_dict, key_detail_files, verbosity, build):
    if DEBUG:
        DEBUG_FILE.write("Creating single markdown file\n")
    output_file = open(output_file_path, mode="w+")
    heading_level = 1

    # Add YAML Header to define output format
    yaml = ["---",
            "documentclass: extarticle",
            "toc: yes",
            "toc-depth: 4",
            "title: BAMKey Documentation",
            "mainfont: \"Roboto\"",
            "monofont: \"Roboto Mono\"",
            "fontsize: 12pt",
            "geometry: \"hmargin=.75in,vmargin=.75in\"",
            "linkcolor: Blue",
            "graphics: yes",
            "logo: \"details/images/logo.png\"",
            "build: \"" + build + "\"",
            "recent-changes: \"" + FILE_PATHS["commit_log"] + "\"",
            "...\n\n"]

    output_file.write("\n".join(yaml))
    # 'P': 'Pump',
    # 'F': 'Foundation',
    # 'O': 'Outlet',
    # 'S': 'SIQ',
    # 'T': 'Thump-pump',
    # 'A': 'Audio-in',
    # 'D': 'Dual-temp'
    actor_delimiters = ['P', 'F', 'O', 'S', 'A', 'D']   # Thump-pump isn't going to be in it's own section
    actors_dict = get_actors_dict(keys_dict)

    # Write the introduction
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['introduction'])

    # Write the SleepIQ Section with Keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['siq'])
    siq_keys = actors_dict['S']
    write_key_descriptions(keys_dict, siq_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Pump Section with keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['pump'])
    pump_keys = actors_dict['P']
    write_key_descriptions(keys_dict, pump_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Foundation Section with keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['foundation'])
    foundation_keys = actors_dict['F']
    write_key_descriptions(keys_dict, foundation_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Dual-temp Section with Keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['dual-temp'])
    dual_temp_keys = actors_dict['D']
    write_key_descriptions(keys_dict, dual_temp_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Audio-in Section with keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['audio-in'])
    audio_in_keys = actors_dict['A']
    write_key_descriptions(keys_dict, audio_in_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Outlet Section with Keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['outlet'])
    outlet_keys = actors_dict['O']
    write_key_descriptions(keys_dict, outlet_keys, output_file, heading_level + 1, key_detail_files)

    # Write the Other Section with Keys
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['other'])
    other_keys = get_other_keys(keys_dict, actor_delimiters)
    write_key_descriptions(keys_dict, other_keys, output_file, heading_level + 1, key_detail_files)

    # Write the keys list table to the file
    output_file.write("\\newpage\n")
    copy_file_to_current_file(output_file, heading_level, from_file_path=FILE_PATHS['keys_list'])
    write_keys_list(keys_dict, output_file)
    if DEBUG:
        DEBUG_FILE.write("Finished creating single markdown\n")


def write_keys_list(keys_dictionary, output_file_object):
    if DEBUG:
        DEBUG_FILE.write("Writing Keys list to output file\n")
    output_file = output_file_object
    keys_dict = keys_dictionary

    keys_heading = ["Key", "Description", "Mode", "Calling", "Actors", "G", "1", "2", "3", "Type"]
    output_file.write(table_heading(keys_heading))
    keys_list = sorted(keys_dict.keys())
    for current_key in keys_list:
        output_description = keys_dict[current_key]['description']
        output_key = link_key(current_key)

        output_mode = parse_mode(keys_dict[current_key]['mode'])
        output_calling = parse_calling(keys_dict[current_key]['calling'])
        output_actors = parse_actors(keys_dict[current_key]['actors'])

        supported_pumps = keys_dict[current_key]['pump_types']
        output_pumps = [' ', ' ', ' ', ' ']
        for pump in sorted(supported_pumps):
            check_mark = '•'
            if pump == 'G':
                output_pumps[0] = check_mark
            elif pump in ['1', '2', '3']:
                output_pumps[int(pump)] = check_mark
            elif pump == 'X':
                output_pumps = [check_mark, check_mark, check_mark, check_mark]
        output_pumps = ' | '.join(output_pumps)

        command_type = keys_dict[current_key]['command_type']
        if type(command_type) is dict:
            output_command_type = []
            for item in command_type.values():
                output_command_type.append(parse_command_type(item))
            output_command_type = ', '.join(output_command_type)
        else:
            output_command_type = parse_command_type(command_type)

        current_row = [output_key, output_description, output_mode, output_calling, output_actors, output_pumps,
                       output_command_type]
        output_file.write(table_row(current_row))


def write_key_descriptions(keys_dictionary, keys_to_write, file_object, current_heading_level, key_detail_files):
    if DEBUG:
        DEBUG_FILE.write("Writing key descriptions to file\n")
    for current_key in sorted(keys_to_write):
        if DEBUG: 
            DEBUG_FILE.write("Writing " + current_key + "\n")
        output_description = keys_dictionary[current_key]['description']
        output_mode = parse_mode(keys_dictionary[current_key]['mode'])
        output_calling = parse_calling(keys_dictionary[current_key]['calling'])
        output_actors = parse_actors(keys_dictionary[current_key]['actors'])

        command_type = keys_dictionary[current_key]['command_type']

        link_to_key = '<span id="' + current_key + '"></span>\n\n'
        title = ' '.join(word[0].upper() + word[1:] for word in output_description.split())
        file_object.write(link_to_key + adjust_heading_level(title, current_heading_level))

        file_object.write("* __Key:__ " + current_key + "\n")
        file_object.write("* __Mode:__ " + output_mode + "\n")
        file_object.write("* __Calls:__ " + output_calling + "\n")
        file_object.write("* __Actors:__ " + output_actors + "\n")

        supported_pumps = keys_dictionary[current_key]['pump_types']
        output_supported_pumps = ', '.join([parse_supported_pump(pump)for pump in supported_pumps])
        file_object.write("* __Supported Pumps:__ " + output_supported_pumps + "\n")

        if type(command_type) is dict:
            file_object.write("* __Key Type:__\n")
            for pump in command_type.keys():
                file_object.write(
                    " + __" + parse_supported_pump(pump) + "__: " + parse_command_type(command_type[pump]) + "\n")
        else:
            file_object.write("* __Key Type:__ " + parse_command_type(command_type) + "\n")

        required = keys_dictionary[current_key]['required']
        if type(required) is dict:
            file_object.write("* __Required:__\n")
            for pump in required.keys():
                file_object.write("  + __" + parse_supported_pump(pump) + "__: " + parse_required(required[pump]) + "\n")
        else:
            output_required = parse_required(required)
            if output_required not in ['n/a']:
                file_object.write("* __Required:__ " + parse_required(required) + "\n")

        help_text = keys_dictionary[current_key]['help_text']
        if type(help_text) is dict:
            file_object.write("* __Help Text:__ \n")
            for pump in help_text.keys():
                file_object.write("  + __" + parse_supported_pump(pump) + "__: `" + help_text[pump].strip() + "`\n")
        else:
            file_object.write("* __Help Text:__ `" + help_text.strip() + "`\n")

        related_commands = keys_dictionary[current_key]['related_commands']
        if type(related_commands) is dict:
            file_object.write("* __Related Keys:__ \n")
            for pump in related_commands.keys():
                linked_commands = ", ".join([link_key(related) for related in sorted(related_commands[pump])])
                file_object.write("  + __" + parse_supported_pump(pump) + "__: " + linked_commands + "\n")
        else:
            if related_commands[0] not in ['----', '']:
                linked_commands = ", ".join([link_key(related) for related in sorted(related_commands)])
                file_object.write("* __Related Keys:__ " + linked_commands + "\n")
        file_object.write('\n')

        copy_file_to_current_file(file_object, current_heading_level + 1, from_file_object=key_detail_files[current_key])
    if DEBUG:
        DEBUG_FILE.write("Finished writing key descriptions\n")


def parse_git_log(file_path):
    if DEBUG:
        DEBUG_FILE.write("Parsing git log file " + file_path + "\n")
    git_log_file = open(file_path, mode="r+")
    current_commit = {}
    git_log = []
    first_blank_line = False
    for line in git_log_file:
        if line.startswith("commit"):
            current_commit["commit"] = line.lstrip("commit").strip()
        elif line.startswith("Author:"):
            author_line = line.lstrip("Author:").strip().split("<")
            current_commit["author"] = author_line[0].strip()
            current_commit["email"] = author_line[1].strip().rstrip('>')
        elif line.startswith("Date:"):
            current_commit["date"] = datetime.strptime(line.lstrip("Date:").strip(), "%c %z")
        elif line.strip() == "":
            if first_blank_line is False:
                first_blank_line = True
            elif first_blank_line is True:
                git_log.append(copy.deepcopy(current_commit))
                current_commit = {}
                first_blank_line = False
        elif line.startswith("    "):
            if "message" in current_commit.keys():
                current_commit["message"] = current_commit["message"] + " " + line
            else:
                current_commit["message"] = line
    git_log.append(copy.deepcopy(current_commit))
    git_log_file.close()
    return git_log


def get_git_details_log(n=0):
    if DEBUG:
        DEBUG_FILE.write("Getting git log for details folder\n")
    file_path = "get_log.txt"

    if n == 0:
        os.system("git log details > " + file_path)
    elif n == -1:
        os.system("git log > " + file_path)  # Used for seeing all changes to documentation
    elif n < -1:
        os.system("git log -n " + n.__abs__().__str__() + " > " + file_path)  # Used for n changes to documentation
    else:
        os.system("git log -n " + n.__str__() + " details > " + file_path)

    git_log = parse_git_log(file_path)
    os.system("rm " + file_path)
    return git_log


def get_svn_details_log(n=0):
    if DEBUG:
        DEBUG_FILE.write("Getting SVN log for details folder\n")
    file_path = "svn_log.txt"
    if n == 0:
        os.system("svn log details > " + file_path)
    else:
        os.system("svn log -l " + n.__str__() + " details > " + file_path)
    svn_log = parse_svn_log(file_path)
    os.system("rm " + file_path)
    return svn_log


def parse_svn_log(file_path):
    if DEBUG:
        DEBUG_FILE.write("Parsing SVN log file " + file_path + "\n")
    svn_log_file = open(file_path, mode="r+")

    # Convert svn user names to display names
    svn_names_file = open("svn_names.txt", mode="r+")
    svn_names = {}
    for line in svn_names_file:
        if line.startswith("#"):
            continue
        split_line = line.strip().split(",")
        svn_names[split_line[0].strip()] = {"display": split_line[1].strip(), "email": split_line[2].strip()}

    current_commit = {}
    svn_log = []
    found_info_line = False
    for line in svn_log_file:
        if re.search("(r(\d)+ )", line) is not None and not found_info_line:
            found_info_line = True
            split_line = line.strip().split("|")
            current_commit["commit"] = split_line[0].strip()
            current_commit["author"] = svn_names[split_line[1].strip()]["display"]
            current_commit["email"] = svn_names[split_line[1].strip()]["email"]
            current_commit["date"] = datetime.strptime(split_line[2].strip().split('(')[0].strip(),
                                                       "%Y-%m-%d %H:%M:%S %z")
        elif line.startswith("------------------------------------------------------------------------"):
            if current_commit.__len__():
                svn_log.append(copy.deepcopy(current_commit))
            found_info_line = False
            current_commit = {}
        elif line.strip() == '':
            continue
        else:
            if "message" in current_commit.keys():
                current_commit["message"] = current_commit["message"] + " " + line
            else:
                current_commit["message"] = line
    if current_commit.__len__():
        svn_log.append(copy.deepcopy(current_commit))
    svn_log_file.close()
    return svn_log


def escape_latex(input_string):
    escaped = input_string.translate(str.maketrans({"&": r"\&",
                                                    "%": r"\%",
                                                    "$": r"\$",
                                                    "#": r"\#",
                                                    "_": r"\_",
                                                    "{": r"\{",
                                                    "}": r"\}",
                                                    "~": r"\textasciitilde",
                                                    "\\": r"\textbackslash",
                                                    "^": r"\textasciicircum"}))
    return escaped


def write_log_table_tex(commit_log, file_path=FILE_PATHS["commit_log"]):
    if DEBUG:
        DEBUG_FILE.write("Writing commit log " + file_path + " to latex\n")
    message_len = 130
    commit_log_file = open(file_path, mode="w+")
    commit_log_file.write("\\begin{tabulary}{0.8\\textwidth}{p{5em} p{9em} L}\n Date & Author & Commit Message "
                          "\\\\\n\hline\n")
    for entry in commit_log:
        message = entry["message"].strip()
        if message.__len__() > message_len:
            message = "\\tooltip[Black]{" + escape_latex(message[:message_len]) + \
                      "...}[ProcessBlue!20]{\parbox[t][][t]{3in}{\\raggedright " + \
                      escape_latex(message).replace("\n", "\\\\") + "}} "
        else:
            message = message.replace("\n", " ")

        author = "\\tooltip[Black]{" + escape_latex(entry["author"]) + \
                 "}[ProcessBlue!20]{ " + escape_latex(entry["email"]) + "} "

        date = "\\tooltip[Black]{" + escape_latex(entry["date"].strftime("%x")) + "}[ProcessBlue!20]{" + \
               escape_latex("Commit: " + entry["commit"]) + "} "

        git_table_row = [date, author, message]
        commit_log_file.write(" & ".join(git_table_row) + "\\\\\n")
    commit_log_file.write("\end{tabulary}\n")


def upload_to_google_drive(file_path, build):
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    if DEBUG:
        DEBUG_FILE.write("STARTING GDRIVE UPLOAD FUNCTION\nUploading " + file_path + " to Google Drive.\n")
        DEBUG_FILE.write("Starting Authentication\n")
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)
    if DEBUG:
        DEBUG_FILE.write("Finished Authentication\n")

    # Get the ID of the BAM Key folder, or create one if it doesn't exist
    bamkey_folder_id = None
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    if DEBUG:
        DEBUG_FILE.write("Finding bamkey folder id\n")

    for file in file_list:
        if file['mimeType'].find('folder') > -1 and file['title'] == 'BAM Keys':
            bamkey_folder_id = file['id']
    if bamkey_folder_id is None:
        if DEBUG:
            DEBUG_FILE.write("bamkey folder doesn't exist. Creating new folder\n")

        bamkey_folder = drive.CreateFile({'title': "BAM Keys",
                                          "parents": [{"id": id}],
                                          "mimeType": "application/vnd.google-apps.folder"})
        bamkey_folder.Upload()
        bamkey_folder_id = bamkey_folder['id']

    # Get a list of files inside of the BAM Key folder
    file_list = drive.ListFile({'q': "'" + bamkey_folder_id + "' in parents and trashed=false"}).GetList()

    # Delete all of the instances of file_path and the folder "Archive"
    archive_folder_id = None
    for file in file_list:
        if file['mimeType'].find('pdf') > -1 and file['title'] == file_path.strip(".pdf"):
            file.Delete()
        if file['mimeType'].find('folder') > -1 and file['title'] == 'Archive':
            archive_folder_id = file['id']

    # Upload file to BAM Keys
    new_pdf = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": bamkey_folder_id}]})
    new_pdf.SetContentFile(file_path)
    new_pdf['title'] = new_pdf['title'].strip('.pdf')

    ################
    # Archive Code #
    ################

    # Create archive folder if it doesn't exist
    if archive_folder_id is None:
        archive_folder = drive.CreateFile({'title': "Archive",
                                           "parents": [{"id": bamkey_folder_id}],
                                           "mimeType": "application/vnd.google-apps.folder"})
        archive_folder.Upload()
        archive_folder_id = archive_folder['id']

    # Get a list of files inside of the Archive folder
    file_list = drive.ListFile({'q': "'" + archive_folder_id + "' in parents and trashed=false"}).GetList()

    # Delete all of the files matching the name of the new documentation
    archive_file_name = file_path.strip(".pdf") + "-" + build
    for file in file_list:
        if file['mimeType'].find('pdf') > -1 and file['title'] == archive_file_name:
            file.Delete()

    # Upload new PDF to old for archival
    archive_pdf = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": archive_folder_id}]})
    archive_pdf.SetContentFile(file_path)
    archive_pdf['title'] = "" + file_path.strip(".pdf") + "-" + build

    # Upload all of the files
    if DEBUG:
        DEBUG_FILE.write("Uploading files to GDrive\n")
    new_pdf.Upload()
    archive_pdf.Upload()


def upload_to_dropbox(file_path, build, token):
    import dropbox

    if DEBUG:
        DEBUG_FILE.write("STARTING DROPBOX UPLOAD FUNCTION\nUploading " + file_path + " to Dropbox.\n")
        DEBUG_FILE.write("Starting Authentication\n")

    dropbox_client = dropbox.Dropbox(token)

    with open(file_path, mode='rb') as file:
        dropbox_client.files_upload(file.read(), "/BAMKeys.pdf", mode=dropbox.files.WriteMode("overwrite"))

    with open(file_path, mode='rb') as archive_file:
        dropbox_client.files_upload(archive_file.read(), "/Archive/BAMKeys-" + build + ".pdf",
                                    mode=dropbox.files.WriteMode("overwrite"))


def argument_parsing():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand")

    # sub parser for generate files
    parser_generate = subparsers.add_parser('generate')
    parser_generate.add_argument("-i", "--input", required=True, help="input BIO file")
    version_control = parser_generate.add_mutually_exclusive_group()
    version_control.add_argument("-s", "--svn", action='store_true', help="Use SVN to commit new files")
    version_control.add_argument("-g", "--git", action='store_true', help="Use git to commit new files")
    parser_generate.add_argument("-v", "--verbosity", action="count", default=0)
    parser_generate.add_argument("--DEBUG", action="store_true")

    # sub parser for markdown output
    parser_markdown = subparsers.add_parser('markdown')
    parser_markdown.add_argument("-i", "--input", required=True, help="input BIO file")
    parser_markdown.add_argument("-o", "--output", required=True, help="output file")
    parser_markdown.add_argument("-v", "--verbosity", action="count", default=0)
    parser_markdown.add_argument("--DEBUG", action="store_true")

    # sub parser for PDF output
    parser_pdf = subparsers.add_parser('pdf')
    parser_pdf.add_argument("-i", "--input", required=True, help="input BIO file")
    parser_pdf.add_argument("-o", "--output", required=True, help="output file")
    parser_pdf.add_argument("-b", "--build", default="DEBUG", help="Build that documentation is being generated for")

    parser_pdf.add_argument("-u", "--upload", action='store_true', default=False,
                            help="Upload the generated PDF to Teams. default=False")
    parser_pdf.add_argument('-t', "--token", help="Dropbox API Token")

    version_control = parser_pdf.add_mutually_exclusive_group(required=True)
    version_control.add_argument("-s", "--svn", action='store_true', help="Use SVN version control for changes list")
    version_control.add_argument("-g", "--git", action='store_true', help="Use git version control for changes list")
    parser_pdf.add_argument("-v", "--verbosity", action="count", default=0)
    parser_pdf.add_argument("--DEBUG", action="store_true")

    # Parse the arguments
    args = parser.parse_args()

    # Set the global debug flag constant and open the file
    global DEBUG
    DEBUG = args.DEBUG
    if DEBUG:
        global DEBUG_FILE
        DEBUG_FILE = open(FILE_PATHS["debug"], mode="w+")

    return args


def main():
    args = argument_parsing()
    # Parse Bio for all keys and get a list of all the key files
    if args.verbosity:
        print("Parsing bio for key information")
    parsed_keys = parse_bio(args.input)
    if args.verbosity:
        print("Opening all key details files and store file objects for later use")
    key_detail_files = get_detail_files(parsed_keys, args.verbosity)
    if args.subcommand == "generate":
        if args.verbosity:
            print("Committing any new details files to version control")
        if args.svn:
            os.system("svn add details/*")
        elif args.git:
            os.system("git add details/*")
    elif args.subcommand == "markdown":
        if args.verbosity:
            print("Creating single markdown file.")
        create_single_markdown(args.output, parsed_keys, key_detail_files, args.verbosity, args.build)
    elif args.subcommand == "pdf":
        # Generate recent changes from commit log of the details folder and store in commit_log.tex
        if args.git:
            if args.verbosity:
                print("Creating recent changes table using git log")
            write_log_table_tex(get_git_details_log(8))
        elif args.svn:
            if args.verbosity:
                print("Creating recent changes table using svn log")
            write_log_table_tex(get_svn_details_log(8))
        # Create single output markdown file
        if args.verbosity:
            print("Creating a single markdown file")
        create_single_markdown(FILE_PATHS["markdown_output"], parsed_keys, key_detail_files, args.verbosity, args.build)
        # Convert single markdown to PDF
        if DEBUG:
            DEBUG_FILE.write("Generating PDF with pandoc\n")
        if args.verbosity:
            print("Converting single markdown file to PDF and saving at " + args.output)
        pandoc_args = ["--from", "markdown+pipe_tables+implicit_figures", "--pdf-engine=xelatex",
                       "--template=\"template.tex\"", "--toc", "-V", "graphics"]
        os.system("pandoc -i " + FILE_PATHS["markdown_output"] + " " + " ".join(pandoc_args) + " -o " + args.output)

        if DEBUG:
            DEBUG_FILE.write("Finished Generating PDF with pandoc\n")
        # Upload new file to dropbox
        if args.upload:
            #if args.verbosity:
            #    print("Uploading " + args.output + " to dropbox")
            # upload_to_dropbox(file_path=args.output, build=args.build, token=args.token)
            if args.verbosity:
                print("Uploading " + args.output + " to google drive")
            upload_to_google_drive(args.output, args.build)



    if DEBUG:
        DEBUG_FILE.close()
    else:
        # Clean up files
        if os.path.isfile(FILE_PATHS["markdown_output"]):
            os.remove(FILE_PATHS["markdown_output"])
        if os.path.isfile(FILE_PATHS["commit_log"]):
            os.remove(FILE_PATHS["commit_log"])
        if os.path.isfile(FILE_PATHS["debug"]):
            os.remove(FILE_PATHS["debug"])


if __name__ == '__main__':
    main()
