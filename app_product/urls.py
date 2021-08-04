from django.urls import path
from . import views

urlpatterns = [
    path ('', views.index, name='index'),
    path ('identifier_delivery', views.identifier_delivery, name='identifier_delivery'),
    path ('check_delivery/<int:identifier_id>', views.check_delivery, name='check_delivery'),
    path ('delivery/<int:identifier_id>', views.delivery, name='delivery'),
    path ('delivery_input/<int:identifier_id>', views.delivery_input, name='delivery_input'),
    path ('delete_line_delivery/<int:imei>/<int:identifier_id>', views.delete_line_delivery, name='delete_line_delivery'),
    path ('enter_new_product/<int:identifier_id>', views.enter_new_product, name='enter_new_product'),
    path ('clear_delivery/<int:identifier_id>', views.clear_delivery, name='clear_delivery'),
    path ('change_delivery/<int:document_id>', views.change_delivery, name='change_delivery'),
    path ('delete_delivery/<int:document_id>', views.delete_delivery, name='delete_delivery'),
    path ('delete_line_change_delivery/<int:document_id>/<int:imei>/<int:shop_id>', views.delete_line_change_delivery, name='delete_line_change_delivery'),
   

    path ('identifier_sale', views.identifier_sale, name='identifier_sale'),
    path ('check_sale/<int:identifier_id>', views.check_sale, name='check_sale'),
    path ('sale/<int:identifier_id>', views.sale, name='sale'),
    path ('delete_line_sale/<int:imei>/<int:identifier_id>', views.delete_line_sale, name='delete_line_sale'),
    path ('clear_sale/<int:identifier_id>', views.clear_sale, name='clear_sale'),

    path ('identifier_transfer', views.identifier_transfer, name='identifier_transfer'),
    path ('check_transfer/<int:identifier_id>', views.check_transfer, name='check_transfer'),
    path ('transfer/<int:identifier_id>', views.transfer, name='transfer'),
    path ('transfer_input/<int:identifier_id>', views.transfer_input, name='transfer_input'),
    path ('delete_line_transfer/<int:imei>/<int:identifier_id>', views.delete_line_transfer, name='delete_line_transfer'),
    path ('clear_transfer/<int:identifier_id>', views.clear_transfer, name='clear_transfer'),
    path ('change_transfer/<int:document_id>', views.change_transfer, name='change_transfer'),
    path ('delete_transfer/<int:document_id>', views.delete_transfer, name='delete_transfer'),

    path ('log', views.log, name='log'),
    path ('open_document/<int:document_id>', views.open_document, name='open_document'),
    path ('file_uploading', views.file_uploading, name='file_uploading'),

    path ('close_without_save/<int:identifier_id>', views.close_without_save, name='close_without_save'),

    path ('cashback/<int:identifier_id>', views.cashback, name='cashback'),
    path ('noCashback/<int:identifier_id>', views.noCashback, name='noCashback'),
    path ('payment/<int:identifier_id>/<int:client_id>', views.payment, name='payment'),
    path ('sale_input_cash/<int:identifier_id>', views.sale_input_cash, name='sale_input_cash'),
   
    # path ('cashback_off/<int:identifier_id>/<int:client_id>', views.cashback_off, name='cashback_off'),


    path ('identifier_recognition', views.identifier_recognition, name='identifier_recognition'),
    path ('clear_recognition/<int:identifier_id>', views.clear_recognition, name='clear_recognition'),
    path ('recognition/<int:identifier_id>', views.recognition, name='recognition'),

    
    path ('close_edited_document', views.close_edited_document, name='close_edited_document'),
    
]