import sys
sys.path.append('..')

from utils import Utils
from abc import abstractproperty, abstractmethod
from _node import Node
import json


class Scenario(object):

	@abstractproperty
	def SCENARIO_IDENTIFIER(self):  # Fixed value depending on the instantiated child class 
		pass

	@abstractproperty
	def CONFIG_FILE(self):
		pass


	def _read_config(self, config_files):
		self.config_node_data = {}
		main_config    = config_files['main']
		testbed_config = config_files[self.testbed]

		with open(main_config, 'r') as f:
			with open(testbed_config, 'r') as tf:
				main_config_obj    = json.load(f)
				testbed_config_obj = json.load(tf)
				
				generic_node_data  = main_config_obj['nodes']

				for generic_id in generic_node_data:
					# Attaching testbed specific data to generic node data
					node_data = generic_node_data[generic_id]
					node_data['node_id'] = testbed_config_obj[generic_id]['node_id']
					node_data['transmission_power_dbm'] = testbed_config_obj[generic_id]['transmission_power_dbm']

					self.config_node_data[generic_id] = node_data

	
	def _instantiate_nodes(self):     # Instantiates node objects based on config objects and EUI-64 addresses read from sut payload
		assert len(self.config_node_data) == len(Utils.id_to_eui64)

		for generic_id in self.config_node_data:
			config_params = self.config_node_data[generic_id]
			params = {
				'generic_id'    : generic_id,
				'node_id'       : config_params['node_id'],
				'eui64'         : Utils.id_to_eui64[config_params['node_id']],
				'role'          : config_params['role'],
				'area'          : config_params['area'],
				'sending_points': config_params['traffic_sending_points']
			}
			self.nodes.append(Node(params))


	def __init__(self, sut_command):
		self.testbed         = sut_command['testbed']   # Testbed and nodes data passed from the MQTT payload (see _README.md, step 2)
		self.nodes           = []                       # List of objects of type Node
		self.config_object   = None                     # Instantiating nodes based on _config.json data and data received from SUT