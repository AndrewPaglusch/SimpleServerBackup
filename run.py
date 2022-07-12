#!/usr/bin/env python3
import sys
from pathlib import Path
from concurrent import futures
from configparser import ConfigParser
from pprint import pprint
import subprocess
import logging
import datetime
from lib.Server import Server
def load_main_config():
    """load main config from disk"""
    cp = ConfigParser()
    cp.read("config.ini")
    config = {
        'concurrency': int(cp.get('main', 'concurrency', fallback=1))
    }
    return config

def load_all_server_config():
    """load server configs from disk"""
    config_files = Path('./servers.d').glob('*.ini')
    server_configs = {}
    for config_file in config_files:
        logging.debug(f"Loading config file {config_file} from disk")
        config = ConfigParser()
        config.read(config_file)

        host = config.get('connection', 'host')
        server_configs[host] = {
            'port': config.get('connection', 'port', fallback="22"),
            'username': config.get('connection', 'username', fallback="root"),
            'ssh_args': [ ssh_arg.strip() for ssh_arg in config.get('connection', 'ssh_args', fallback="").split(',') if ssh_arg.strip() != '' ],
            'remote_path': config.get('main', 'remote_path'),
            'excludes': [ exclude.strip() for exclude in config.get('main', 'excludes').split(',') if exclude.strip() != '' ]
        }
    return server_configs

def main():
    logging.basicConfig(stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s (%(levelname)s) - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ')
    try:
        config = load_main_config()
    except Exception:
        logging.exception(f"Unable to read main config from disk.")
        exit()

    try:
        server_configs = load_all_server_config()
    except Exception:
        logging.exception(f"Unable to load server configs from disk.")
        exit()

    # build and start thread pool
    with futures.ThreadPoolExecutor(max_workers=config['concurrency']) as ex:
        backup_futures = {}
        for server_host, server_config in server_configs.items():
            logging.debug(f"Adding {server_host} to thread pool")
            s = Server(logging, server_host, server_config)
            backup_futures[ex.submit(s.start)] = server_host

        for future in futures.as_completed(backup_futures):
            # Iterate over futures as they complete
            # Tuple is returned. First item is True/False if it was a success
            # Second is a message to be displayed
            # If an exception is thrown when getting the results, that means an error
            # happened that wasn't caught. Print the server name and a backtrace

            server_host = backup_futures[future]
            try:
                success, message = future.result()
                if success:
                    logging.info(f"{server_host}: {message}")
                else:
                    logging.error(f"{server_host}: {message}")
            except Exception:
                    logging.exception(f"{server_host}: An exception was hit while running backups")

if __name__ == '__main__':
   main()
