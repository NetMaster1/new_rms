from django.urls import path
from . import views

urlpatterns = [
    path ('error', views.error, name='error'),
    path ('modify_supplier', views.modify_supplier, name='modify_supplier'),
]