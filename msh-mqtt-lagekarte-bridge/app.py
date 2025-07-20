import paho.mqtt.client as mqtt
import requests
import json
import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv ("MQTT_TOPIC", "msh/gps")
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MLO_USERNAME = os.getenv("MLO_USERNAME", "Default")

def send_GPS_Information_to_mobile_lagekarte(mlo_tid, lat, lon, username):
    url = (
            f"http://api.mobile-lagekarte.de/InserData.php"
            f"?id={mlo_tid}$lat={lat:.6f}$long={lon:.6f}&orga={username}"
        )
    try: 
        respone = request.post(url)
        print(f"Sent to Lagekarte: {url} -> {response.status_code}")
    except Exception as e:
        print(f"Error sending to Lagekarte: {e}")


def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode("utf-8")
    print(f"Recieved ({topic}): {message}")
    try: 
        payload = json.loads(msg.payload.decode())
        mlo_tid = payload.get("from", "UNKNOWN")
        position = payload.get("payload", {}).get("position", {})
        lat = position.get("latitude")
        lon = position.get("longitude")

        if lat is not None and lon is not None:
            send_to_mobile_lagekarte(mlo_tid, lat, lon, MLO_USERNAME)
        else:
            print("No Balid position in payload")
    
    except Exception as e:
        print(f"Failed to parse message: {e}")


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " +str(rc))
    client.subscribe(topic)

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscription acknowledged (mid={mid}, qos={granted_qos})")

def on_log(client, userdata, level, buf):
    print(f"MQTT Log: {buf}")


client = mqtt.Client()
if MQTT_USER and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    print("Logging into MQTT with user: " + MQTT_USER)

client.on_message = on_message
client.on_subscribe = on_subscribe
#client.on_log = on_log


print(f"Connecting to MQTT {MQTT_BROKER}:{MQTT_PORT}, topic '{MQTT_TOPIC}'...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC, qos=1)
print("Connected...")
client.loop_forever()
