from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path ('personnel', views.personnel, name='personnel'),
    path('logout', views.logout, name='logout'),
    path('my_bonus', views.my_bonus, name='my_bonus'),
    path('motivation', views.motivation, name='motivation'),
]
 