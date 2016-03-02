NMEAd and SBScan documentation
==============================

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

If any of the required parameters are missing, NMEAd will fail to run. The
INFO_LIST parameter is a comma separated list of NMEA data that you explicitely
want to exclude from the resulting json file.
