from django.contrib import admin
from . models import Shop, Supplier, Product, ProductCategory


class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sale_k')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'imei')

class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cashback_percent', 'bonus_percent')


admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)


