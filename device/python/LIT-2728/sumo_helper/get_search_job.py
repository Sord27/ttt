# Get query data via search job
# python get_search_job.py --query_source query.sumoql --from_time 1616389259000 --to_time 1616734859000 --output_file result.csv

import argparse
import time

from sumologic import SumoLogic

from helper import read_config, read_sumoql, write_csv_file
from settings import CONFIG, SUMO_CREDENTIALS

parser = argparse.ArgumentParser()
parser.add_argument('-q', '--query_source', help='File with sumologic query')
parser.add_argument('-f', '--from_time', help='Timestamp in milliseconds')
parser.add_argument('-t', '--to_time', help='Timestamp in milliseconds')
parser.add_argument('-o', '--output_file', help='Filename to write result in csv format')
arguments = parser.parse_args()

SUMO_LOGIC_ACCESS_ID = read_config(CONFIG, SUMO_CREDENTIALS)['access_id']
SUMO_LOGIC_ACCESS_KEY = read_config(CONFIG, SUMO_CREDENTIALS)['access_key']

query = read_sumoql(arguments.query_source)
from_time = arguments.from_time
to_time = arguments.to_time
output_file = arguments.output_file

sumo = SumoLogic(SUMO_LOGIC_ACCESS_ID, SUMO_LOGIC_ACCESS_KEY)


def main():
    search_job = sumo.search_job(query, from_time, to_time)
    print('Search_job started')

    while True:
        search_job_status = sumo.search_job_status(search_job)
        status = search_job_status['state']

        if status == 'GATHERING RESULTS':
            print('Waiting for query results...')
            time.sleep(10)
            continue
        elif status == 'DONE GATHERING RESULTS':
            print(status)
            break
        else:
            print(status)

    records = sumo.search_job_records(search_job, 1000)['records']
    if records:
        csv_fields = list(records[0]['map'].keys())
        entries = [x['map'] for x in records]
        write_csv_file(output_file, csv_fields, entries)

        print('Results:')
        for entry in entries:
            print(entry['mac'])
    else:
        print('No devices found for specified time interval')
    return records

if __name__ == '__main__':
    main()
