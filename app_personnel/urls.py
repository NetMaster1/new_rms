from django.urls import path
from . import views

urlpatterns = [
    path ('', views.personnel, name='personnel'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('my_bonus', views.my_bonus, name='my_bonus'),
]
 