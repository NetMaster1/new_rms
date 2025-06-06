from django.urls import path
from . import views

urlpatterns = [

    path ('close_report', views.close_report, name='close_report'),
    path ('close_remainder_report', views.close_remainder_report, name='close_remainder_report'),
    #path ('close_report_dynamic/<int:report_id>', views.close_report_dynamic, name='close_report_dynamic'),

    path ('sale_report_per_shop', views.sale_report_per_shop, name='sale_report_per_shop'),
    path ('sale_report_analytic', views.sale_report_analytic, name='sale_report_analytic'),
    path ('effectiveness_report', views.effectiveness_report, name='effectiveness_report'),
    path ('sale_report_excel/<int:report_id>/', views.sale_report_excel, name='sale_report_excel'),
    path ('sale_report_per_supplier', views.sale_report_per_supplier, name='sale_report_per_supplier'),
    #path ('supplier_report_excel', views.supplier_report_excel, name='supplier_report_excel'),

    path ('daily_report', views.daily_report, name='daily_report'),
    path ('save_in_excel_daily_rep', views.save_in_excel_daily_rep, name='save_in_excel_daily_rep'),

    path ('cashback_rep', views.cashback_rep, name='cashback_rep'),
    path ('cashback_history', views.cashback_history, name='cashback_history'),
    path ('clients_per_user', views.clients_per_user, name='clients_per_user'),
    path ('clients_history_report', views.clients_history_report, name='clients_history_report'),
    path ('delete_clients_history_report', views.delete_clients_history_report, name='delete_clients_history_report'),


    path ('daily_pay_card_rep_general', views.daily_pay_card_rep_general, name='daily_pay_card_rep_general'),
    path ('daily_pay_card_rep_per_shop', views.daily_pay_card_rep_per_shop, name='daily_pay_card_rep_per_shop'),
    path ('daily_shop_rep', views.daily_shop_rep, name='daily_shop_rep'),

    path ('delivery_report', views.delivery_report, name='delivery_report'),
    path ('delivery_report_per_supplier', views.delivery_report_per_supplier, name='delivery_report_per_supplier'),

    path ('remainder_report_ver_1', views.remainder_report_ver_1, name='remainder_report_ver_1'),
    path ('remainder_report', views.remainder_report, name='remainder_report'),
    path ('remainder_report_output_ver_1/<int:shop_id>/<int:category_id>', views.remainder_report_output_ver_1, name='remainder_report_output_ver_1'),
    path ('remainder_report_output/<int:shop_id>/<int:category_id>/<date>', views.remainder_report_output, name='remainder_report_output'),
    path ('remainder_list/<int:shop_id>/<int:category_id>', views.remainder_list, name='remainder_list'),
    path ('remainder_report_dynamic)', views.remainder_report_dynamic, name='remainder_report_dynamic'),
    path ('remainder_report_excel/<int:shop_id>/<int:category_id>/<date>', views.remainder_report_excel, name='remainder_report_excel'),
    path ('remainder_genearl_report', views.remainder_general_report, name='remainder_general_report'),

    path ('item_report', views.item_report, name='item_report'),
    path ('bonus_report', views.bonus_report, name='bonus_report'),
    path ('bonus_report_excel', views.bonus_report_excel, name='bonus_report_excel'),
    path ('salary_report', views.salary_report, name='salary_report'),
    path ('cash_report', views.cash_report, name='cash_report'),
    path ('card_report', views.card_report, name='card_report'),
    path ('credit_report', views.credit_report, name='credit_report'),
    path ('payment_report', views.payment_report, name='payment_report'),

    path ('expenses_report', views.expenses_report, name='expenses_report'),

    path ('account_report_60_excel', views.account_report_60_excel, name='account_report_60_excel'),
    path ('account_report_62_excel', views.account_report_62_excel, name='account_report_62_excel'),
    path ('account_report_90_excel', views.account_report_90_excel, name='account_report_90_excel'),

]