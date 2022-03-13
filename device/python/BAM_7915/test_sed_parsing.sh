#!/usr/bin/env bash

STRING="Dec 15 00:57:26 500-64dba000002e bamid[10135]: SE_500_zep4_4.3.0_1711301200 <circle1-dg> data_fill_pump_status: Pump2Serv Info<00000001 p 00 f 30 n 050 a 045> fpos<h 062 f 000> ra<0> fw<0>"

echo "$STRING" | sed -rn "s/(.*) 500-([A-Fa-f0-9]{12}).*(Pump2Serv|Pump2Algo).*(0000000[01]).*f ([0-9]{2}) n.*fpos.h ([0-9]{3}) f ([0-9]{3}).*/\2\t\3\t\4\t\1\t\5\t\6\t\7/p"
