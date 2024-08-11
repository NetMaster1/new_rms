from django.contrib import admin
from . models import Expense, Shop, Supplier, Product, ProductCategory, Services, DocumentType, Expense, Teko_pay, Voucher, Contributor, Month, Year

class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sale_k', 'TID', 'commission', 'retail', 'subdealer', 'cash_register', 'shift_status', 'active', 'offline', 'shift_status_updated',)

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei', 'for_mp_sale', 'ozon_id')
    search_fields = ('imei', 'name',)
    list_select_related = True
    list_editable = ('imei', 'category', 'name')

class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bonus_percent')

class ServicesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'retail_price', 'bonus_percent')

class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class Teko_payAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class VoucherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class ContributorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

class MonthAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'number_of_days',)
    list_editable = ('number_of_days',)

class YearAdmin(admin.ModelAdmin):
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
admin.site.register(Teko_pay, Teko_payAdmin)
admin.site.register(Month, MonthAdmin)
admin.site.register(Year, YearAdmin)


