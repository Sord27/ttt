# Raw1k files post-processing

This script is designed for the analysis of raw1k files converted into JSON. It helps determine exact DSP report sequence numbers that are missing in a raw1k file which should aid in debugging the missing data issue.

## Installation

For the script to work you need a python 3.7+ and to install the required python packages:

```
pip3 install -r requirements.txt
```


## Usage

1. Increase the logging level on the pump so that it logs every sent/generated DSP report.
   * on *fuzion* you can do this by running `redis-cli publish logging:cloud:level 7`.
   * on *legacy* you have to modify [this condition](https://github.com/bam-labs/bammit/blob/9d81687faa5907c1221e40918c2f80e3fda2b0cc/bammit/data.c#L1081) and install the customized build onto a pump.
2. Turn on raw1k logging by checking *Send Raw Data* and *Write to raw file* in the OPS portal. 
3. Leave the pump for one full day to gather the necessary data. Please, note that the script analyses raw1k files, and they start at 7 PM UTC.
4. Download the raw1k and pump log files. It is best to concatenate pump log files into a signle one.
5. Convert raw1k files into JSON using [the raw1k script](../DEVICE-227/) like so:  
`python3 ../DEVICE-227/raw1k.py dump -i RAW1K_FILENAME -o JSON_FILENAME -t ../DEVICE-227/tags.json`

   Substitute `RAW1K_FILENAME` and `JSON_FILENAME` as you see fit.

6. Substitute `JSON_FILENAME` and `PUMP_LOG_FILENAME` as you see fit and run the script.
   It will produce useful messages on which exactly DSP report sequence numbers are missing, so you might want save the output into a file by appending ` | tee JSON_FILENAME.log` to the command.
   * on *fuzion*:  
`python3 raw1k_analyse.py cmp_dsp --fuzion JSON_FILENAME PUMP_LOG_FILENAME`
   * on *legacy*:  
`python3 raw1k_analyse.py cmp_dsp JSON_FILENAME PUMP_LOG_FILENAME`

## Produced Output

The script will output messages like these:
  * `invalid DSP ts -1, skipping` means that there was a DSP report with a timestamp equal to -1. The script drops theese reports as they can't possibly be valid.
  * `missed DSP #1622068247 @ 2021-06-03 07:33:22.879000+00:00: (0, 7, 1622705602.879)` means that there was a DSP report with sequence number `1622068247` in the pump log file, but it is absent in the raw1k file. `2021-06-03 07:33:22.879000+00:00` tells the UTC time of that DSP report.

The script will produce filenames by appending a suffix to `JSON_FILENAME`:
  * `CMP_DSP.jumped_seqno.png` is a bar plot that shows the time of DSP sequence number jumps (if any).
  * `CMP_DSP.png` is a bar plot that shows the number of missing DSP reports at given time slots. `Max (640)` on the Y axis tells the size of a time slot in seconds.
  * `CMP_DSP.timediff.png` is a scatter plot that shows time difference between adjacent DSP reports.
