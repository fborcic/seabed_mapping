#!/usr/bin/env python

"""
NMEA driver for a sounder and a GPS. Output is written to specified file
in json format. Uses nmea_templates.py to specify sentence format and
a mandatory config file with three mandatory sections documented in
load_config docstring. Should be run with permissions to read and write to
the serial ports specified, and write to the log file specified. Automated
install script should take care of that, preferably by adding a new user.

This should be run as an upstart job.
"""

import json
import threading
import time
import argparse
import ConfigParser
import sys
import logging
import traceback

import serial
import setproctitle

from nmea_templates import nmea_templates
from file_lock import file_lock

CONFIG_LOCATION = '/etc/nmead.conf'
LOGFILE_LOCATION = '/var/log/nmead.log'
WRITER_SLEEP_TIME = 0.1
SERIAL_TIMEOUT = 0.05

terminate = False   # Global termination flag

@contextmanager
def file_lock(filed, exclusive=False):
    """Non-blocking file lock context manager"""
    opcode = [fcntl.LOCK_SH, fcntl.LOCK_EX][exclusive] | fcntl.LOCK_NB
    try:
        try:
            fcntl.flock(filed, opcode)
        except IOError, err:
            if not (err.errno == errno.EAGAIN or err.errno == errno.EACCES):
                raise
            else:
                yield False
        else:
            yield True
    except:
        raise
    finally:
        fcntl.flock(filed, fcntl.LOCK_UN)

def thunk(callable_, *args, **kwargs):
    """Return thunk that calls callable_ with args/kwargs"""
    return lambda: callable_(*args, **kwargs)

def timeout_block(nb_callable, timeout, timeiter=0.05):
    """Emulate blocking call with a non-blocking one"""
    starttime = time.time()
    currtime = starttime
    while currtime < starttime+timeout:
        if nb_callable():
            return True
        else:
            time.sleep(timeiter)
        currtime = time.time()

def chk_nmea_cs(sentence):
    """NMEA checksum evaluator"""
    xor = 0
    for char in sentence[1:-3]:
        xor ^= ord(char)
    return '%02X' % xor == sentence[-2:]

class CfgErr(Exception):
    """Config file related error"""
    pass


class ChecksumError(Exception):
    """Checksum check failure error"""
    pass


class TemplateMismatchError(Exception):
    """NMEA template/sentence mismatch error"""
    pass


class SharedStruct(object):
    """Thread-shared memory with access control mechanisms"""
    def __init__(self):
        self.updated = threading.Event()
        self.lock = threading.Lock()
        self.struct = dict()


class ThreadClass(object):
    """Clean exit thread base class"""
    def __init__(self):
        self.cleanup_stack = []
        self.terminate = False
    
    def __call__(self):
        self.mainloop()

    def mainloop(self):
        """Main loop of the thread"""
        while not (self.terminate or terminate):
            try:
                self.repeat()
            except:
                exc_info = sys.exc_info()
                logging.critical(('Unexpected error %s occured,'
                                  ' saying: %s \nTraceback:\n%s'),
                                  exc_info[0], exc_info[1],
                                  traceback.format_exc())
                main_exit()
        self.cleanup()

    def cleanup(self):
        """Clean up by calling anything on self.cleanup_stack"""
        while self.cleanup_stack:
            try:
                self.cleanup_stack.pop()()
            except:
                pass

    def repeat(self):
        """Should be overloaded in the subclass; the code to be repeated."""
        raise NotImplementedError
    
    def start(self):
        """Start the thread"""
        self.th_handle = threading.Thread(target=self)
        self.th_handle.start()
        return self.th_handle


class Driver(ThreadClass):
    """NMEA device driver class"""
    def __init__(self, shared_struct, params, device_name):
        ThreadClass.__init__(self)
        self.struct = shared_struct
        self.device_name = device_name
        self.params = dict(params)
        self.structcpy = None
        self.nmea_templates = nmea_templates.copy()
        self.chk_chksums = (self.params.get('check_checksums') == 'True')
        
        logging.info('%s listener starting.', self.device_name)
        try:
            self.device = serial.Serial(self.params['port'], 
                                        int(self.params['baud']),
                                        timeout=SERIAL_TIMEOUT)
        except serial.SerialException:
            logging.critical('Failed to open %s serial port: %s',
                             self.device_name, self.params['port'])
            logging.debug(traceback.format_exc())
            main_exit()
            return
        logging.info('Successfully opened %s serial port.', self.device_name)
        self.cleanup_stack.append(self.device.close)
        
        disabled_sentences = self.params.get('disable_nmea', '')
        for dsentence in disabled_sentences.split():
            if dsentence in self.nmea_templates:
                del self.nmea_templates[dsentence]
        
    def repeat(self):
        try:
            sentence = self.device.readline()
            toa = time.time()
            sentence = sentence.strip()  
            if sentence:
                header = sentence[:6]
                if header in self.nmea_templates:
                    if self.chk_chksums and not chk_nmea_cs(sentence):
                        raise ChecksumError
                    template = self.nmea_templates[header]
                    sentence = sentence[7:-3].split(',')
                    if len(template) != len(sentence):
                        raise TemplateMismatchError
                    data = zip(sentence, [toa]*len(sentence))
                    self.structcpy = dict(p for p in 
                                     zip(template, data) if p[0])
        except TemplateMismatchError:
            logging.error('NMEA template mismatch: %s', header)
            logging.debug('MISMATCH: %d %d', len(template), len(sentence))
        except ChecksumError:
            logging.warning('Bad NMEA checksum on %s:%s',
                            self.device_name, header)
        except serial.SerialException:
            logging.critical('Serial communication error with %s, exiting.',
                             self.device_name)
            main_exit(True) # Does NOT exit!
        
        if self.structcpy is not None and self.struct.lock.acquire(False):
            self.struct.struct.update(self.structcpy)
            self.struct.updated.set()
            self.struct.lock.release()
            self.structcpy = None
            logging.debug('Written to struct')

            
class Writer(ThreadClass):
    """File writer class"""
    def __init__(self, shared_struct, params):
        ThreadClass.__init__(self)
        self.struct = shared_struct
        self.params = dict(params)
        self.structcpy = None
        
        try:
            self.file = open(self.params['output_file'], 'w')
        except:
            logging.critical('Failed to open output file: %s',
                             self.params['output_file'])
            main_exit()
            return
        logging.info('Opened interface file: %s',
                     self.params['output_file'])
        self.cleanup_stack.append(self.file.close)
    
    def repeat(self):
        updated = self.struct.updated.is_set()
        if updated and self.struct.lock.acquire(False):
            self.structcpy = self.struct.struct.copy()
            self.struct.lock.release()
            self.struct.updated.clear()
            logging.debug('Copied struct!')
            
        if self.structcpy is not None:
            with file_lock(self.file, exclusive=True) as lock_established:
                if lock_established:
                    self.file.truncate(0)
                    self.file.seek(0)
                    json.dump(self.struct.struct, self.file)
                    self.file.flush()
                    self.structcpy = None
                    logging.debug('Written struct to file.')
        time.sleep(WRITER_SLEEP_TIME)

def handle_sigterm(signum, sigframe):
    """SIGTERM handler function"""
    logging.info('Received SIGTERM, exiting gracefully.')
    main_exit()

def main_exit(nonmain=False):
    """Exit all threads; should be called with
       nonmain=True from threads other than main."""
    
    global terminate
    terminate = 'SIGTERM'
    if not nonmain:
        sys.exit()

def load_config(fname):
    """Load a config file."""
    required_params = [('writer', ['output_file']),
                       ('sounder', ['port']),
                       ('gps', ['port'])]
    optional_params = [('sounder', {'baud':'4800', 
                                    'disable_nmea':'', 
                                    'check_checksums':'False'}),
                       ('gps', {'baud':'4800', 
                               'disable_nmea':'', 
                               'check_checksums':'False'})]
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
    """Entry point"""
    apr = argparse.ArgumentParser()
    apr.add_argument('--logfile', 
                     help='Log file location (defaults to /var/log/nmead.log)')
    apr.add_argument('--config',
                     help='Config file location (defaults to /etc/nmead.conf)')
    app = apr.parse_args()
    logfile = app.logfile or LOGFILE_LOCATION
    configf = app.config or CONFIG_LOCATION
    
    try:
        logging.basicConfig(format='%(asctime)s [%(levelname)s] -\t%(message)s',
                            filename=logfile, level=logging.INFO)
    except:
        sys.exit()
        
    logging.info('NMEA daemon started!')
    try:
        config = load_config(configf)
    except CfgErr:
        logging.critical(str(sys.exc_info()[1]))
        sys.exit()
    else:
        logging.info('Loaded config file.')
    
    
    struct = SharedStruct()
    gpsdriver = Driver(struct, config.items('gps'), 'GPS')
    soudriver = Driver(struct, config.items('sounder'), 'SOUNDER')
    writer = Writer(struct, config.items('writer'))
    
    th_objects = [gpsdriver, soudriver, writer]
    if all(th_objects):
        th_handles = []
        for thread in th_objects:
            th_handles.append(thread.start())
        logging.info('Initialized!')
    else:
        logging.critical('Initialization failed!')    
    
if __name__ == '__main__':
    setproctitle.setproctitle('NMEAd')
    signal.signal(signal.SIGTERM, handle_sigterm)
    main()
    while True:
        time.sleep(0.5)
