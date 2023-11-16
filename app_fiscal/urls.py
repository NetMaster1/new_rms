from django.urls import path
from . import views

urlpatterns = [

    path ('get_shift_status', views.get_shift_status, name='get_shift_status'),
    path ('fiscal_day_open', views.fiscal_day_open, name='fiscal_day_open'),
    path ('fiscal_day_close', views.fiscal_day_close, name='close'),
    path ('x_report', views.x_report, name='x_report'),
    path ('z_report', views.z_report, name='z_report'),

]