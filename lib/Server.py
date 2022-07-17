#!/usr/bin/env python3
import subprocess
import datetime, json
"""
Server Class for SimpleServerBackup
Start is the main method available to the user.
"""

__author__ = "Andrew Paglusch"
__license__ = "MIT"

class Backup:
    def __init__(self, logging, server_host, server_config, scripts_dir, logfile='TBD'):
        self.starttime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.logging = logging
        self.host = server_host # web01.whatever.com
        self.username = server_config['username'] # root
        self.connect_string = f"{self.username}@{self.host}" # root@web01.whatever.com
        self.port = server_config['port'] # 22
        self.ssh_args = ' '.join(server_config['ssh_args'])
        self.remote_path = server_config['remote_path'] # /
        self.excludes = [ f"--exclude={ex}" for ex in server_config['excludes'] ]
        self.backup_dest = 'backups/' + server_host + '/' # backups/web01.whatever.com/
        self.logfile = f"logs/{self.host}_{self.starttime}.log" if logfile == 'TBD' else logfile
        self.build_rsync_cmd()
        self.scripts_remote_location = server_config['scripts_location']
        self.scripts_dir = scripts_dir + "/" + server_host + "/"
        # will be updated to True after pre/post scripts have been synced to host
        self.script_deployed = False

    def build_rsync_cmd(self):
        self.rsync_cmd = ['rsync', '-e', f'ssh -p {self.port} {self.ssh_args}', '-avPHS', '--delete'] + self.excludes

    def deploy_scripts(self):
        res = self.__run_rsync__(self.scripts_remote_location, self.scripts_dir, direction='to_remote')
        if res['return_code'] == 0:
            self.script_deployed = True

    def __run_rsync__(self, remote_dest, local_dest, direction='from_remote'):
        rsync_cmd = self.rsync_cmd
        if direction == 'from_remote':
            rsync_cmd.append(f"{self.connect_string}:{remote_dest}")
            rsync_cmd.append(local_dest)
        else:
            rsync_cmd.append(local_dest)
            rsync_cmd.append(f"{self.connect_string}:{remote_dest}")
        rsync_exec = subprocess.run(rsync_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.build_rsync_cmd()
        return({ 'return_code': rsync_exec.returncode,
             'output': rsync_exec.stdout.decode("utf-8") or b"" })

    def run_pre_scripts(self):
        pass

    def run_post_scripts(self):
        pass

    def clean_scripts(self):
        pass

    def run_single_remote_command(self, command):
        ssh_command = ['ssh', '-p', self.port, self.connect_string, command]
        cmd = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = cmd.stdout or b""
        if cmd.returncode != 0:
            raise Exception(f"Remote command resulted in a non-zero return code: {cmd.returncode}. Command output: {output}")
        return output.decode("utf-8")

    def log_backup_results(self, output):
        self.logging.info(f"Saving rsync output for {self.host} to {self.logfile}")
        f = open(self.logfile, 'w')
        f.write(output)
        self.logging.debug(f"Finished saving rsync output for {self.host} to {self.logfile}")

    def start(self):
        self.logging.info(f"Backup started for {self.host}")

        # deploy pre/post scripts
        self.logging.info(f"Syncing scripts to remoted server")
        self.deploy_scripts()

        # run pre-scripts
        # run_pre_scripts()

        # run the backup
        rsync_results = self.__run_rsync__(remote_dest=self.remote_path, local_dest=self.backup_dest)
        self.log_backup_results(rsync_results['output'])

        # TODO: Simply checking the return code of rsync
        # won't be enough to determine if a backup failed or not.
        # We will also need to consider the success of all pre/post scripts
        if rsync_results['return_code'] == 0:
            # run post-scripts
            # run_post_scripts()
            return (True, "Backup completed successfully")

        return (False, f"Backup failed. Rsync return code: {rsync_results['return_code']}. Check {self.logfile}")

