#!/usr/bin/env python3
from configparser import ConfigParser
from pathlib import Path
"""
Configuration Parser for SimpleServerBackup
"""

class SSBConfig:
    def __init__(self, configfile, logging):
        self.logging = logging
        self.cp = ConfigParser()
        self.cp.read(configfile)
        self.config = self._normalize_config()
        self._load_all_server_config()
        self._load_all_scripts()

    def _normalize_config(self):
        """load main config from disk"""
        config = {
            'concurrency':       self.cp.getint('main', 'concurrency', fallback=1),
            'scripts_directory': self.cp.get('main', 'scripts_dir'),
            'server_directory':  self.cp.get('main', 'server_dir'),
            'server_configs':    {},
            'scripts_configs':   {}
        }
        return config

    def _load_server_config(self, filepath):
        sc = ConfigParser()
        sc.read(filepath)
        try:
            self.config['server_configs'][sc.get('connection', 'host')] = {
               'port': sc.get('connection', 'port', fallback="22"),
               'username': sc.get('connection', 'username', fallback="root"),
               'ssh_args': [ ssh_arg.strip() for ssh_arg in sc.get('connection', 'ssh_args', fallback="").split(',') if ssh_arg.strip() != '' ],
               'remote_path': sc.get('main', 'remote_path'),
               'excludes': [ exclude.strip() for exclude in sc.get('main', 'excludes').split(',') if exclude.strip() != '' ],
               'scripts_location':  sc.get('main', 'scripts_remote_location', fallback="/tmp")
            }
        except Exception:
            self.logging.error(f"Unable to load {filepath} due to {Exception}")

    def _load_all_server_config(self):
        """load server configs from disk"""
        config_files = Path(self.config['server_directory']).glob('*.ini')
        for config_file in config_files:
            self.logging.debug(f"Loading config file {config_file} from disk")
            self._load_server_config(config_file)

    def _load_all_scripts(self):
        script_servers = Path(self.config['scripts_directory']).glob('*')
        for server in script_servers:
            if not self._verify_script_to_server(server):
                continue
            files = [ file.parts[-1] for file in server.iterdir() ]
            pre, post = self._sort_files(files)
            self.config['scripts_configs'][server.parts[-1]] = {}
            self.config['scripts_configs'][server.parts[-1]]['pre'] = pre
            self.config['scripts_configs'][server.parts[-1]]['post'] = post

    def _sort_files(self, files):
        pre  = sorted([ file for file in files if file.startswith('pre') ])
        post = sorted([ file for file in files if file.startswith('post') ])
        return pre, post

    def _verify_script_to_server(self, server):
        if not server.is_dir():
            self.logging.info(f"{server.parts} is not a directory")
            return False
        hostname = server.parts[-1]
        if hostname not in self.config['server_configs'].keys():
            self.logging.info(f"{hostname} has no scripts - no pre/post scripts will be ran.")
            return False
        return True
