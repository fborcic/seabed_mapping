#!/usr/bin/env python
import sqlite3
import json
import logging
import ConfigParser
import argparse
import signal

import setproctitle

from file_lock import file_lock

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
    signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == '__main__':
    main()