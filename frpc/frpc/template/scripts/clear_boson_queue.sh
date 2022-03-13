#!/bin/bash
/etc/init.d/syslog stop
rm -rf /var/log/boson-queue.*
/etc/init.d/syslog start

tunnel start &
