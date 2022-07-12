#!/usr/bin/env python3
import sys
from pathlib import Path
from concurrent import futures
from configparser import ConfigParser
from pprint import pprint
import subprocess
import logging
import datetime

class Server:
    def __init__(self, server_host, server_config):
        self.host = server_host # web01.whatever.com
        self.username = server_config['username'] # root
        self.connect_string = f"{self.username}@{self.host}" # root@web01.whatever.com
        self.port = server_config['port'] # 22
        self.ssh_args = ' '.join(server_config['ssh_args'])
        self.remote_path = server_config['remote_path'] # /
        self.excludes = server_config['excludes']
        self.backup_dest = 'backups/' + server_host + '/' # backups/web01.whatever.com/
        self.logfile = "Not yet set" # will be set by log_backup_results

        # will be updated to True after pre/post scripts have been synced to host
        self.script_deployed = False

    def deploy_scripts(self, scripts):
        try:
            self.run_remote_command('mkdir /tmp/SimpleServerBackup_scripts')
        except Exception as ex:
            return (False, f"Error while creating remote script directory: {ex}")

        rsync_command = ['rsync', '-e', f'ssh -p {self.port} {self.ssh_args}'] + \
                ['-avPH'] + \
                ['--delete', f"{self.connect_string}:{self.remote_path}", self.backup_dest ]
        rsync_exec = subprocess.run(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def run_pre_scripts(self, ):
        pass

    def run_post_scripts(self):
        pass

    def run_remote_command(self, command):
        ssh_command = ['ssh', '-p', self.port, self.connect_string, command]
        cmd = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = cmd.stdout or b""
        if cmd.returncode != 0:
            raise Exception(f"Remote command resulted in a non-zero return code: {cmd.returncode}. Command output: {output}")
        return output.decode("utf-8")

    def run_rsync(self):
        self.excludes = [ f"--exclude={ex}" for ex in self.excludes ]
        rsync_command = ['rsync', '-e', f'ssh -p {self.port} {self.ssh_args}'] + \
                        ['-avPH'] + \
                        self.excludes + \
                        ['--delete', f"{self.connect_string}:{self.remote_path}", self.backup_dest ]
        rsync_exec = subprocess.run(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return_code = rsync_exec.returncode
        rsync_output = rsync_exec.stdout or b""

        return({ 'return_code': return_code,
             'output': rsync_output.decode("utf-8") })

    def log_backup_results(self, output):
        self.logfile = f"logs/{self.host}_{self.starttime}.log"

        # write rsync output to logfile
        logging.info(f"Saving rsync output for {self.host} to {self.logfile}")
        f = open(self.logfile, 'w')
        f.write(output)
        logging.debug(f"Finished saving rsync output for {self.host} to {self.logfile}")

    def start(self):
        self.starttime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        logging.info(f"Backup started for {self.host}")

        # deploy pre/post scripts
        # deploy_scripts()

        # run pre-scripts
        # run_pre_scripts()

        # run the backup
        rsync_results = self.run_rsync()
        self.log_backup_results(rsync_results['output'])

        # TODO: Simply checking the return code of rsync
        # won't be enough to determine if a backup failed or not.
        # We will also need to consider the success of all pre/post scripts
        if rsync_results['return_code'] == 0:
            # run post-scripts
            # run_post_scripts()
            return (True, "Backup completed successfully")

        return (False, f"Backup failed. Rsync return code: {rsync_results['return_code']}. Check {self.logfile}")

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
            s = Server(server_host, server_config)
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
