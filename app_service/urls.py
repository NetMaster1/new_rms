from django.urls import path
from . import views


urlpatterns = [
    path ('current_qnt_correct', views.current_qnt_correct, name='kpi_excel_input'),

  
]