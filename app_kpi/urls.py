from django.urls import path
from . import views


urlpatterns = [
    path ('', views.monthly_kpi, name='monthly_kpi'),
    path ('kpi_excel_input', views.kpi_excel_input, name='kpi_excel_input'),
    path ('kpi_adjustment', views.kpi_adjustment, name='kpi_adjustment'),
    path ('kpi_execution', views.kpi_execution, name='kpi_execution'),
  
]