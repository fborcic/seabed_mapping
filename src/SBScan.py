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
import datetime

import setproctitle

from file_lock import file_lock

CONFIG_LOCATION = '/etc/sbscan.conf'
LOGFILE_LOCATION = '/var/log/sbscan.log'
LOCK_SLEEP_TIME = 0.02

stopped = False

NMEA_REQDATA = ['latitude', 'longitude', 'NS', 'EW', 'depthm', 'speed']

def safe_depth(nmea_data):
    return (float(nmea_data['depthm'][0] or 0) or
            float(nmea_data['depthf'][0] or 0)*0.3048 or
            float(nmea_data['depthF'][0] or 0)*1.8288)

class CfgErr(Exception):
    """Config file related error"""
    pass

class Session(object):
    def __init__(self, params):
        self.params = params
        self.sid = None
        self.paused = False
        self.have_req_nmea = False
        self.position_counter = 0
        self.last_timest = float('-inf')
        self.check_minspeed = (self.params['pause_on_stop'] == 'True')
        self.minspeed = float(self.params['minspeed'])
        self.commit_interval = int(self.params['commit_interval'])
        self.log_interval = int(self.params['log_point_count_interval'])
        self.log_count = (self.params['log_point_count'] == 'True')
        try:
            self.db = sqlite3.connect(self.params['db_file'])
        except:
            logging.critical('Failed to open db file %s !', 
                             self.params['db_file'])
            sys.exit()
            
        self.cursor = self.db.cursor()
        
    def __enter__(self):
        start_time = time.time()
        start_tstamp = datetime.datetime.fromtimestamp(start_time)
        
        self.safe_execute(('INSERT INTO sessions(starttime, stoptime) '
                           'VALUES (?, NULL)'), (start_tstamp,))
            
        self.sid = self.cursor.lastrowid
        assert self.sid
        
        self.db.commit()
        return self
        
    def __exit__(self, dummy, dummy2, dummy3):
        stop_time = time.time()
        stop_tstamp = datetime.datetime.fromtimestamp(stop_time)
        
        self.safe_execute(('UPDATE sessions SET stoptime = ? '
                           'WHERE _id = ?'), (stop_tstamp, self.sid))
        
        self._close()
        
    def check_add_position(self, nmea_data):
        if self.check_minspeed:
            self.paused = float(nmea_data['speed'][0]) < self.minspeed
        if not self.have_req_nmea:
            for key in NMEA_REQDATA:
                if key not in nmea_data:
                    print key
                    return
            logging.info('Received required NMEA data.')
            self.have_req_nmea = True
        pass_time = nmea_data['latitude'][1]
        print self.paused, pass_time > self.last_timest
        if not self.paused and pass_time > self.last_timest:
            print 'CAP - passed condition'
            s_g_delta = nmea_data['latitude'][1] - nmea_data['depthm'][1]
            lat = nmea_data['latitude'][0] + nmea_data['NS'][0]
            lon = nmea_data['longitude'][0] + nmea_data['EW'][0]
            spd = float(nmea_data['speed'][0])
            trk = float(nmea_data['track'][0])
            dpt = safe_depth(nmea_data)
            
            self.safe_execute(('INSERT INTO positions(passing_time, lat, '
                                 'lon, speed, heading, time_between, '
                                 ' session_id) VALUES (?,?,?,?,?,?,?)'),
                                 (pass_time, lat, lon, spd,
                                 trk, s_g_delta, self.sid))
            self.position_counter += 1
            
            if not self.position_counter % self.commit_interval:
                self.db.commit()
            
            if self.log_count and not (self.position_counter %
                                       self.log_interval):
                logging.info('Recorded %d points', self.position_counter)
            
    def safe_execute(self, querystring, argtuple):
        try:
            self.cursor.execute(querystring, argtuple)
        except sqlite3.OperationalError:
            logging.critical('SQL operation failed: ', querystring)
            self._close()
            sys.exit(1)
            
    def _close(self):
        self.db.commit()
        self.cursor.close()
        self.db.close()
        
    def log_count(self):
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
                                    'log_point_count_interval':'1000',
                                    'commit_interval':'500'})]
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
            if not cfg.has_option(section[0], option):
                cfg.set(section[0], option, value)
    return cfg

def main():
    apr = argparse.ArgumentParser()
    apr.add_argument('--logfile', 
                     help=('Log file location (defaults to %s)' % 
                     LOGFILE_LOCATION))
    apr.add_argument('--config',
                     help=('Config file location (defaults to %s)' %
                     CONFIG_LOCATION))
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
    
    params = dict(config.items('scanner'))
    
    with Session(params) as session:
        try:
            with open(params['nmea_file']) as f:
                logging.info('Established connection to NMEAd.')
                while not stopped:
                    with file_lock(f) as lock:
                        if not lock:
                            time.sleep(LOCK_SLEEP_TIME)
                            print 'Ctn1!'
                            continue
                        try:
                            f.seek(0)
                            json_file = json.load(f)
                        except ValueError:
                            print 'Ctn2!'
                            continue
                    print 'Check!'
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
