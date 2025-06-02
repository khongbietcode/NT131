import os
import django
import json
import threading
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime
import time
from django.utils import timezone
import ssl
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webquanly.settings')
django.setup()

from app.models import CardEvent, CardUser, PersonalAttendanceSetting

# Cấu hình MQTT - ĐẢM BẢO TOPIC BẮT ĐẦU BẰNG USERNAME
MQTT_BROKER = '0c1804ec304d42579831c43b09c0c5b3.s1.eu.hivemq.cloud' 
MQTT_PORT = 8883 
MQTT_USERNAME = 'Taicute123'
MQTT_PASSWORD = 'Tai123123'

# Sửa các topic theo đúng định dạng
BASE_TOPIC = f"{MQTT_USERNAME}/"
MQTT_TOPIC = f"{BASE_TOPIC}rfid/uid"
ESP32_DATA_TOPIC = f"{BASE_TOPIC}esp32/data"
ESP32_STATUS_TOPIC = f"{BASE_TOPIC}esp32/status"

channel_layer = get_channel_layer()

# Tạo client duy nhất
mqtt_client = mqtt.Client(client_id=f"server_{random.randint(1000,9999)}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully to MQTT broker!')
        client.subscribe(MQTT_TOPIC)
        client.subscribe(ESP32_DATA_TOPIC)
    else:
        print(f'Failed to connect, return code {rc}')

def on_message(client, userdata, msg):
    print(f"Received message: {msg.topic} - {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        card_id = payload.get('card_id')
        
        if not card_id:
            print("Received message without card_id")
            return

        try:
            card_user = CardUser.objects.select_related('user').get(card_id=card_id)
            user_name = card_user.user.username
            print(f"User found: {user_name} ({card_id})")
            
            # Tạo sự kiện thẻ
            CardEvent.objects.create(card_id=card_id, user=card_user.user)
            
            # Gửi qua WebSocket
            async_to_sync(channel_layer.group_send)(
                'esp32_data',
                {
                    'type': 'esp32_message',
                    'data': {
                        'card_id': card_id,
                        'user_name': user_name
                    }
                }
            )
            
            # Xử lý trạng thái điểm danh
            now = timezone.localtime()
            today = now.date()
            setting = PersonalAttendanceSetting.objects.filter(
                user=card_user.user, 
                date=today
            ).first()
            
            status = "Không có cấu hình"
            if setting:
                checkin_dt = datetime.combine(today, setting.checkin_time)
                now_naive = now.replace(tzinfo=None)
                
                if now_naive < checkin_dt:
                    status = "sớm"
                elif now_naive > checkin_dt:
                    status = "trễ"
                else:
                    status = "đúng giờ"
            
            # Gửi trạng thái về ESP32
            publish_message(ESP32_STATUS_TOPIC, status)
            print(f"Sent status: {status}")
            
        except CardUser.DoesNotExist:
            print(f"User not found: {card_id}")
            publish_message(ESP32_STATUS_TOPIC, "người dùng không tồn tại")
        except Exception as e:
            print(f"Error: {e}")
            publish_message(ESP32_STATUS_TOPIC, "lỗi hệ thống")
            
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        print(f"Processing error: {e}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected with code {rc}")
    if rc != 0:
        print("Reconnecting...")
        reconnect_with_backoff()

def reconnect_with_backoff():
    """Kết nối lại với cơ chế backoff"""
    max_attempts = 5
    base_delay = 2
    
    for attempt in range(max_attempts):
        try:
            print(f"Reconnect attempt {attempt+1}/{max_attempts}")
            mqtt_client.reconnect()
            print("Reconnected successfully!")
            return
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            print(f"Reconnect failed: {e}, retrying in {delay}s")
            time.sleep(delay)
    
    print("Max reconnect attempts reached")

def publish_message(topic, message):
    try:
        result = mqtt_client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published: {topic} - {message}")
        else:
            print(f"Publish failed: {mqtt.error_string(result.rc)}")
    except Exception as e:
        print(f"Publish error: {e}")

def start_mqtt():
    # Cấu hình TLS
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    mqtt_client.tls_set_context(ssl_context)
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Thiết lập callback
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    
    try:
        print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Connection failed: {e}")
        reconnect_with_backoff()

# Hàm gửi ping định kỳ
def send_ping():
    while True:
        try:
            if mqtt_client.is_connected():
                publish_message(f"{BASE_TOPIC}ping", "alive")
            time.sleep(45)
        except Exception as e:
            print(f"Ping error: {e}")
        time.sleep(5)

def run_mqtt_forever():
    start_mqtt()
    ping_thread = threading.Thread(target=send_ping, daemon=True)
    ping_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        mqtt_client.disconnect()

if __name__ == "__main__":
    run_mqtt_forever()