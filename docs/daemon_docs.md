NMEAd and SBScan documentation
==============================

**TODO: Document the interface format**

NMEAd
-----

NMEAd is a json interface to sounder and GPS nmea data coming over two
separate serial ports. NMEAd is not itself a daemon but should be run as one
using upstart or an equivalent tool. It reads NMEA through two serial ports,
parses it and presents the data as specified in nmea_templates and this
document. The presentation format shouldn't be altered except if additional
data is required. The json data is saved in a file.

Program should be run as follows:
NMEAd.py [--config CONFIG_FILE] [--logfile LOG_FILE]

Both the parameters are optional. If ommited, the config defaults to 
*'/etc/nmead.conf'* and logfile defaults to *'/var/log/nmead.log'*.

When run, it is neccessary that NMEAd have the permissions to access serial
ports, read the config file and write to log and json files. It is recommended
that a separate user be created to run NMEAd.

The config file is of standard python ConfigParser format and should contain
the following sections and options:

[writer]
output_file:*PATH_TO_JSON_FILE* *(required)*

[sounder]
port:*PATH_TO_SERIAL_PORT* *(required)*
baud:*BAUD_RATE* *(default: 4800)*
disable_nmea:*INFO_LIST* *(default: None)*
check_checksums:*True|False* *(default: False)*

[gps]
port:*PATH_TO_SERIAL_PORT* *(required)*
baud:*BAUD_RATE* *(default: 4800)*
disable_nmea:*INFO_LIST* *(default: None)*
check_checksums:*True|False* *(default: False)*

If any of the required parameters are missing, NMEAd will fail to run. 
Parameter description

*output_file* - absolute path to json file
*port* - absolute path to the serial port device file
*disable_nmea* - comma separated list of nmea parameters explicitely
                 excluded from the json files
*check_checksum* - if 'True', NMEAd checks nmea sentence checksums 


SBScan
------

Most of the above applies to SBScan as well. It is a logging daemon that
connects to NMEAd by a common json file, respecting the POSIX advisory
file locks. The command line syntax is the same, and the default values
for config files and log files are *'/etc/sbscan.conf'* and 
*'/var/log/sbscan.log'*.

It can use the same config file NMEAd uses, requiring a section named
scanner, formatted as follows:

[scanner]
db_file:*PATH_TO_DB_FILE* *(required)*
minspeed:*MIN_SPEED* *(defaults to 0.5)*
maxdelta:*MAX_DELTA* *(defaults to 1.0)*
pause_on_stop:*True|False* *(defaults to True)*

