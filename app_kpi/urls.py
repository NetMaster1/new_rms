from django.urls import path
from . import views


urlpatterns = [
    path ('kpi_excel_input', views.kpi_excel_input, name='kpi_excel_input'),
    path ('kpi_performance_update', views.kpi_performance_update, name='kpi_performance_update'),


    path ('kpi_performance', views.kpi_performance, name='kpi_performance'),
    path ('kpi_monthly_report_per_shop', views.kpi_monthly_report_per_shop, name='kpi_monthly_report_per_shop'),

    path ('GI_report_input', views.GI_report_input, name='GI_report_input'),
    path ('GI_report_output/<identifier_id>', views.GI_report_output, name='GI_report_output'),

    path ('close_kpi_report', views.close_kpi_report, name='close_kpi_report'),
  
]