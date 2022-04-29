from django.urls import path
from . import views

urlpatterns = [
    # path ('', views.index, name='index'),
    path ('search', views.search, name='search'),
    path ('close_search', views.close_search, name='close_search'),
    path ('close_unposted_document/<int:document_id>', views.close_unposted_document, name='close_unposted_document'),
    path ('delete_unposted_document/<int:document_id>', views.delete_unposted_document, name='delete_unposted_document'),
    path ('log', views.log, name='log'),
    path ('close_log', views.close_log, name='close_log'),
    #==================Remainde Input=====================================
    path ('remainder_input', views.remainder_input, name='remainder_input'),
    
    # ==================Delivery========================
    path ('delivery_auto', views.delivery_auto, name='delivery_auto'),
    path ('identifier_delivery', views.identifier_delivery, name='identifier_delivery'),
    path ('check_delivery/<int:identifier_id>', views.check_delivery, name='check_delivery'),
    path ('check_delivery_unposted/<int:document_id>', views.check_delivery_unposted, name='check_delivery_unposted'),
    path ('delivery/<int:identifier_id>', views.delivery, name='delivery'),
    path ('delivery_input/<int:identifier_id>', views.delivery_input, name='delivery_input'),
    path ('delete_line_delivery/<int:imei>/<int:identifier_id>', views.delete_line_delivery, name='delete_line_delivery'),
    path ('delete_line_unposted_delivery/<int:document_id>/<int:imei>', views.delete_line_unposted_delivery, name='delete_line_unposted_delivery'),
    path ('enter_new_product/<int:identifier_id>', views.enter_new_product, name='enter_new_product'),
    path ('clear_delivery/<int:identifier_id>', views.clear_delivery, name='clear_delivery'),
    path ('change_delivery_unposted/<int:document_id>', views.change_delivery_unposted, name='change_delivery_unposted'),
    path ('change_delivery_posted/<int:document_id>', views.change_delivery_posted, name='change_delivery_posted'),
    path ('enter_new_product_from_unposted/<int:document_id>', views.enter_new_product_from_unposted, name='enter_new_product_from_unposted'),
   
    path ('unpost_delivery/<int:document_id>', views.unpost_delivery, name='unpost_delivery'),
   
    # ======================Recognition=========================
    path ('identifier_recognition', views.identifier_recognition, name='identifier_recognition'),
    path ('check_recognition/<int:identifier_id>', views.check_recognition, name='check_recognition'),
    path ('enter_new_product_recognition/<int:identifier_id>', views.enter_new_product_recognition, name='enter_new_product_recognition'),
    path ('check_recognition_unposted/<int:document_id>', views.check_recognition_unposted, name='check_recognition_unposted'),

    path ('clear_recognition/<int:identifier_id>', views.clear_recognition, name='clear_recognition'),
    path ('recognition/<int:identifier_id>', views.recognition, name='recognition'),
    path ('delete_line_recognition/<int:imei>/<int:identifier_id>', views.delete_line_recognition, name='delete_line_recognition'),
    path ('delete_line_recognition_unposted/<int:imei>/<int:document_id>', views.delete_line_recognition_unposted, name='delete_line_recognition_unposted'),
    path ('recognition_input/<int:identifier_id>', views.recognition_input, name='recognition_input'),
    path ('delete_recognition/<int:document_id>', views.delete_recognition, name='delete_recognition'),
    path ('change_recognition_posted/<int:document_id>', views.change_recognition_posted, name='change_recognition_posted'),
    path ('change_recognition_unposted/<int:document_id>', views.change_recognition_unposted, name='change_recognition_unposted'),
    path ('unposted_recognition/<int:document_id>', views.unpost_recognition, name='unpost_recognition'),
    
    # ============================SignOff==========================
    path ('identifier_signing_off', views.identifier_signing_off, name='identifier_signing_off'),
    path ('check_signing_off/<int:identifier_id>', views.check_signing_off, name='check_signing_off'),
    path ('check_signing_off_unposted/<int:document_id>', views.check_signing_off_unposted, name='check_signing_off_unposted'),
    path ('clear_signing_off/<int:identifier_id>', views.clear_signing_off, name='clear_signing_off'),
    path ('signing_off/<int:identifier_id>', views.signing_off, name='signing_off'),
    path ('delete_line_signing_off/<int:imei>/<int:identifier_id>', views.delete_line_signing_off, name='delete_line_signing_off'),
    path ('delete_line_unposted_signing_off/<int:imei>/<int:document_id>', views.delete_line_unposted_signing_off, name='delete_line_unposted_signing_off'),
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
    # path ('list_sale', views.list_sale, name='list_sale'),

    path ('sale_input_cash/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.sale_input_cash, name='sale_input_cash'),
    path ('sale_input_card/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.sale_input_card, name='sale_input_card'),
    path ('sale_input_credit/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.sale_input_credit, name='sale_input_credit'),
    path ('sale_input_complex/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.sale_input_complex, name='sale_input_complex'),

    path ('change_sale_posted/<int:document_id>/', views.change_sale_posted, name='change_sale_posted'),
    path ('change_sale_unposted/<int:document_id>/', views.change_sale_unposted, name='change_sale_unposted'),
    path ('unpost_sale/<int:document_id>/', views.unpost_sale, name='unpost_sale'),

    path ('check_sale_unposted/<int:document_id>/', views.check_sale_unposted, name='check_sale_unposted'),
    path ('delete_line_change_sale_unposted/<int:document_id>/<int:imei>', views.delete_line_change_sale_unposted, name='delete_line_change_sale_unposted'),
    path ('sale_interface', views.sale_interface, name='sale_interface'),

    #==============================Services============================
    path ('identifier_service', views.identifier_service, name='identifier_service'),
    path ('service/<int:identifier_id>', views.service, name='service'), 
    path ('check_service/<int:identifier_id>', views.check_service, name='check_service'),

    # ==============================Return====================================
    path ('identifier_return', views.identifier_return, name='identifier_return'),
    path ('return_doc/<int:identifier_id>', views.return_doc, name='return_doc'),
    path ('check_return/<int:identifier_id>', views.check_return, name='check_return'),
    path ('check_return_unposted/<int:document_id>', views.check_return_unposted, name='check_return_unposted'),
    path ('delete_line_return/<int:imei>/<int:identifier_id>', views.delete_line_return, name='delete_line_return'),
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
    # path ('check_transfer_posted/<int:document_id>', views.check_transfer_posted, name='check_transfer_posted'),
    path ('check_transfer_unposted/<int:document_id>', views.check_transfer_unposted, name='check_transfer_unposted'),
    # path ('delete_line_posted_transfer/<int:document_id>/<int:imei>', views.delete_line_posted_transfer, name='delete_line_posted_transfer'),
    path ('delete_line_unposted_transfer/<int:document_id>/<int:imei>', views.delete_line_unposted_transfer, name='delete_line_unposted_transfer'),

    # ===============================Revaluation==================================
    path ('identifier_revaluation', views.identifier_revaluation, name='identifier_revaluation'),
    path ('check_revaluation/<int:identifier_id>', views.check_revaluation, name='check_revaluation'),
    path ('revaluation/<int:identifier_id>', views.revaluation, name='revaluation'),
    path ('revaluation_input/<int:identifier_id>', views.revaluation_input, name='revaluation_input'),
    path ('delete_line_revaluation/<int:imei>/<int:identifier_id>/<shop_id>', views.delete_line_revaluation, name='delete_line_revaluation'),
    #======================================================================================
    path ('open_document/<int:document_id>', views.open_document, name='open_document'),
    path ('close_without_save/<int:identifier_id>', views.close_without_save, name='close_without_save'),
    # ==================================================================================

    path ('cash_off_salary', views.cash_off_salary, name='cash_off_salary'),
    path ('change_cash_off_salary_posted/<int:document_id>', views.change_cash_off_salary_posted, name='change_cash_off_salary_posted'),
    path ('change_cash_off_salary_unposted/<int:document_id>', views.change_cash_off_salary_unposted, name='change_cash_off_salary_unposted'),
    path ('unpost_cash_off_salary/<int:document_id>', views.unpost_cash_off_salary, name='unpost_cash_off_salary'),

    #========================================================================================
    path ('cash_off_expenses', views.cash_off_expenses, name='cash_off_expenses'),
    path ('change_cash_off_expenses_posted/<int:document_id>', views.change_cash_off_expenses_posted, name='change_cash_off_expenses_posted'),
    path ('change_cash_off_expenses_unposted/<int:document_id>', views.change_cash_off_expenses_unposted, name='change_cash_off_expenses_unposted'),
     path ('unpost_cash_off_expenses/<int:document_id>', views.unpost_cash_off_expenses, name='unpost_cash_off_expenses'),
    #====================================================================================
    path ('cash_receipt', views.cash_receipt, name='cash_receipt'),
    path ('change_cash_receipt_posted/<int:document_id>', views.change_cash_receipt_posted, name='change_cash_receipt_posted'),
    path ('change_cash_receipt_unposted/<int:document_id>', views.change_cash_receipt_unposted, name='change_cash_receipt_unposted'),
    path ('unpost_cash_receipt/<int:document_id>', views.unpost_cash_receipt, name='unpost_cash_receipt'),

    #=================================================================================================
  
    path ('cash_movement', views.cash_movement, name='cash_movement'),
    path ('change_cash_movement_unposted/<int:document_id>', views.change_cash_movement_unposted, name='change_cash_movement_unposted'),
    path ('change_cash_movement_posted/<int:document_id>', views.change_cash_movement_posted, name='change_cash_movement_posted'),
    path ('unpost_cash_movement/<int:document_id>', views.unpost_cash_movement, name='unpost_cash_movement'),
    #===============================================================================================

    path ('noCashback/<int:identifier_id>', views.noCashback, name='noCashback'),
   
    path ('delete_sale_input/<int:document_id>', views.delete_sale_input, name='delete_sale_input'),
    
    #=============================================================================================
    path ('payment/<int:identifier_id>/<int:client_id>/<int:cashback_off>', views.payment, name='payment'),
    #=============================================================================================
    
    path ('cashback/<int:identifier_id>', views.cashback, name='cashback'),
    path ('cashback_off_choice/<int:identifier_id>/<int:client_id>', views.cashback_off_choice, name='cashback_off_choice'),
    path ('cashback_off/<int:identifier_id>/<int:client_id>', views.cashback_off, name='cashback_off'),
    path ('no_cashback_off/<int:identifier_id>/<int:client_id>', views.no_cashback_off, name='no_cashback_off'),
    path ('security_code/<int:identifier_id>/<int:client_id>', views.security_code, name='security_code'),
    path ('sec_code_confirm/<int:identifier_id>/<int:client_id>', views.sec_code_confirm, name='sec_code_confirm'),
   

   #=========================================================================
    path ('close_edited_document/<int:document_id>', views.close_edited_document, name='close_edited_document'),
    
    path ('identifier_inventory', views.identifier_inventory, name='identifier_inventory'),
    path ('inventory/<int:identifier_id>', views.inventory, name='inventory'),
    path ('inventory_list/<int:identifier_id>', views.inventory_list, name='inventory_list'),
    path ('inventory_input/<int:identifier_id>', views.inventory_input, name='inventory_input'),
    path ('change_inventory_posted/<int:document_id>', views.change_inventory_posted, name='change_inventory_posted'),
    path ('change_inventory_unposted/<int:document_id>', views.change_inventory_unposted, name='change_inventory_unposted'),
    path ('unpost_inventory/<int:document_id>', views.unpost_inventory, name='unpost_inventory'),

    path ('check_inventory_unposted/<int:document_id>', views.check_inventory_unposted, name='check_inventory_unposted'),
    path ('check_inventory/<int:identifier_id>', views.check_inventory, name='check_inventory'),

    path ('enter_new_product_inventory_unposted/<int:document_id>', views.enter_new_product_inventory_unposted, name='enter_new_product_inventory_unposted'),
    path ('enter_new_product_inventory/<int:document_id>', views.enter_new_product_inventory, name='enter_new_product_inventory'),
    
    path('GeneratePDF/<pk>', views.GeneratePDF.as_view(), name="GeneratePDF"),
    path('DownloadPDF/<int:document_id>', views.DownloadPDF.as_view(), name="DownloadPDF"),

]