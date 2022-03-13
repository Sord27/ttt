#!/usr/bin/env python

"""
//! \brief A simple script to show all entries in serial_number.db database
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

"""
Usage::
    python show_serial_db.py
"""

import sqlite3
import os


def show_serial_db():
    conn = sqlite3.connect('serial_number.db')
    c = conn.cursor()
    c.execute("SELECT * from serial_number_table")
    data = c.fetchall()
    if data is not None:
        print("         UID             serial_number      ")
        for d in data:
            uid = hex(d[0])
            sn = hex(d[1])
            print(uid, sn)
    else:
        print("No data in serial_number.db")


def Main():
    if not os.path.isfile('serial_number.db'):
        print("There is no serial_number.db to look for!")
    else:
        show_serial_db()


if __name__ == "__main__":
    Main()
