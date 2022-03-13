# Sumo Logic Query 

## This a class to get the result of any Sumo Logic query using python package.

## Requirements:

1- Need Sumo logic accessId and accessKey. To create those two requirements you can follow the instruction on this link from [Sumo logic](https://help.sumologic.com/Manage/Security/Access-Keys) website.

2- You need the Sumo Logic Endpoint URL, to choose one, you can pick the most suitable one for you application from this [Sumo Logic URLs](https://help.sumologic.com/APIs/General-API-Information/Sumo-Logic-Endpoints-and-Firewall-Security).

3- You need to create a file with name “user.json”, the file need to be at the same directory as the main script or you need to modify the script to point to its location, the file should looks like this
```
    {
        "accessId":"replace this value with your accessId you obtained in step 1",
        "accessKey":" replace this value with your accessKey you obtained in step 1",
        "sumo_logic_server" : " replace this value with the URL you obtained in step 2"
    }
```
4- You need to create a txt file named “sumo_query.txt” in the same directory as the main script. This file will contains the Sumo query search string, example; 

    `_sourceXXXX=XXXX/XXXXX/XXXXX AND "L:SCLC_RX_gotPacket[1]: Failed to send message 0x713" | parse "500-* " as mac | count by mac | sort by _count`
    
5- The headers file included. 

## Brief introduction:

The constructor of the class defaults to the previous 12 hours from run time, example; 

        TEST = GetSumoQuery()

However, it can be overloaded to search previous days, hours, minutes and second, also you can specify the number of
records that can be pulled, here some examples;
 
        TEST = GetSumoQuery(5)  -> search up to 5 days backward. 
	    TEST = GetSumoQuery(0, 10) ->  search up to 10 hours backward.
	    TEST = GetSumoQuery(0, 0, 25) -> search up to 25 minutes backward.
	    TEST = GetSumoQuery(0, 0, 0, 35) search up to 35 seconds backward 
	    TEST = GetSumoQuery(2, 7, 15, 10, 100) search backward up to 2 days, 7 hours, 15 minutes, 10 seconds
	                        and limit the number of returned records from the query  to 100.

If you have specific period of time you want to query, after the class is initialized you can use the method
set_time_interval for example;

        TEST.set_time_interval("2020-01-22T00:00:00", "2020-01-24T00:00:00")

The constrain with this method is the date must be in specific format 

	    (Year-Month-DayTHours:Minutes:Seconds) 

Please note the letter “T” must be included on the date format. 


# How to run 
Python3  sumo_query.py 

While the script is waiting for SUMO server to finish processing the query a message “GATHERING RESULTS” will 
keep printing on the screen, once Sumo finishes loading the records a line will be printed on the screen terminal 
“DONE GATHERING RESULTS” indicating the process is complete and your script handles what action to impose on 
the returned records. 



