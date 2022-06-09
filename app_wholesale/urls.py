from django.urls import path
from . import views

urlpatterns = [

    path ('', views.wholesale_page, name='wholesale_page'),
    

]