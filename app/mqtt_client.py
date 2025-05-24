
import os
import django
import json
import threading
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webquanly.settings')
django.setup()

MQTT_BROKER = 'ad66d2d5e34a426099f94af411e4ad88.s1.eu.hivemq.cloud' 
MQTT_PORT = 8883 
MQTT_TOPIC = 'rfid/uid'


MQTT_USERNAME = 'Taicute123'
MQTT_PASSWORD = 'Tai123123'

channel_layer = get_channel_layer()


mqtt_client_instance = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully to MQTT broker!')
        client.subscribe(MQTT_TOPIC)
        client.subscribe('esp32/data')
    else:
        print('Failed to connect, return code %d\n', rc)

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print(f'Received MQTT message: {data}')
    try:
        payload = json.loads(data)
        from app.models import CardEvent
        CardEvent.objects.create(
            card_id=payload.get('card_id'),
            timestamp=payload.get('timestamp')
        )
    except Exception as e:
        print('Error processing message:', e)
    async_to_sync(channel_layer.group_send)(
        'esp32_data',
        {
            'type': 'esp32_message',
            'data': {'message': data}
        }
    )

def get_mqtt_client():
    global mqtt_client_instance
    if mqtt_client_instance is None:
        mqtt_client_instance = mqtt.Client()
       
        mqtt_client_instance.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        mqtt_client_instance.tls_set()
        mqtt_client_instance.on_connect = on_connect
        mqtt_client_instance.on_message = on_message
        mqtt_client_instance.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        threading.Thread(target=mqtt_client_instance.loop_start, daemon=True).start()
    return mqtt_client_instance

def publish_message(topic, message):
    client = get_mqtt_client()
    client.publish(topic, message)

def start_mqtt():
    client = mqtt.Client()
    
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start() 
