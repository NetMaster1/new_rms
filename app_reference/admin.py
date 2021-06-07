from django.contrib import admin
from . models import Shop, Supplier, Product, ProductCategory


class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'imei')

class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)

