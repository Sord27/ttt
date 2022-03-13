# RAW1k Parsing and Manipulation #

This is a tool used to view and edit raw1k files.

## Requirements ##

* Python 3.5 or later

## How to Use ##

This tool is used by running the following command:

```bash
./raw1k.py <arg> <flags> -i <input_file> -o <output_file>
```

The args and their flags are as follows:

### json ###

**Description:** Using the `dump` tag will parse the input raw1k file, and output the data as a json file in a human readable format.

***Flags:***

| Short |   Long      | Description                                                        |
| :---: | ----------- | ------------------------------------------------------------------ |
|  -i   | --input     | input raw1k file (required)                                        |
|  -o   | --output    | output json file (required)                                        |
|  -t   | --tags      | tags json file used for parsing (default is `tags.json`)           |
|  -v   | --verbosity | changes the logging level according to the number of 'v's          |
|  -f   | --filter    | filters the tags to be outputted to json output file               |
|  -    | --raw       | Flag to turn on raw data output in the json file                   |

**Example:** Running `python3 raw1k.py dump -i raw1k_sample.raw1k -o raw1k_sample.json --raw -f 600 900` will create a human readable json file containing all of the data contained in `raw1k_sample.raw1k`. The process will print all WARNING level messages and higher.

### modify ###

**Description:** Using the `modify` tag will output a `.raw1k` file with the specified changes made.

***Flags:***

| Short |   Long      | Description                                                        |
| :---: | ----------- | ------------------------------------------------------------------ |
|  -i   | --input     | input raw1k file (required)                                        |
|  -o   | --output    | output raw1k file (required)                                       |
|  -t   | --tags      | tags json file used for parsing (default is `tags.json`)           |
|  -d   | --date      | change timestamp dates to YYYY-MM-DD                               |
|  -t   | --time      | change timestamp start time to HH:MM:SS                            |
|  -v   | --verbosity | changes the logging level according to the number of 'v's          |
|  -s   | --start     | specifies the starting time in HH:MM:SS format to start truncation |
|  -e   | --end       | specifies the ending time in HH:MM:SS format to end truncation     |
|  -    | --side      | specifies the which side of the bed to set the raw1k for           |

**Example:** Running `python3 raw1k.py modify -v -d 1999-12-31 -t 12:00:00 -s 23:59:00 -e 00:01:00 -i raw1k_sample.raw1k -o modified_sample.raw1k` will create a `.raw1k` file containing the packets of data between 11:59pm and 12:01am from `raw1k_sample.raw1k` with the timestamps of the original raw1k changed to begin at noon on New Year's Eve, 1999. The process will print all INFO level messages and higher.

### raw ###

**Description:** Using the `raw` tag will parse the input raw1k file, and output only the pressure data in binary format.

***Flags:***

| Short |   Long      | Description                                                        |
| :---: | ----------- | ------------------------------------------------------------------ |
|  -i   | --input     | input raw1k file (required)                                        |
|  -o   | --output    | output raw pressure file (required)                                |
|  -t   | --tags      | tags json file used for parsing (default is `tags.json`)           |
|  -v   | --verbosity | changes the logging level according to the number of 'v's          |

**Example:** Running `python3 raw1k.py raw -vv -i raw1k_sample.raw1k -o raw1k_sample.raw` will create a binary file containing all of the pressure data contained in `raw1k_sample.raw1k`. The process will print all DEBUG level messages and higher.

## Notes ##

* This is a very resource intensive script. It is recommended to have at least 6GB of memory available.
* Completion time varies based on the file. It is normal for the process to last several minutes.
