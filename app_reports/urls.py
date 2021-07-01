from django.urls import path
from . import views

urlpatterns = [
    path ('', views.reports, name='reports'),
    path ('close_report', views.close_report, name='close_report'),
    path ('save_in_excel', views.save_in_excel, name='save_in_excel'),
    path ('sale_report', views.sale_report, name='sale_report'),
    path ('purchase_report', views.purchase_report, name='purchase_report'),
    path ('remainder_report', views.remainder_report, name='remainder_report'),
    path ('item_report', views.item_report, name='item_report'),
    path ('bonus_report', views.bonus_report, name='bonus_report'),
    path ('cash_report', views.cash_report, name='cash_report'),
    path ('card_report', views.card_report, name='card_report'),
    path ('credit_report', views.credit_report, name='credit_report'),

]