#!/usr/bin/env python

"""
//! \brief A simple HTTP server which streams device software files
//! \version v1
//! \copyright Sleep Number Proprietary and Confidential
//! \copyright Protected by Copyright 2018-2019
"""

"""
Usage::
    python dummy_device_software_streaming_server.py [<port(default:8000)>]
Send a POST request::
    curl --max-time 5 --retry 5 --retry-max-time 60 --output /tmp/bam.conf \
    --data "hardwareVersion=175&deviceId=64dba0000144&deviceId2=e0e5cf21ea7e&deviceVersion=500&accountNumber=" \
    http://localhost:8000/bam/device/getConfig.jsp

    curl --max-time 5 --retry 5 --retry-max-time 60 --output /tmp/device_software.zip \
    --data "version=SE_500_zep4_4.7.0_1811151200_GA&deviceId=64dba0000144&deviceId2=e0e5cf21ea7e&deviceVersion=500" \
    http://localhost:8000/bam/device/getSoftware.jsp
"""

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import urlparse
import socket

server_port = 8000


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        print("GET")
        valid = False
        print(self.path)

        if not valid:
            print("not valid")
            self._set_headers()
            self.wfile.write("Unknown GET request")

    def do_HEAD(self):
        print("HEAD")
        self._set_headers()

    def do_POST(self):
        global server_port
        print("POST")
        valid = False
        print(self.path)

        target_dir = os.getcwd() + "/latest"
        applicationVersion = None
        rfsVersion = None
        for filename in os.listdir(target_dir):
            if "SE_500_z" in filename:
                applicationVersion = filename.split('.zip')[0]
            elif "SE_500_rfs" in filename:
                rfsVersion = filename.split('.zip')[0]
        if applicationVersion is None or rfsVersion is None:
            print("Error: no file available to stream")
            self._set_headers()
            self.wfile.write("Error: no file available to stream")
            return

        if 'getSoftware' in self.path:
            length = int(self.headers.getheader('content-length'))
            field_data = self.rfile.read(length)
            if field_data is not None:
                fields = urlparse.parse_qs(field_data)
                if 'version' in fields.keys():
                    softwareVersion = fields['version']
                    softwareVersion = softwareVersion[0]
                    print("getting " + softwareVersion + ".zip file")
                    f = open(target_dir + "/" + softwareVersion + ".zip", "rb")
                    self._set_headers()
                    self.wfile.write(f.read())
                    f.close()
                    valid = True
        elif 'getConfig' in self.path:
            print("getting current software version")
            server_ip = socket.gethostbyname(socket.gethostname())
            self._set_headers()
            self.wfile.write("blohURL   = https://circle1-dg.circle.siq.sleepnumber.com\n" +
                             "blohConnectPath = /bam/requestConnection\n" +
                             "blohUplinkPath = /bam/uplink\n" +
                             "blohDownlinkPath = /bam/downlink\n" +
                             "provisionURL = http://" + server_ip + ":" + str(server_port) + "/bam/device/getSoftware.jsp\n" +
                             "keyURL = https://circle1-dg.circle.siq.sleepnumber.com/bam/device/getFile.jsp\n" +
                             "timeURL = https://circle1-dg.circle.siq.sleepnumber.com/bam/device/getTime.jsp\n" +
                             "pingURL = https://circle1-dg.circle.siq.sleepnumber.com\n" +
                             "syslogServer = devices_log.bamlabs.com\n" +
                             "syslogFacility  = local1\n" +
                             "vpnServer = devices_vpn.bamlabs.com\n" +
                             "tunnelURL = devices.zepp.bamlabs.com\n" +
                             "a2d_report_period = 1\n" +
                             "usb_raw_send = 10000\n" +
                             "usb_filter_send = 0\n")
            self.wfile.write("applicationVersion = " + applicationVersion + '\n')
            self.wfile.write("rfsVersion = " + rfsVersion + '\n')
            valid = True

        if not valid:
            print("not valid")
            self._set_headers()
            self.wfile.write("Unknown POST request")


def run(server_class=HTTPServer, handler_class=S, port=8000):
    global server_port
    server_address = ('', port)
    server_port = port
    httpd = server_class(server_address, handler_class)
    print('Starting dummy device software streaming server...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
