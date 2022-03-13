# Sumologic search job script


## Installation

Use the package manager [pip](https://pypi.org/project/sumologic-sdk/) to install sumologic-sdk/.

```bash
pip3 install sumologic-sdk
```

## Getting Sumologic API credentials
1. Open preferences page (https://service.us2.sumologic.com/ui/#/preferences)
2. Find 'My Access Keys' section and generate credentials via '+ Add Access Key' button
3. Copy 'access_id' and 'access_key' to corresponding lines of config.ini file 


## Usage

```
-q, --query_source     File with sumologic query
-f, --from_time        Timestamp in milliseconds
-t, --to_time          Timestamp in milliseconds
-o, --output_file      Filename to write result in csv format

python3 get_search_job.py --q query1.sumoql -f 1616043659000 -t 1616734859000 -o result.csv
python3 get_search_job.py --query_source query2.sumoql --from_time 1616043659000 --to_time 1616734859000 --output_file result.csv

```
