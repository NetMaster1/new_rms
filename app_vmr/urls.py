from django.urls import path
from . import views

urlpatterns = [
    path ('', views.open_vmr_check_form, name='open_vmr_check_form'),
    path ('save_vmr_daily_check_rep', views.save_vmr_daily_check_rep, name='save_vmr_daily_check_rep'),
    path ('vmr_today_reps', views.vmr_today_reps, name='vmr_today_reps'),
    #path ('change_sim_return_posted/<int:document_id>/', views.change_sim_return_posted, name='change_sim_return_posted'),

]
