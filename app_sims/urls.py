from django.urls import path
from . import views

urlpatterns = [
    path ('', views.sim_return_list, name='sim_return_list'),
    path ('sim_return_report', views.sim_return_report, name='sim_return_report'),
    path ('change_sim_return_posted/<int:document_id>/', views.change_sim_return_posted, name='change_sim_return_posted'),
    path ('activation_list', views.activation_list, name='activation_list'),
  
]