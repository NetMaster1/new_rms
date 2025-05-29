from django.urls import path
from . import views


urlpatterns = [
    path ('current_qnt_correct', views.current_qnt_correct, name='current_qnt_correct'),
    path ('delete_current_qnty_table', views.delete_current_qnty_table, name='delete_current_qnty_table'),

  
]