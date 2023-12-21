from django.urls import path
from . import views

urlpatterns = [
    path ('', views.sim_return_list, name='sim_return_list'),
    
    path ('sim_return_report', views.sim_return_report, name='sim_return_report'),
    path ('change_sim_return_posted/<int:document_id>/', views.change_sim_return_posted, name='change_sim_return_posted'),
    path ('delete_sim_return_posted/<int:document_id>/', views.delete_sim_return_posted, name='delete_sim_return_posted'),
    #============================
    path ('sim_register_list', views.sim_register_list, name='sim_register_list'),
    path ('change_sim_register_posted/<int:document_id>/', views.change_sim_register_posted, name='change_sim_register_posted'),
    path ('delete_sim_register_posted/<int:document_id>/', views.delete_sim_register_posted, name='delete_sim_register_posted'),
    #============================
    path ('activation_list', views.activation_list, name='activation_list'),
    path ('delete_sim_reports', views.delete_sim_reports, name='delete_sim_reports'),
    path ('sim_dispatch', views.sim_dispatch, name='sim_dispatch'),
    #====================================
    path ('sim_sales_MB', views.sim_sales_MB, name='sim_sales_MB'),
    path ('sim_delivery_MB', views.sim_delivery_MB, name='sim_delivery_MB'),
    path ('sim_sign_off_MB', views.sim_sign_off_MB, name='sim_sign_off_MB'),
]