from django.urls import path
from . import views



urlpatterns = [
    path ('', views.reference, name='reference'),
    path ('products', views.products, name='products'),
    path ('product_list', views.product_list, name='product_list'),
    path ('update_product/<int:id>', views.update_product, name='update_product'),
    path ('product_card/<int:id>', views.product_card, name='product_card'),
    path ('clients', views.clients, name='clients'),
    path ('eans', views.eans, name='eans'),
    path ('ean_search', views.ean_search, name='ean_search'),
    path ('eans_card/<int:sku_id>', views.ean_card, name='ean_card'),
    path ('update_sku/<int:sku_id>', views.update_sku, name='update_sku'),
    path ('delete_sku/<int:sku_id>', views.delete_sku, name='delete_sku'),

]