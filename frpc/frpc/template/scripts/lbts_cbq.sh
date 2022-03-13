#!/bin/bash
bamio -k LBTS -K 1

/etc/init.d/syslog stop
rm -rf /var/log/boson-queue.*
/etc/init.d/syslog start

tunnel start &
