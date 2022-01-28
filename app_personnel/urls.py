from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path ('personnel', views.personnel, name='personnel'),
    path ('shop_choice', views.shop_choice, name='shop_choice'),
    path('logout', views.logout, name='logout'),
    path('my_bonus', views.my_bonus, name='my_bonus'),
    path('motivation', views.motivation, name='motivation'),
    path('number_of_work_days', views.number_of_work_days, name='number_of_work_days'),
    path('cash_back_bonus', views.cash_back_bonus, name='cash_back_bonus'),
]
 