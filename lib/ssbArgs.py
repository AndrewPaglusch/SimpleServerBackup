#!/usr/bin/env python
import json, sys, os, argparse
try:
   from lib.Parseconfig import ssbConfig
except:
   import Parseconfig
class ssbArgs:
    '''
    class to handle arguement parsing for a more elegant
    soultion to options handling
    '''
    def __init__(self, logging):
        '''
        overload the required/ optional options here
        '''
        self.logging = logging
        self.parser = argparse.ArgumentParser()
        self.parser._action_groups.pop()
        self.required = self.parser.add_argument_group('required arguments')
        self.optional = self.parser.add_argument_group('optional arguments')
        self.optional.add_argument("-c", "--config", default='config.ini', help="Main configuration file in ini format - see example")
        self.args, self.unknown = self.parser.parse_known_args()
        self.checkArgs()

    def checkArgs(self):
       pass
