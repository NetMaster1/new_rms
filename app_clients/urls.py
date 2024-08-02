from django.urls import path
from . import views

urlpatterns = [
    path ('', views.new_client, name='new_client'),
    path ('new_client_sale/<int:identifier_id>', views.new_client_sale, name='new_client_sale'),
    path ('calculate_discount', views.calculate_discount, name='calculate_discount'),
    path ('client_history', views.client_history, name='client_history'),
    path ('repeated_purchase', views.repeated_purchase, name='repeated_purchase'),
  
]