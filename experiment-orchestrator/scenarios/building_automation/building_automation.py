import os
import json
from scenarios.scenario import Scenario


class BuildingAutomation(Scenario):

	SCENARIO_IDENTIFIER = 'building-automation'

	def __init__(self, sut_command):
		super(BuildingAutomation, self).__init__(sut_command)
		
		self.CONFIG_FILES = {
			"main"  : os.path.join(self.scenario_config, self.SCENARIO_IDENTIFIER, "_config.json"),
			"iotlab": os.path.join(self.scenario_config, self.SCENARIO_IDENTIFIER, "_iotlab_config.json"),
			"wilab" : os.path.join(self.scenario_config, self.SCENARIO_IDENTIFIER, "_wilab_config.json")
		}

		super(BuildingAutomation, self)._read_config(self.CONFIG_FILES)

		self._instantiate_nodes()