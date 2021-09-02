from django.urls import path
from . import views

urlpatterns = [
    path ('', views.index, name='index'),
    # ==================Delivery========================
    path ('identifier_delivery', views.identifier_delivery, name='identifier_delivery'),
    path ('check_delivery/<int:identifier_id>', views.check_delivery, name='check_delivery'),
    path ('delivery/<int:identifier_id>', views.delivery, name='delivery'),
    path ('delivery_input/<int:identifier_id>', views.delivery_input, name='delivery_input'),
    path ('delete_line_delivery/<int:imei>/<int:identifier_id>', views.delete_line_delivery, name='delete_line_delivery'),
    path ('enter_new_product/<int:identifier_id>', views.enter_new_product, name='enter_new_product'),
    path ('clear_delivery/<int:identifier_id>', views.clear_delivery, name='clear_delivery'),
    path ('pre_change_delivery/<int:document_id>', views.pre_change_delivery, name='pre_change_delivery'),
    path ('change_delivery/<int:document_id>/<int:identifier_id>', views.change_delivery, name='change_delivery'),
    path ('delete_delivery/<int:document_id>', views.delete_delivery, name='delete_delivery'),
    path ('delete_line_change_delivery/<int:document_id>/<int:identifier_id>/<int:imei>', views.delete_line_change_delivery, name='delete_line_change_delivery'),
    path ('check_delivery_change/<int:document_id>/<int:identifier_id>', views.check_delivery_change, name='check_delivery_change'),
    # ======================Recognition=========================
    path ('identifier_recognition', views.identifier_recognition, name='identifier_recognition'),
    path ('check_recognition/<int:identifier_id>', views.check_recognition, name='check_recognition'),
    path ('clear_recognition/<int:identifier_id>', views.clear_recognition, name='clear_recognition'),
    path ('recognition/<int:identifier_id>', views.recognition, name='recognition'),
    path ('delete_line_recognition/<int:imei>/<int:identifier_id>', views.delete_line_recognition, name='delete_line_recognition'),
    path ('recognition_input/<int:identifier_id>', views.recognition_input, name='recognition_input'),
    path ('delete_recognition/<int:document_id>', views.delete_recognition, name='delete_recognition'),
    # ============================SignOff==========================
    path ('identifier_signing_off', views.identifier_signing_off, name='identifier_signing_off'),
    path ('check_signing_off/<int:identifier_id>', views.check_signing_off, name='check_signing_off'),
    path ('clear_signing_off/<int:identifier_id>', views.clear_signing_off, name='clear_signing_off'),
    path ('signing_off/<int:identifier_id>', views.signing_off, name='signing_off'),
    path ('delete_line_signing_off/<int:imei>/<int:identifier_id>', views.delete_line_signing_off, name='delete_line_signing_off'),
    path ('signing_off_input/<int:identifier_id>', views.signing_off_input, name='signing_off_input'),
    path ('delete_signing_off/<int:document_id>', views.delete_signing_off, name='delete_signing_off'),
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


    # ==============================Return====================================
    path ('identifier_return', views.identifier_return, name='identifier_return'),
    path ('check_return/<int:identifier_id>', views.check_return, name='check_return'),
    path ('return_doc/<int:identifier_id>', views.return_doc, name='return_doc'),
    path ('delete_line_return/<int:imei>/<int:identifier_id>', views.delete_line_return, name='delete_line_return'),
    path ('clear_return/<int:identifier_id>', views.clear_return, name='clear_return'),
    path ('return_input/<int:identifier_id>', views.return_input, name='return_input'),
    path ('delete_return/<int:document_id>', views.delete_return, name='delete_return'),
    # ===========================Return=========================================
    path ('identifier_transfer', views.identifier_transfer, name='identifier_transfer'),
    path ('check_transfer/<int:identifier_id>', views.check_transfer, name='check_transfer'),
    path ('transfer/<int:identifier_id>', views.transfer, name='transfer'),
    path ('transfer_input/<int:identifier_id>', views.transfer_input, name='transfer_input'),
    path ('delete_line_transfer/<int:imei>/<int:identifier_id>', views.delete_line_transfer, name='delete_line_transfer'),
    path ('clear_transfer/<int:identifier_id>', views.clear_transfer, name='clear_transfer'),
    path ('change_transfer/<int:document_id>', views.change_transfer, name='change_transfer'),
    path ('delete_transfer/<int:document_id>', views.delete_transfer, name='delete_transfer'),
    # ===============================Revaluation==================================
    path ('identifier_revaluation', views.identifier_revaluation, name='identifier_revaluation'),
    path ('check_revaluation/<int:identifier_id>', views.check_revaluation, name='check_revaluation'),
    path ('revaluation/<int:identifier_id>', views.revaluation, name='revaluation'),
    path ('revaluation_input/<int:identifier_id>', views.revaluation_input, name='revaluation_input'),

    path ('log', views.log, name='log'),
    path ('open_document/<int:document_id>', views.open_document, name='open_document'),
    path ('file_uploading', views.file_uploading, name='file_uploading'),

    path ('close_without_save/<int:identifier_id>', views.close_without_save, name='close_without_save'),

    
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
   


    
    path ('close_edited_document/<int:identifier_id>', views.close_edited_document, name='close_edited_document'),
    
]