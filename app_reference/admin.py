from django.contrib import admin
from . models import Shop, Supplier, Product, ProductCategory, DocumentType


class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sale_k')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei')

class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bonus_percent')

class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(DocumentType, DocumentTypeAdmin)


