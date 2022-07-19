#!/usr/bin/env python
import argparse
import logging

class SSBArgs:
    '''
    class to handle arguement parsing for a more elegant
    soultion to options handling
    '''
    def __init__(self, log):
        '''
        overload the required/ optional options here
        '''
        self.log = log
        loglevels = ['info', 'debug', 'warn', 'error']
        self.parser = argparse.ArgumentParser()
        self.parser._action_groups.pop()
        self.required = self.parser.add_argument_group('required arguments')
        self.optional = self.parser.add_argument_group('optional arguments')
        self.optional.add_argument("-c", "--config", default='config.ini', help="Main configuration file in ini format - see config.ini example")
        self.optional.add_argument("-l", "--loglevel", default='info', help="Logging level output", choices=loglevels)
        self.args, self.unknown = self.parser.parse_known_args()
        self._check_args()

    def _check_args(self):
        if self.args.loglevel != 'info':
            self._set_log_level()

    def _set_log_level(self):
        if self.args.loglevel == 'error':
            self.log.setLevel(logging.ERROR)
        if self.args.loglevel == 'debug':
            self.log.setLevel(logging.DEBUG)
        if self.args.loglevel == 'warn':
            self.log.setLevel(logging.WARN)

    def get_args(self):
        return self.args
