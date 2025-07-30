from django.apps import AppConfig

class CarbonAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'carbon_app'

    def ready(self):
        import carbon_app.signals