#!/usr/bin/env python
import sqlite3
import json
import logging
import ConfigParser
import argparse
import signal
import sys
import traceback
import time

import setproctitle

from file_lock import file_lock

CONFIG_LOCATION = '/etc/sbscan.conf'
LOGFILE_LOCATION = '/var/log/sbscan.log'
LOCK_SLEEP_TIME = 0.02

stopped = False

class CfgErr(Exception):
    """Config file related error"""
    pass

class Session(object):
    def __init__(self, params):
        pass
        
    def __enter__():
        pass
    
    def __exit__():
        pass
    
    def _get_sid():
        pass
    
    def check_add_position(nmea_data):
        pass
    
    def pause():
        pass

def handle_sigterm(signum, sigframe):
    global stopped
    logging.info('Caught SIGTERM, exiting.')
    stopped = True

def load_config(fname):
    """Load a config file."""
    required_params = [('scanner', ['db_file', 'nmea_file'])]
    optional_params = [('scanner', {'minspeed':'0.5', 
                                    'maxdelta':'1.0', 
                                    'pause_on_stop':'True',
                                    'polling_interval':'0.5',
                                    'log_point_count':'True',
                                    'log_point_count_interval':'1000'})]
    cfg = ConfigParser.ConfigParser()
    cfg.read([fname])
    if not cfg.sections():
        raise CfgErr, 'Unable to open config file %s or file empty.' % fname

    for section in required_params:
        for option in section[1]:
            if not cfg.has_option(section[0], option):
                raise CfgErr, ('Required config argument \'%s\''
                               'in section [%s] missing!') % (option,
                                                              section[0])
    for section in optional_params:
        if not cfg.has_section(section[0]):
            cfg.add_section(section[0])
        for option, value in section[1].iteritems():
            cfg.set(section[0], option, value)
    return cfg

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
        logging.basicConfig(format=('%(asctime)s [%(levelname)s]'
                                    ' -\t%(message)s'),
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
    
    params = config.items('scanner')
    
    with Session(params) as session:
        try:
            with open(params['nmea_file']) as f:
                logging.info('Established connection to NMEAd.')
                while not stopped:
                    with file_lock(f) as lock:
                        if not lock:
                            time.sleep(LOCK_SLEEP_TIME)
                            continue
                        try:
                            json_file = json.load(f)
                        except ValueError:
                            continue
                    session.check_add_position(json_file)
                    time.sleep(float(params['polling_interval']))
                    
        except IOError, err:
            if err.errno == errno.ENOENT:
                logging.critical(('Failed to establish connection to '
                                  'NMEAd through %s. Is NMEAd running? '
                                  'Does SBScan have the '
                                  'required permissions?'), 
                                  params['nmea_file'])
                sys.exit()
            else:
                raise
                
if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    setproctitle.setproctitle('SBScan')
    main()