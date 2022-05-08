from django.urls import path
from . import views

urlpatterns = [

    path ('close_report', views.close_report, name='close_report'),
    path ('close_remainder_report', views.close_remainder_report, name='close_remainder_report'),
    #path ('close_report_dynamic/<int:report_id>', views.close_report_dynamic, name='close_report_dynamic'),

    path ('sale_report', views.sale_report, name='sale_report'),

    path ('daily_report', views.daily_report, name='daily_report'),
    path ('save_in_excel_daily_rep', views.save_in_excel_daily_rep, name='save_in_excel_daily_rep'),

    path ('daily_pay_card_rep_general', views.daily_pay_card_rep_general, name='daily_pay_card_rep_general'),
    path ('daily_pay_card_rep_per_shop', views.daily_pay_card_rep_per_shop, name='daily_pay_card_rep_per_shop'),
    path ('daily_shop_rep', views.daily_shop_rep, name='daily_shop_rep'),
    path ('delivery_report', views.delivery_report, name='delivery_report'),

    path ('remainder_report', views.remainder_report, name='remainder_report'),
    path ('remainder_report_output/<int:shop_id>/<int:category_id>/<date>', views.remainder_report_output, name='remainder_report_output'),
    path ('remainder_list/<int:shop_id>/<int:category_id>', views.remainder_list, name='remainder_list'),
    path ('remainder_report_dynamic)', views.remainder_report_dynamic, name='remainder_report_dynamic'),
    path ('remainder_report_excel/<int:shop_id>/<int:category_id>/<date>', views.remainder_report_excel, name='remainder_report_excel'),

    path ('item_report', views.item_report, name='item_report'),
    path ('bonus_report', views.bonus_report, name='bonus_report'),
    path ('bonus_report_excel', views.bonus_report_excel, name='bonus_report_excel'),
    path ('salary_report', views.salary_report, name='salary_report'),
    path ('cash_report', views.cash_report, name='cash_report'),
    path ('card_report', views.card_report, name='card_report'),
    path ('credit_report', views.credit_report, name='credit_report'),

    #path ('update_retail_price/<int:imei>/<int:shop_id>/<int:category_id>', views.update_retail_price, name='update_retail_price'),
    path ('update_retail_price', views.update_retail_price, name='update_retail_price'),
    

]