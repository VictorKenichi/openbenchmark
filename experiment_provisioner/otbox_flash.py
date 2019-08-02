import paho.mqtt.client as mqtt
import json
import base64
import Queue
import os
from mqtt_client import MQTTClient

# ============================ defines =========================================

NUMBER_OF_MOTES   = 80 - 4 - 4  # 4 motes are used for local teste and one otbox is not available
ITERATION_NUMBER  = 3
# ============================ classes =========================================
class OTBoxFlash(object):

    CLIENT_ID     = "OpenWSN"

    # in seconds, should be larger than the time starting from publishing message until receiving the response
    MESSAGE_RESP_TIMEOUT     = 30

    def __init__(self, user_id, firmware_path, broker, testbed):

        # initialize parameters
        self.image = None
        self.image_name      = ''
        self.firmware_path   = firmware_path
        self.broker          = broker
        self.testbed         = testbed
        self.user_id         = ''

        with open(firmware_path, 'rb') as f:
            self.image = base64.b64encode(f.read())
        if os.name == 'nt':       # Windows
            self.image_name = firmware_path.split('\\')[-1]
        elif os.name == 'posix':  # Linux
            self.image_name = firmware_path.split('/')[-1]

	self.program('all_motes')
    # ======================== private =========================================
    def _on_mqtt_connect(self, client, userdata, flags, rc):

        pass
        #topic = self.mqtttopic_mote_resp
        #client.subscribe(topic)
        # print "subscribe at {0}".format(topic)

        #client.loop_start()

    def _on_mqtt_message(self, client, userdata, message):
        '''
        Record the number of message received and success status
        '''

        self.response_success['message_counter']     += 1
        if json.loads(message.payload)['success']:
            self.response_success['success_counter'] += 1
        else:
            self.response_success['failed_messages_topic'].append(message.topic)
            self.response_success['failed_messages_payload'].append(message.payload)

        #if self.mote == 'all':
        if self.response_success['message_counter'] == NUMBER_OF_MOTES:
            self.cmd_response_success_queue.put('unblock')

    # ======================== public ==========================================
    def is_response_success(self):
        print ("-----------------------------------------------------------------------------")
        print ("Try to program {0} motes, {1} motes report with success".format(
            self.response_success['message_counter'],
            self.response_success['success_counter']
        ))
        if self.response_success['message_counter'] > self.response_success['success_counter']:
            print ("failed_messages_topic :")
            for topic in self.response_success['failed_messages_topic']:
                print ("    {0}".format(topic))
        print ("-----------------------------------------------------------------------------")


    def program(self, parameter):

        # initialize statistic result
        self.response_success = {
            'success_counter': 0,
            'message_counter': 0,
            'failed_messages_topic': [],
            'failed_messages_payload': []
        }

        # connect to MQTT
        self.mqttclient = mqtt.Client(self.CLIENT_ID)

        self.mqttclient.on_connect = self._on_mqtt_connect
        self.mqttclient.on_message = self._on_mqtt_message
        self.mqttclient.connect(self.broker)
        self.mqttclient.loop_start()

        # create queue for receiving resp messages
        self.cmd_response_success_queue = Queue.Queue()

        payload_program_image = {
            'token': 123,
            'description': self.image_name,
            'hex': self.image,
        }

        if parameter == 'all_motes':
            # mqtt topic string format and selec all motes
            mqtttopic_mote_cmd        = '{0}/deviceType/mote/deviceId/all/cmd/program'.format(self.testbed)
            self.mqtttopic_mote_resp  = '{0}/deviceType/mote/deviceId/+/resp/program'.format(self.testbed)
            self.mqttclient.subscribe(self.mqtttopic_mote_resp)
            # publish the cmd message
            self.mqttclient.publish(
                topic    = mqtttopic_mote_cmd,
                payload  = json.dumps(payload_program_image)
            )

        else:
            for i in parameter:
                mqtttopic_mote_cmd       = '{0}/deviceType/mote/deviceId/{1}/cmd/program'.format(self.testbed, i)
                self.mqtttopic_mote_resp = '{0}/deviceType/mote/deviceId/{1}/resp/program'.format(self.testbed, i)
                self.mqttclient.subscribe(self.mqtttopic_mote_resp)
                # publish the cmd message
                self.mqttclient.publish(
                    topic    = mqtttopic_mote_cmd,
                    payload  = json.dumps(payload_program_image)
                )

        try:
            # wait maxmium MESSAGE_RESP_TIMEOUT seconds before return
            self.cmd_response_success_queue.get(timeout=self.MESSAGE_RESP_TIMEOUT)
        except Queue.Empty as error:
            print("Getting Response messages timeout in {0} seconds".format(self.MESSAGE_RESP_TIMEOUT))
        finally:
            self.is_response_success()
            self.mqttclient.loop_stop()

    def flash(self):
        ITERATION_NUMBER       = 3
        unflashed_motes_list   = []

        print("Number of Motes not Flashed: {0}".format(len(self.response_success['failed_messages_topic'])))

        # Create a list with the motes not flashed correctly
        for topic in self.response_success['failed_messages_topic']:
            unflashed_motes_list.append(topic.split("/")[4])

        # Verify if there are some motes not flashed correctly
        while len(self.response_success['failed_messages_topic']) != 0 and ITERATION_NUMBER > 0:
            print ("Still have errors !")
            print ("Trying Again ...")
            self.program(unflashed_motes_list)
            print ("Finished !")
            print("Number of Motes not Flashed: {0}".format(len(self.response_success['failed_messages_topic'])))
            ITERATION_NUMBER -= 1