import paho.mqtt.client as mqtt
import requests
import json
import os
import logging


logLevel=logging.DEBUG

# Define Logger
logger = logging.getLogger()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logLevel)


# Variables
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv ("MQTT_TOPIC", "msh/tracker")
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MLO_USERNAME = os.getenv("MLO_USERNAME", "Default")

def send_GPS_Information_to_mobile_lagekarte(mlo_tid, lat, lon, username):
    url = (
            f"http://api.mobile-lagekarte.de/InsertData.php"
            f"?id={mlo_tid}&lat={lat}&long={lon}&orga={username}"
        )
    try: 
        response = requests.post(url)
        logger.info(f"Sent to Lagekarte: {url} -> {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending to Lagekarte: {e}")


node_name_map = {}

def convert_to_fixpoint(value):
    return value / 1e7

def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode("utf-8")
    logger.debug(f"Recieved ({topic}): {message}")
    try:
        json_message = json.loads(msg.payload.decode())
        msg_type = json_message["type"]
        nodeID = json_message["from"]

        if msg_type == "nodeinfo":
            payload = json_message["payload"]
	        # Create Mapping of ID too Long Name
            longname = payload["longname"]

            if nodeID and longname:
                node_name_map[nodeID] = longname
                logger.info(f"Creating Mapping {nodeID}: {longname}")

        elif msg_type == "position":
            if nodeID in node_name_map:
                # print(json_message)
                mlo_tid = node_name_map[nodeID]
                payload = json_message["payload"]
                lat = convert_to_fixpoint(payload.get("latitude_i"))
                lon = convert_to_fixpoint(payload.get("longitude_i"))
                logger.debug(f"Position: {lat}, {lon}")

                if lat is not None and lon is not None:
                    send_GPS_Information_to_mobile_lagekarte(mlo_tid, lat, lon, MLO_USERNAME)
                else:
                    logger.warning("No Valid position in payload")
            else:
                logger.warning("No Mapping for NodeID too a Name!")
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    except Exception as e:
        logger.error(f"Failed to parse message: {e}")


def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " +str(rc))
    client.subscribe(topic)

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info(f"Subscription acknowledged (mid={mid}, qos={granted_qos})")

def on_log(client, userdata, level, buf):
    logger.info(f"MQTT Log: {buf}")


client = mqtt.Client()
if MQTT_USER and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    logger.info("Logging into MQTT with user: " + MQTT_USER)

client.on_message = on_message
client.on_subscribe = on_subscribe
#client.on_log = on_log


logger.info(f"Connecting to MQTT {MQTT_BROKER}:{MQTT_PORT}, topic '{MQTT_TOPIC}'...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC, qos=1)
logger.info("Connected...")
client.loop_forever()
