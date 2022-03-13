#!/bin/bash
for i in {1..50}; do /etc/init.d/networking restart && sleep 15; done
