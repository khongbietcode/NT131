from django.apps import AppConfig
from django.conf import settings

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'  # thay 'app' bằng tên thư mục app thật sự của bạn

    def ready(self):
        from .mqtt_client import get_mqtt_client
        mqtt_client = get_mqtt_client()
