#!/usr/bin/env python3
import sys
from concurrent import futures
import subprocess
import logging
import datetime
from lib.Server import Backup
from lib.SSBArgs import SSBArgs
from lib.SSBConfig import SSBConfig

def main():
    logging.basicConfig(stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s (%(levelname)s) - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ')
    args   = SSBArgs().get_args()
    config = SSBConfig(args.config, logging).get_config()

    # build and start thread pool
    with futures.ThreadPoolExecutor(max_workers=config['concurrency']) as ex:
        backup_futures = {}
        for server_host, server_config in config['server_configs'].items():
            logging.debug(f"Adding {server_host} to thread pool")
            s = Backup(logging, server_host, server_config, config['scripts_directory'])
            backup_futures[ex.submit(s.start_backup)] = server_host

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
