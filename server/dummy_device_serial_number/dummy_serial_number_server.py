#!/usr/bin/env python

"""
//! \brief A simple HTTP server which provides unique serial number based on
//!        given MAC in POST request for legacy(SP1, SP2, GVB) devices.
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

"""
Usage::
    python dummy_serial_number_server.py [<port(default:8000)>]
Send a GET request::
    curl http://localhost:8000
    wget -T 10 "http://localhost:8000/SETest/getMAC?UID=381a79d4e3172692" -o tmpLog.txt -O tmp.txt
Send a HEAD request::
    curl -I http://localhost:8000
Send a POST request::
    curl -d "UID=381a79d4e3172700" http://localhost:8000/SETest/getMAC
    wget -T 10 "http://localhost:8000/SETest/getMAC" --post-data="UID=381a79d4e3172692" -o tmpLog.txt -O tmp.txt
"""

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
import sqlite3
import os


def create_db():
    conn = sqlite3.connect('serial_number.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE serial_number_table
                 (mac number, serial_no number)''')
    conn.commit()
    conn.close()


# Convert file serial_number.db to SQL dump file dump_serial_number.sql
def convert_to_sql_dump():
    con = sqlite3.connect('serial_number.db')
    with open('dump_serial_number.sql', 'w') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)


def write_to_db(mac, serial_number):
    conn = sqlite3.connect('serial_number.db')
    c = conn.cursor()
    c.execute("INSERT INTO serial_number_table VALUES (?, ?)", (mac, serial_number))
    conn.commit()
    conn.close()
    return True


def ask_db_for_serial_number(mac):
    conn = sqlite3.connect('serial_number.db')
    c = conn.cursor()
    c.execute("SELECT * from serial_number_table WHERE mac=:mac", {"mac": mac})
    data = c.fetchone()
    if data is not None:
        serial_number = data[1]
        print("serial_no from db: " + str(hex(serial_number)))
        return serial_number
    else:
        return None


def handle_serial_numbers(mac):
    mac = int(mac, 16)
    serial_number = ask_db_for_serial_number(mac)

    if serial_number is None:
        # Get serial count from a file
        with open('serial_count.txt') as f:
            file_str = f.read()

        try:
            new_no = int(file_str) + 1
            file_str = str(new_no)
            serial_number = 0xcc04b4800000 + new_no
            write_to_db(mac, serial_number)
            serial_number = str(hex(serial_number))
            serial_number = serial_number[2:14]

            # Update serial_count file
            with open('serial_count.txt', "w") as f:
                f.write(file_str)
            return serial_number

        except:
            print("Got exception in getting serial number")
            return None
    else:
        serial_number = str(hex(serial_number))
        serial_number = serial_number[2:14]
        return serial_number


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        # Based on given mac, send serial number...
        valid = False
        bits = urlparse.urlparse(self.path)
        field_data = bits.query
        if field_data != '':
            fields = urlparse.parse_qs(field_data)
            if 'UID' in fields.keys():
                mac = fields['UID']
                mac = mac[0]
                maclen = len(mac)
                if maclen == 16 and mac.isalnum():
                    serial_number = handle_serial_numbers(mac)
                    print(mac, serial_number)
                    self._set_headers()
                    self.wfile.write("MAC=" + serial_number)
                    valid = True
        if not valid:
            self._set_headers()
            self.wfile.write("Unknown GET request")

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Based on given mac, send serial number...
        valid = False
        length = int(self.headers.getheader('content-length'))
        field_data = self.rfile.read(length)
        if field_data is not None:
            fields = urlparse.parse_qs(field_data)
            if 'UID' in fields.keys():
                mac = fields['UID']
                mac = mac[0]
                maclen = len(mac)
                if maclen == 16 and mac.isalnum():
                    serial_number = handle_serial_numbers(mac)
                    print(mac, serial_number)
                    self._set_headers()
                    self.wfile.write("MAC=" + serial_number)
                    valid = True
        if not valid:
            self._set_headers()
            self.wfile.write("Unknown POST request")


def run(server_class=HTTPServer, handler_class=S, port=8000):
    if not os.path.isfile('serial_number.db'):
        print("Creating database..")
        create_db()

    if not os.path.isfile('serial_count.txt'):
        print("Creating serial count file..")
        with open('serial_count.txt', "w") as f:
                f.write("0")

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting dummy serial_number server...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
