from django.apps import AppConfig


class HopinAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hopin_app'
    def ready(self):
        import hopin_app.signals