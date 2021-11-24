from django.urls import path
from . import views

urlpatterns = [
    path ('', views.index, name='index'),
    path ('search', views.search, name='search'),
    path ('close_search', views.close_search, name='close_search'),
    path ('close_unposted_document/<int:document_id>', views.close_unposted_document, name='close_unposted_document'),
    path ('delete_unposted_document/<int:document_id>', views.delete_unposted_document, name='delete_unposted_document'),
    # ==================Delivery========================
    path ('delivery_auto', views.delivery_auto, name='delivery_auto'),
    path ('identifier_delivery', views.identifier_delivery, name='identifier_delivery'),
    path ('check_delivery/<int:identifier_id>', views.check_delivery, name='check_delivery'),
    path ('check_delivery_unposted/<int:document_id>', views.check_delivery_unposted, name='check_delivery_unposted'),
    path ('check_delivery_change/<int:document_id>', views.check_delivery_change, name='check_delivery_change'),
    path ('delivery/<int:identifier_id>', views.delivery, name='delivery'),
    path ('delivery_input/<int:identifier_id>', views.delivery_input, name='delivery_input'),
    path ('delete_line_delivery/<int:imei>/<int:identifier_id>', views.delete_line_delivery, name='delete_line_delivery'),
    path ('delete_line_change_delivery/<int:document_id>/<int:imei>', views.delete_line_change_delivery, name='delete_line_change_delivery'),
    path ('delete_line_unposted_delivery/<int:document_id>/<int:imei>', views.delete_line_unposted_delivery, name='delete_line_unposted_delivery'),
    path ('enter_new_product/<int:identifier_id>', views.enter_new_product, name='enter_new_product'),
    path ('clear_delivery/<int:identifier_id>', views.clear_delivery, name='clear_delivery'),
    path ('change_delivery_unposted/<int:document_id>', views.change_delivery_unposted, name='change_delivery_unposted'),
    path ('change_delivery_posted/<int:document_id>', views.change_delivery_posted, name='change_delivery_posted'),
    path ('enter_new_product_from_unposted/<int:document_id>', views.enter_new_product_from_unposted, name='enter_new_product_from_unposted'),
    path ('enter_new_product_from_posted/<int:document_id>', views.enter_new_product_from_posted, name='enter_new_product_from_posted'),
    path ('unpost_delivery/<int:document_id>', views.unpost_delivery, name='unpost_delivery'),
   
    # ======================Recognition=========================
    path ('identifier_recognition', views.identifier_recognition, name='identifier_recognition'),
    path ('check_recognition/<int:identifier_id>', views.check_recognition, name='check_recognition'),
    path ('check_recognition_unposted/<int:document_id>', views.check_recognition_unposted, name='check_recognition_unposted'),
    path ('check_recognition_posted/<int:document_id>', views.check_recognition_posted, name='check_recognition_posted'),

    path ('clear_recognition/<int:identifier_id>', views.clear_recognition, name='clear_recognition'),
    path ('recognition/<int:identifier_id>', views.recognition, name='recognition'),
    path ('delete_line_recognition/<int:imei>/<int:identifier_id>', views.delete_line_recognition, name='delete_line_recognition'),
    path ('delete_line_recognition_unposted/<int:imei>/<int:document_id>', views.delete_line_recognition_unposted, name='delete_line_recognition_unposted'),
    path ('delete_line_recognition_posted/<int:imei>/<int:document_id>', views.delete_line_recognition_posted, name='delete_line_recognition_posted'),

    path ('recognition_input/<int:identifier_id>', views.recognition_input, name='recognition_input'),
    path ('delete_recognition/<int:document_id>', views.delete_recognition, name='delete_recognition'),
    path ('change_recognition_posted/<int:document_id>', views.change_recognition_posted, name='change_recognition_posted'),
    path ('change_recognition_unposted/<int:document_id>', views.change_recognition_unposted, name='change_recognition_unposted'),
    path ('unposted_recognition/<int:document_id>', views.unpost_recognition, name='unpost_recognition'),
    
    # ============================SignOff==========================
    path ('identifier_signing_off', views.identifier_signing_off, name='identifier_signing_off'),
    path ('check_signing_off/<int:identifier_id>', views.check_signing_off, name='check_signing_off'),
    path ('check_signing_off_unposted/<int:document_id>', views.check_signing_off_unposted, name='check_signing_off_unposted'),
    path ('check_signing_off_posted/<int:document_id>', views.check_signing_off_posted, name='check_signing_off_posted'),
    path ('clear_signing_off/<int:identifier_id>', views.clear_signing_off, name='clear_signing_off'),
    path ('signing_off/<int:identifier_id>', views.signing_off, name='signing_off'),
    path ('delete_line_signing_off/<int:imei>/<int:identifier_id>', views.delete_line_signing_off, name='delete_line_signing_off'),
    path ('delete_line_unposted_signing_off/<int:imei>/<int:document_id>', views.delete_line_unposted_signing_off, name='delete_line_unposted_signing_off'),
    path ('delete_line_posted_signing_off/<int:imei>/<int:document_id>', views.delete_line_posted_signing_off, name='delete_line_posted_signing_off'),
    path ('signing_off_input/<int:identifier_id>', views.signing_off_input, name='signing_off_input'),
    path ('delete_signing_off/<int:document_id>', views.delete_signing_off, name='delete_signing_off'),
    path ('change_signing_off_posted/<int:document_id>', views.change_signing_off_posted, name='change_signing_off_posted'),
    path ('change_signing_off_unposted/<int:document_id>', views.change_signing_off_unposted, name='change_signing_off_unposted'),
    path ('unpost_signing_off/<int:document_id>', views.unpost_signing_off, name='unpost_signing_off'),

    # =====================Sale===============================================
    path ('identifier_sale', views.identifier_sale, name='identifier_sale'),
    path ('check_sale/<int:identifier_id>', views.check_sale, name='check_sale'),
    path ('sale/<int:identifier_id>', views.sale, name='sale'),
    path ('delete_line_sale/<int:imei>/<int:identifier_id>', views.delete_line_sale, name='delete_line_sale'),
    path ('clear_sale/<int:identifier_id>', views.clear_sale, name='clear_sale'),
    path ('list_sale', views.list_sale, name='list_sale'),
    
    path ('sale_input_card/<int:identifier_id>/<int:client_id>', views.sale_input_card, name='sale_input_card'),
    path ('pre_change_sale/<int:document_id>', views.pre_change_sale, name='pre_change_sale'),
    path ('change_sale/<int:document_id>/<identifier_id>/', views.change_sale, name='change_sale'),
    path ('check_sale_change/<int:document_id>/<identifier_id>/', views.check_sale_change, name='check_sale_change'),
    path ('delete_line_change_sale/<int:document_id>/<identifier_id>/<int:imei>', views.delete_line_change_sale, name='delete_line_change_sale'),
    path ('sale_interface', views.sale_interface, name='sale_interface'),

    # ==============================Return====================================
    path ('identifier_return', views.identifier_return, name='identifier_return'),
    path ('check_return/<int:identifier_id>', views.check_return, name='check_return'),
    path ('check_return_unposted/<int:document_id>', views.check_return_unposted, name='check_return_unposted'),
    path ('check_return_posted/<int:document_id>', views.check_return_posted, name='check_return_posted'),
    path ('return_doc/<int:identifier_id>', views.return_doc,  name='return_doc'),
    path ('delete_line_return/<int:imei>/<int:identifier_id>', views.delete_line_return, name='delete_line_return'),
    path ('delete_line_posted_return/<int:document_id>/<int:imei>', views.delete_line_posted_return, name='delete_line_posted_return'),
    path ('delete_line_unposted_return/<int:imei>/<int:document_id>', views.delete_line_unposted_return, name='delete_line_unposted_return'),
    path ('clear_return/<int:identifier_id>', views.clear_return, name='clear_return'),
    path ('return_input/<int:identifier_id>', views.return_input, name='return_input'),
    path ('unpost_return/<int:document_id>', views.unpost_return, name='unpost_return'),
    path ('change_return_unposted/<int:document_id>/', views.change_return_unposted, name='change_return_unposted'),
    path ('change_return_posted/<int:document_id>/', views.change_return_posted, name='change_return_posted'),


    # ===========================Return=========================================
    path ('identifier_transfer', views.identifier_transfer, name='identifier_transfer'),
    path ('check_transfer/<int:identifier_id>', views.check_transfer, name='check_transfer'),
    path ('transfer/<int:identifier_id>', views.transfer, name='transfer'),
    path ('transfer_input/<int:identifier_id>', views.transfer_input, name='transfer_input'),
    path ('delete_line_transfer/<int:imei>/<int:identifier_id>', views.delete_line_transfer, name='delete_line_transfer'),
    path ('clear_transfer/<int:identifier_id>', views.clear_transfer, name='clear_transfer'),
    path ('unpost_transfer/<int:document_id>/', views.unpost_transfer, name='unpost_transfer'),
    path ('change_transfer_unposted/<int:document_id>/', views.change_transfer_unposted, name='change_transfer_unposted'),
    path ('change_transfer_posted/<int:document_id>', views.change_transfer_posted, name='change_transfer_posted'),
    path ('check_transfer_posted/<int:document_id>', views.check_transfer_posted, name='check_transfer_posted'),
    path ('check_transfer_unposted/<int:document_id>', views.check_transfer_unposted, name='check_transfer_unposted'),
    path ('delete_line_posted_transfer/<int:document_id>/<int:imei>', views.delete_line_posted_transfer, name='delete_line_posted_transfer'),
    path ('delete_line_unposted_transfer/<int:document_id>/<int:imei>', views.delete_line_unposted_transfer, name='delete_line_unposted_transfer'),

    # ===============================Revaluation==================================
    path ('identifier_revaluation', views.identifier_revaluation, name='identifier_revaluation'),
    path ('check_revaluation/<int:identifier_id>', views.check_revaluation, name='check_revaluation'),
    path ('revaluation/<int:identifier_id>', views.revaluation, name='revaluation'),
    path ('revaluation_input/<int:identifier_id>', views.revaluation_input, name='revaluation_input'),
    path ('log', views.log, name='log'),
    path ('open_document/<int:document_id>', views.open_document, name='open_document'),
    path ('close_without_save/<int:identifier_id>', views.close_without_save, name='close_without_save'),
    # ==================================================================================

    path ('cash_off_salary', views.cash_off_salary, name='cash_off_salary'),
    path ('delete_cash_off_salary/<int:document_id>', views.delete_cash_off_salary, name='delete_cash_off_salary'),
    path ('change_cash_off_salary/<int:document_id>', views.change_cash_off_salary, name='change_cash_off_salary'),

    path ('cash_off_expenses', views.cash_off_expenses, name='cash_off_expenses'),
    path ('delete_cash_off_expenses/<int:document_id>', views.delete_cash_off_expenses, name='delete_cash_off_expenses'),
    path ('change_cash_off_expenses/<int:document_id>', views.change_cash_off_expenses, name='change_cash_off_expenses'),
    path ('cash_receipt', views.cash_receipt, name='cash_receipt'),
    path ('change_cash_receipt/<int:document_id>', views.change_cash_receipt, name='change_cash_receipt'),
    path ('delete_cash_receipt/<int:document_id>', views.delete_cash_receipt, name='delete_cash_receipt'),
    path ('cash_movement', views.cash_movement, name='cash_movement'),
    path ('delete_cash_movement/<int:document_id>', views.delete_cash_movement, name='delete_cash_movement'),
    path ('change_cash_movement/<int:document_id>', views.change_cash_movement, name='change_cash_movement'),
    



    path ('noCashback/<int:identifier_id>', views.noCashback, name='noCashback'),
    path ('payment/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.payment, name='payment'),
    path ('sale_input_cash/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.sale_input_cash, name='sale_input_cash'),
    path ('delete_sale_input/<int:document_id>', views.delete_sale_input, name='delete_sale_input'),
    path ('sale_input_credit/<int:identifier_id>/<int:client_id>', views.sale_input_credit, name='sale_input_credit'),

    path ('sale_input_complex/<int:identifier_id>/<int:client_id>', views.sale_input_complex, name='sale_input_complex'),

   
    path ('cashback/<int:identifier_id>', views.cashback, name='cashback'),
    path ('cashback_off_choice/<int:identifier_id>/<int:client_id>', views.cashback_off_choice, name='cashback_off_choice'),
    path ('cashback_off/<int:identifier_id>/<int:client_id>', views.cashback_off, name='cashback_off'),
    path ('no_cashback_off/<int:identifier_id>/<int:client_id>', views.no_cashback_off, name='no_cashback_off'),
    path ('security_code/<int:identifier_id>/<int:client_id>', views.security_code, name='security_code'),
    path ('sec_code_confirm/<int:identifier_id>/<int:client_id>', views.sec_code_confirm, name='sec_code_confirm'),
   


    
    path ('close_edited_document/<int:document_id>', views.close_edited_document, name='close_edited_document'),
    path ('inventory', views.inventory, name='inventory'),
    
]