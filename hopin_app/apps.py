from django.apps import AppConfig


class HopinAppConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='hopin_app'
    def ready(self):
        from .compat import patch_pywebpush_for_cryptography_46
        patch_pywebpush_for_cryptography_46()
        import hopin_app.signals
