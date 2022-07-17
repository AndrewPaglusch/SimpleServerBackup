#!/usr/bin/env python3
from configparser import ConfigParser
from pathlib import Path
"""
Configuration Parser for SimpleServerBackup
"""

class ssbConfig:
    def __init__(self, configfile, logging):
        self.logging = logging
        self.cp = ConfigParser()
        self.cp.read(configfile)
        self.config = self.normalize_config()
        self.load_all_server_config()

    def normalize_config(self):
        """load main config from disk"""
        config = {
            'concurrency':       self.cp.getint('main', 'concurrency', fallback=1),
            'scripts_directory': self.cp.get('main', 'scripts_dir'),
            'server_directory':  self.cp.get('main', 'server_dir'),
            'server_configs': {},
            'scripts_configs': {}
        }
        return config

    def load_server_config(self, filepath):
        sc = ConfigParser()
        sc.read(filepath)
        try:
            self.config['server_configs'][sc.get('connection', 'host')] = {
               'port': sc.get('connection', 'port', fallback="22"),
               'username': sc.get('connection', 'username', fallback="root"),
               'ssh_args': [ ssh_arg.strip() for ssh_arg in sc.get('connection', 'ssh_args', fallback="").split(',') if ssh_arg.strip() != '' ],
               'remote_path': sc.get('main', 'remote_path'),
               'excludes': [ exclude.strip() for exclude in sc.get('main', 'excludes').split(',') if exclude.strip() != '' ]
               }
        except Exception:
            self.logging.error(f"Unable to load {filepath} due to {Exception}")

    def load_all_server_config(self):
        """load server configs from disk"""
        config_files = Path(self.config['server_directory']).glob('*.ini')
        for config_file in config_files:
            self.logging.debug(f"Loading config file {config_file} from disk")
            self.load_server_config(config_file)

    def load_all_scripts(self):
        script_servers = Path(self.config['scripts_directory']).glob()

