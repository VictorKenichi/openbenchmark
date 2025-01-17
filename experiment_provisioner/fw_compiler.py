import os
import subprocess
import random
import string

from mqtt_client import MQTTClient


class FWCompiler:

	def __init__(self, repo_url, branch, testbed, user_id):
		self.repo_url    = repo_url
		self.branch      = branch
		self.repo_name   = self._get_repo_name()
		self.testbed     = testbed
		self.user_id     = user_id  
		self.local_repo  = os.path.join(os.path.dirname(__file__), self.repo_name)
		self.mqtt_client = MQTTClient.create(testbed, user_id)

		self.board_names = {
			"iotlab" : "iot-lab_A8-M3",
			"wilab"  : "remote" ,
			"opentestbed" : "openmote-b-24ghz"
		}
		self.fw_dir      = os.path.join(os.path.dirname(__file__), "firmware") 

	def compile(self):
		self._clone_branch()
		self._compile_fw()
		fw_name = self._move_fw()
		self._delete_repo()

		return fw_name


	def _clone_branch(self):
		self._print_log('Cloning the branch...')
		self._run_cmd('clone')

	def _compile_fw(self):
		self._print_log('Compiling firmware...')
		self._run_cmd('compile')

	def _move_fw(self):
		self._print_log('Renaming and moving firmware...')
		fw_name = self._generate_random_fw_name()
		
		compiled_fw_path = os.path.join(self.local_repo, 'build', '{0}_armgcc'.format(self.board_names[self.testbed]), 'projects', 'common', '03oos_openwsn_prog')
		move_to_location = os.path.join(self.fw_dir, fw_name)

		print (self.fw_dir)
		print (fw_name)
		print (compiled_fw_path)
		print (move_to_location)

		mv_cmd = "mv {0} {1}".format(compiled_fw_path, move_to_location)
		subprocess.Popen(mv_cmd, shell=True)

		self._print_log('')
		self._print_log('')
		self._print_log('')
		self._print_log('Firmware moved to a new location: {0}'.format(move_to_location))

		return fw_name

	def _delete_repo(self):
		self._print_log('Removing the cloned repo...')
		del_dir = "rm -rf {0}".format( os.path.join(os.path.dirname(__file__), self.repo_name) )
		subprocess.Popen(del_dir, shell=True)


	def _run_cmd(self, cmd):
		cmds = {
			"clone"   : ['git', 'clone', '-b', self.branch, '--single-branch', self.repo_url],
			"compile" : ['scons', 'board={0}'.format(self.board_names[self.testbed]), 'toolchain=armgcc', 'apps=cbenchmark', 'oos_openwsn']
		}

		cwds = {
			"clone"   : os.path.dirname(os.path.abspath(__file__)),
			"compile" : self.local_repo
		}

		pipe = subprocess.Popen(cmds[cmd], cwd=cwds[cmd], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		
		for line in iter(pipe.stdout.readline, b''):
			output = line.rstrip()
			self._print_log(output)
			
		for line in iter(pipe.stderr.readline, b''):
			output = line.rstrip()
			self._print_log(output)


	def _get_repo_name(self):
		url_split = self.repo_url.split('/')
		return url_split[len(url_split) - 1].split('.')[0]

	def _generate_random_fw_name(self):
		letters = string.ascii_lowercase
		suffix  = ''.join(random.choice(letters) for i in range(7))
		return "{0}_{1}_{2}".format(self.repo_name, self.branch, suffix)

	def _print_log(self, message):
		self.mqtt_client.push_debug_log("[FW_COMPILATION]", message)
		print("[FW_COMPILATION] {0}".format(message))


def main():
	FWCompiler(
		repo_url = 'https://github.com/malishav/openwsn-fw.git',
		branch   = 'develop_FW-808',
		testbed  = 'iotlab',
		user_id  = 1
	).compile()

if __name__ == '__main__':
	main()