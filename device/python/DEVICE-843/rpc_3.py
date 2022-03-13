"""
Rebooting the Sleep Expert hardware module
"""
import sys
import csv
import json
import requests


def send_rpc_command(mac_list, server, boson_server, backend_server_username,\
                     backend_server_password, boson_user, boson_password):
    """
    Check the status of each MAC in Boson server connected/disconnected
    Send the RPC commands to reboot the Sleep expert
    """

    get_unix_command = None
    disconnected_mac = []
    connected_mac = []
    medui_session = requests.session()
    boson_session = requests.session()

    medui_login_header = {
        "login": backend_server_username,
        "password": backend_server_password
    }
    bosonlogin = {"login": boson_user, "password": boson_password}
    json_headers = {'content-type': 'application/json', 'Accept-Version': '3.5'}

    try:
        response = medui_session.put(server + "/rest/login",\
                                     json=medui_login_header, headers=json_headers)
        data = json.loads(response.text)
        if response.status_code != 200:
            print("Cannot communicate with MEDUI server exiting script ")
            sys.exit(1)
        medui_token = data["key"]

        response = boson_session.put(boson_server + "/rest/boson/login",\
                                     json=bosonlogin, headers=json_headers)
        data = json.loads(response.text)
        if response.status_code != 200:
            print("Cannot communicate with MEDUI server exiting script ")
            sys.exit(1)
        boson_token = data["access_token"]

    except requests.exceptions.RequestException as exception_error:
        print("Unknown exception terminating script...", exception_error)
        sys.exit(1)

    with open('command.json') as json_file:
        data = json.load(json_file)
        get_unix_command = data["unixCommand"]

    for mac in mac_list:
        response = boson_session.get(boson_server + "/rest/boson/device/" + mac + \
                                     "/status?access_token=" + boson_token)
        data = json.loads(response.text)
        if response.status_code != 200 or data["isDeviceOnline"] == False:
            disconnected_mac.append(mac)
            print(mac, "... not reachable through Boson :: Skipped.")
            continue

        send_unix_command = {"macAddress" : mac, "unixCommand" : get_unix_command}
        response = medui_session.post(server + "/rest/bed/rpc?_k=" + medui_token,\
                                      json=send_unix_command, headers=json_headers)
        if response.status_code != 200:
            disconnected_mac.append(mac)
            print(mac, "is not in MEDUI database :: Skipped.")
            continue
        print("Command send successfully to MAC::", mac)
        connected_mac.append(mac)

    with open('disconnected.csv', "w") as output:
        writer = csv.writer(output, lineterminator=',')
        for val in disconnected_mac:
            writer.writerow([val])

    with open('connected.csv', "w") as output:
        writer = csv.writer(output, lineterminator=',')
        for val in connected_mac:
            writer.writerow([val])


def main():
    """
    Initialize required credentials for MEDUI and Boson servers’ accesses.
    Initialize a list with MACs addresses from external input file.
    Call the send_rpc_command.
    """

    with open('Secret.json') as json_file:
        data = json.load(json_file)
    server = data["server"]
    boson_server = data["bosonServer"]
    backend_server_username = data["backendServer_UserName"]
    backend_server_password = data["backendServer_Password"]
    boson_user = data["boson_User"]
    boson_password = data["boson_Password"]
    input_file = sys.argv[1]
    mac_list = []

    with open(input_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            mac_list.append(row[0])

    send_rpc_command(mac_list, server, boson_server, backend_server_username, \
                     backend_server_password, boson_user, boson_password)

if __name__ == '__main__':
    main()
