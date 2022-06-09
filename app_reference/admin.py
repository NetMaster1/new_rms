from django.contrib import admin
from . models import Expense, Shop, Supplier, Product, ProductCategory, Services, DocumentType, Expense, Voucher, Contributor

class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sale_k', 'retail')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei',)

class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bonus_percent')

class ServicesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'retail_price', 'bonus_percent')

class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class VoucherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class ContributorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Services, ServicesAdmin)
admin.site.register(DocumentType, DocumentTypeAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Voucher, VoucherAdmin)
admin.site.register(Contributor, ContributorAdmin)


