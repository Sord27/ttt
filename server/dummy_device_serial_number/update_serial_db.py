#!/usr/bin/env python

"""
//! \brief A simple script to update serial_number.db by giving UID and
           serial number.
//! \version v2
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

"""
Usage::
    python update_serial_db.py <UID:16 digits(hex)> <serial_number:12 digits(hex)>"
 Overwrites existing entry:    
    python update_serial_db.py f <UID:16 digits(hex)> <serial_number:12 digits(hex)>"
e.g.
    python update_serial_db.py 150cb1d4e3167a95 cc04b4601038
"""

import sys
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


def delete_from_db(mac):
    conn = sqlite3.connect('serial_number.db')
    c = conn.cursor()
    c.execute("DELETE from serial_number_table WHERE mac=:mac", {"mac": mac})
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



def update_serial_db(UID, serial_number, force):
    UIDlen = len(UID)
    SNlen = len(serial_number)
    if UIDlen == 16 and SNlen == 12:
        if not os.path.isfile('serial_number.db'):
            print("Creating database..")
            create_db()
        UID = int(UID, 16)
        serial_number = int(serial_number, 16)
        print(UID, serial_number)
        if force:
            delete_from_db(UID)
        if ask_db_for_serial_number(UID) is None:
            if write_to_db(UID, serial_number):
                print("Successfully " + str(UID) + ":" +
                      str(serial_number) + " written to serial_number.db")
            else:
                print("Error writing to serial_number.db")
        else:
            print("Found existing entry in the database, try forcefully "
                  "updating it!")
    else:
        usage()

def usage():
    print("python update_serial_db.py <UID:16 digits(hex)> "
          "<serial_number:12 digits(hex)>")
    print("python update_serial_db.py f <UID:16 digits(hex)> "
          "<serial_number:12 digits(hex)>")


def Main():
    if len(sys.argv) == 3 and sys.argv[1].isalnum() and sys.argv[2].isalnum():
        UID = sys.argv[1]
        serial_number = sys.argv[2]
        update_serial_db(UID, serial_number, False)
 
    elif len(sys.argv) == 4 and sys.argv[1] == 'f' and \
            sys.argv[2].isalnum() and sys.argv[3].isalnum():
        UID = sys.argv[2]
        serial_number = sys.argv[3]
        update_serial_db(UID, serial_number, True)

    else:
        usage()


if __name__ == "__main__":
    Main()
