#!/usr/bin/env python3
import subprocess
import sys
import datetime
"""
Server Class for SimpleServerBackup
Start is the main method available to the user.
"""

__author__ = "Andrew Paglusch"
__license__ = "MIT"

class Backup:
    def __init__(self, logging, server_host, server_config, scripts_dir, scripts, logfile='TBD'):
        self.scripts = scripts
        self.starttime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.host = server_host
        self._parse_serverconfig(server_config)
        self.log = logging.getLogger('ssb')
        self.connect_string = f"{self.username}@{self.host}" # root@web01.whatever.com
        self.backup_dest = 'backups/' + server_host + '/' # backups/web01.whatever.com/
        self.logfile = f"logs/{self.host}_{self.starttime}.log" if logfile == 'TBD' else logfile
        self._build_rsync_cmd()
        self.scripts_dir = scripts_dir + "/" + server_host + "/"
        self.script_deployed = False

    def _parse_serverconfig(self, server_config):
        self.username = server_config['username']
        self.port = server_config['port']
        self.ssh_args = ' '.join(server_config['ssh_args'])
        self.excludes = [ f"--exclude={ex}" for ex in server_config['excludes'] ]
        self.remote_path = server_config['remote_path']
        self.scripts_remote_location = server_config['scripts_location'] + '/'

    def _build_rsync_cmd(self):
        self.rsync_cmd = ['rsync', '-e', f'ssh -p {self.port} {self.ssh_args}', '-avPHS', '--delete'] + self.excludes

    def _deploy_scripts(self):
        res = self._run_rsync(self.scripts_remote_location, self.scripts_dir, direction='to_remote')
        if res['return_code'] == 0:
            self.script_deployed = True

    def _run_rsync(self, remote_dest, local_dest, direction='from_remote'):
        rsync_cmd = self.rsync_cmd
        if direction == 'from_remote':
            rsync_cmd.append(f"{self.connect_string}:{remote_dest}")
            rsync_cmd.append(local_dest)
        else:
            rsync_cmd.append(local_dest)
            rsync_cmd.append(f"{self.connect_string}:{remote_dest}")
        rsync_exec = subprocess.run(rsync_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._build_rsync_cmd()
        return({ 'return_code': rsync_exec.returncode,
             'output': rsync_exec.stdout.decode("utf-8") or b"" })

    def _run_pre_scripts(self):
        self.log.debug(f"Starting pre-scripts using config {self.scripts}")
        for pre_script in self.scripts['pre']:
            result = self._run_script( self.scripts_remote_location + pre_script, None)
            if result['return_code'] != 0:
                self.log.error(f"{pre_script} had nonzero return code! output was: \n {result['output']}")
                self.pre_script_failed = True
                break
            else:
                self.log.info(f"{pre_script} completed on {self.host}")
        self.pre_script_failed = False

    def _run_post_scripts(self):
        self.log.debug(f"Starting post-scripts using config {self.scripts}")
        for post_script in self.scripts['post']:
            result = self._run_script( self.scripts_remote_location + post_script, None)
            if result['return_code'] != 0:
                self.log.error(f"{post_script} had a nonzero return code! output was: \n {result['output']}")
                self.post_script_failed = True
                break
            else:
                self.log.info(f"{post_script} completed on {self.host}")
        self.post_script_failed = False

    def _run_script(self, script, options):
        self.log.debug(f"running script: {script} on {self.host}")
        if self.ssh_args == '':
            sshcmd = ['ssh', '-p', self.port, self.connect_string, script]
        else:
            sshcmd = ['ssh', self.ssh_args, '-p', self.port, self.connect_string, script]
        self.log.debug(f"attempting to run {sshcmd}")
        results = subprocess.run(sshcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return({'return_code': results.returncode,
              'output': results.stdout.decode("utf-8") or b"" })

    def _run_single_remote_cmd(self, command):
        ssh_command = ['ssh', '-p', self.port, self.connect_string, command]
        cmd = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = cmd.stdout or b""
        if cmd.returncode != 0:
            raise Exception(f"Remote command resulted in a non-zero return code: {cmd.returncode}. Command output: {output}")
        return output.decode("utf-8")

    def _log_backup_results(self, output):
        self.log.info(f"Saving rsync output for {self.host} to {self.logfile}")
        f = open(self.logfile, 'w')
        f.write(output)
        self.log.debug(f"Finished saving rsync output for {self.host} to {self.logfile}")

    def start_backup(self):
        self.log.info(f"Backup started for {self.host}")

        # deploy pre/post scripts
        self.log.info(f"Syncing pre-post scripts to {self.host} ")
        self._deploy_scripts()

        # run pre-scripts
        self._run_pre_scripts()
        if self.pre_script_failed == True:
            return (False, f"Pre scripts failed for {self.host} will not continue")
        rsync_results = self._run_rsync(remote_dest=self.remote_path, local_dest=self.backup_dest)
        self._log_backup_results(rsync_results['output'])

        # run post-scripts
        self._run_post_scripts()
        if self.post_script_failed == True:
            return (False, f"Post scripts failed for {self.host} will not continue")
        # TODO: Simply checking the return code of rsync
        # won't be enough to determine if a backup failed or not.
        # We will also need to consider the success of all pre/post scripts
        if rsync_results['return_code'] == 0:
            # run post-scripts
            # run_post_scripts()
            return (True, "Backup completed successfully")

        return (False, f"Backup failed. Rsync return code: {rsync_results['return_code']}. Check {self.logfile}")
