from django.urls import path
from . import views


urlpatterns = [
    path ('kpi_excel_input', views.kpi_excel_input, name='kpi_excel_input'),
    path ('kpi_adjustment', views.kpi_adjustment, name='kpi_adjustment'),


    path ('kpi_performance', views.kpi_performance, name='kpi_performance'),
    path ('kpi_monthly_report_per_shop', views.kpi_monthly_report_per_shop, name='kpi_monthly_report_per_shop'),
    path ('close_kpi_report/<int:identifier>', views.close_kpi_report, name='close_kpi_report'),
  
]