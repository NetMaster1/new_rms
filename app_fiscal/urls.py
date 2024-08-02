from django.urls import path
from . import views

urlpatterns = [

    
    path ('fiscal_day_open', views.fiscal_day_open, name='fiscal_day_open'),
    path ('fiscal_day_close', views.fiscal_day_close, name='fiscal_day_close'),
    path ('reportX', views.reportX, name='reportX'),
    path ('z_report', views.z_report, name='z_report'),
    path ('get_shift_status', views.get_shift_status, name='get_shift_status'),

]