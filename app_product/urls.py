from django.urls import path
from . import views

urlpatterns = [
    path ('', views.index, name='index'),
    path ('delivery_document', views.delivery_document, name='delivery_document'),
    path ('check_delivery/<int:document_id>', views.check_delivery, name='check_delivery'),
    path ('delivery/<int:document_id>', views.delivery, name='delivery'),
    path ('sale_document', views.sale_document, name='sale_document'),
    path ('check_sale/<int:document_id>', views.check_sale, name='check_sale'),
    path ('sale/<int:document_id>', views.sale, name='sale'),
    path ('transer_document', views.transfer_document, name='transfer_document'),
    path ('check_transfer/<int:document_id>', views.check_transfer, name='check_transfer'),
    path ('transfer/<int:document_id>', views.transfer, name='transfer'),
    
    
    
]