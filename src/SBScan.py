#!/usr/bin/env python
import sqlite3
import json
import logging
import ConfigParser
import argparse
import signal
import sys
import traceback

import setproctitle

from file_lock import file_lock

CONFIG_LOCATION = '/etc/sbscan.conf'
LOGFILE_LOCATION = '/var/log/sbscan.log'

class Session(object):
    def __init__(self, params):
        pass
        
    def __enter__():
        pass
    
    def __exit__():
        pass
    
    def _get_sid():
        pass
    
    def add_position(nmea_data):
        pass
    
    def pause():
        pass

def handle_sigterm(signum, sigframe):
    pass

def load_config(fname):
    pass

def main():
    apr = argparse.ArgumentParser()
    apr.add_argument('--logfile', 
                     help=('Log file location (defaults to %s)' % LOGFILE_LOCATION))
    apr.add_argument('--config',
                     help=('Config file location (defaults to %s)' % CONFIG_LOCATION))
    app = apr.parse_args()
    logfile = app.logfile or LOGFILE_LOCATION
    configf = app.config or CONFIG_LOCATION
    
    try:
        logging.basicConfig(format='%(asctime)s [%(levelname)s] -\t%(message)s',
                            filename=logfile, level=logging.INFO)
    except:
        sys.exit()
        
    logging.info('SBScan started!')
    try:
        config = load_config(configf)
    except CfgErr:
        logging.critical(str(sys.exc_info()[1]))
        sys.exit()
    else:
        logging.info('Loaded config file.')

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    setproctitle.setproctitle('SBScan')
    main()