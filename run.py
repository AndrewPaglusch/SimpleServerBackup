#!/usr/bin/env python3
from concurrent import futures
import lib

def main():
    log = lib.log
    args   = lib.SSBArgs(log).get_args()
    config = lib.SSBConfig(args.config, lib.logging).get_config()
    # build and start thread pool
    with futures.ThreadPoolExecutor(max_workers=config['concurrency']) as ex:
        backup_futures = {}
        for server_host, server_config in config['server_configs'].items():
            try:
                scripts = config['scripts_configs'][server_host]
            except:
                scripts = None
            log.debug(f"Adding {server_host} to thread pool")
            log.debug(f"{config['scripts_configs']} passed to class")
            s = lib.Backup(lib.logging, server_host, server_config, config['scripts_directory'], scripts)
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
                    log.info(f"{server_host}: {message}")
                else:
                    log.error(f"{server_host}: {message}")
            except Exception:
                    log.exception(f"{server_host}: An exception was hit while running backups")

if __name__ == '__main__':
   main()
