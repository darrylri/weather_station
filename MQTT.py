import time
from datetime import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json

class MQTTClient:
    def __init__(self, name, location, topic, broker_ip, port, username, password) -> None:
        self.name = name
        self.location = location
        self.topic = topic
        self.host = broker_ip
        self.port = port
        self.timeout = 60
        self.connected = 0
        self.username = username
        self.password = password
        self.start()

    def start(self):
        self.client = mqtt.Client(self.name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        # breakpoint()
        if self.port == 8883:
            self.client.tls_set()
        if self.username is not None and self.password is not None:
            self.client.username_pw_set(self.username, password=self.password)
        self.client.connect(self.host, self.port, self.timeout)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if self.connected == 0:
            self.connected = 1
            # print("Connected to MQTT, rc="+str(rc))
        self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        message = str(msg.payload)
        # print("MQTT "+msg.topic+': '+str(message))

    def on_publish(self, client, userdata, mid):
        # print("MQTT published "+str(mid))
        return

    def publish(self, topic, payload):
        jsonwrapper = {
            'location': self.location, 
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            'payload': { }
            }
        time.sleep(1)
        for k in payload:
            jsonwrapper['payload'][k] = payload[k]
        payload_str = json.dumps(jsonwrapper)
        if self.connected == 0:
            self.start()
        try:
            mi = self.client.publish(topic, payload_str)
            rc = mi.rc
        except:
            rc = mqtt.MQTT_ERR_CONN_LOST
        if rc == mqtt.MQTT_ERR_NO_CONN or rc == mqtt.MQTT_ERR_CONN_LOST:
            self.connected = 0
        return rc
