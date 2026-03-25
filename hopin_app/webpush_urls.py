from django.urls import path

from webpush.views import ServiceWorkerView, save_info

urlpatterns = [
    path("save_information", save_info, name="save_webpush_info"),
    path("service-worker.js", ServiceWorkerView.as_view(), name="service_worker"),
]
