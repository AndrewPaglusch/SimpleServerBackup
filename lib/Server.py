#!/usr/bin/env python3
import subprocess
import datetime
"""
Server Class for SimpleServerBackup
Start is the main method available to the user.
"""

__author__ = "Andrew Paglusch"
__license__ = "MIT"

class Server:
    def __init__(self, logging, server_host, server_config):
        self.logging = logging
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

    def run_pre_scripts(self):
        pass

    def run_post_scripts(self):
        pass

    def clean_scripts(self):
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
        ## maybe move rsync to its own method
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

        self.logging.info(f"Saving rsync output for {self.host} to {self.logfile}")
        f = open(self.logfile, 'w')
        f.write(output)
        self.logging.debug(f"Finished saving rsync output for {self.host} to {self.logfile}")

    def start(self):
        self.starttime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.logging.info(f"Backup started for {self.host}")

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

