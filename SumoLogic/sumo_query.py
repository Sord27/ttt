"""
A script to get Sumologic queries and return a list of the MACs found
    for given set of devices
Output file columns:
    |MAC |
"""
import sys
import json
import re
#import logging
from datetime import datetime
from datetime import timedelta
import requests

class GetSumoQuery:
    """ Class to handle sumo logic search """
    def __init__(self, days=0, hours=12, minutes=0, seconds=0, limit=1000):
        """ Constructor to initialize object's variables  """
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.limit = limit
        self.recent_date = ''
        self.older_date = ''
        self.query = self.get_query_string()
        self.get_sumo_access()
        self.time_elapsed()
        self.get_sumo_http_headers()

    def get_query_string(self):
        """ Get the query search string and stored it the query variable  """
        with open('sumo_query.txt', 'r') as query_string:
            self.output = query_string.read()
        return self.output

    def set_record_limit(self, record=1000):
        """ Set the limit of the records returned from the sumo search """
        self.limit = record

    def get_sumo_access(self):
        """ Get the Sumo logic user accessId and access_key"""
        with open('user.json') as json_file:
            data = json.load(json_file)
            self.access_id = data["accessId"]
            self.access_key = data["accessKey"]
            self.sumo_server = data["sumo_logic_server"]

    def time_elapsed(self):
        """Calculate the time difference, default 12 hours
         backward from the current time and date"""
        time_now = datetime.now()
        time_delta = timedelta(days=self.days, hours=self.hours,
                               minutes=self.minutes, seconds=self.seconds)
        datetime_new = time_now - time_delta
        self.recent_date = time_now.strftime("%Y-%m-%dT%H:%M:%S")
        self.older_date = datetime_new.strftime("%Y-%m-%dT%H:%M:%S")

    def set_time_interval(self, older_date, recent_date):
        """Overwrite the time_elapsed method to search for any given period between two dates """
        self.recent_date = recent_date
        self.older_date = older_date
        string_match = re.match(r"(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$)", self.recent_date)
        if string_match is None:
            print("Incorrect date format for the start point")
            sys.exit(0)
        string_match = re.match(r"(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$)", self.older_date)
        if string_match is None:
            print("Incorrect date format for the end point")
            sys.exit(0)

    def get_sumo_http_headers(self):
        """Get the Sumo required 2 headers and cookie settings from external file"""
        with open('headers.json') as json_file:
            data = json.load(json_file)
            self.header1 = data["header1"]
            self.header2 = data["header2"]
            self.cookies = data["cookies"]



    def execute_sumo_query(self):
        """ Three API calls required to complete a Sumo search """
        sumo_api_parameters = json.dumps({"query" : self.query,
                                          "from" : self.older_date,
                                          "to" : self.recent_date,
                                          "timeZone" : "PST",
                                          "rawResultsJson" : "",
                                          "aggregateResultsJson" : "[{\"Hostcount\":1}]",
                                          "searchDescription" : "Cem",
                                          "byReceiptTime": True})

        response = requests.post(self.sumo_server, headers=self.header1, cookies=self.cookies,
                                 data=sumo_api_parameters,
                                 auth=(self.access_id, self.access_key))

        responsedata = json.loads(response.text)
        job_id = responsedata["id"]
        state = "GATHERING RESULTS"
        """ Wait for the search to complete  """
        while state == "GATHERING RESULTS":
            response = requests.get(self.sumo_server +'/' + job_id, headers=self.header1,
                                    cookies=self.cookies, auth=(self.access_id, self.access_key))
            responsedata = json.loads(response.text)
            state = responsedata["state"]
            print(state)

        response = requests.get(self.sumo_server + '/' + job_id +
                                '/records?offset=0&limit=' + str(self.limit),
                                headers=self.header2, auth=(self.access_id, self.access_key))
        result = json.loads(response.text)
        return result

if __name__ == "__main__":
    TEST = GetSumoQuery()
    RESULT = TEST.execute_sumo_query()
    print(json.dumps(RESULT, indent=4, sort_keys=True))



