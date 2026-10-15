from django.urls import path
from . import views


urlpatterns = [
    path ('synchronize_rho_latest_with_rco', views.synchronize_rho_latest_with_rco, name='synchronize_rho_latest_with_rco'),
    path ('excel_list_rco', views.excel_list_rco, name='excel_list_rco'),
  
]