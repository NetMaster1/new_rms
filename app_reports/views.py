from app_personnel.models import BonusAccount
from django.db.models import query
from app_reference.models import ProductCategory, Shop, Supplier, Product
from app_cash.models import Cash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from app_product.models import Product, Remainder, Sale, Transfer, Delivery, Document
from app_clients.models import Client
from . models import ProductHistory
from django.contrib import messages
import pandas as pd

# Create your views here.

def reports (request):
    return render (request, 'reports/reports.html')

def close_report(request):
    return redirect ('index')

def save_in_excel (request):
    pass

def sale_report(request):
    queryset_list=Sale.objects.all()
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    suppliers=Supplier.objects.all()
    users=User.objects.all()
    sum=0
    for item in queryset_list:
        sum+=item.sub_total
    if request.method=="POST":
        category = request.POST['category']
        imei = request.POST['imei']
        shop = request.POST['shop']
        supplier = request.POST['supplier']
        user = request.POST['user']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        if imei:
            queryset_list = queryset_list.filter(imei__icontains=imei)
        if category:
            queryset_list = queryset_list.filter(category=category)
        if shop:
            queryset_list = queryset_list.filter(shop=shop)
        if supplier:
            queryset_list = queryset_list.filter(supplier=supplier)
        if user:
            queryset_list = queryset_list.filter(user=user)
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        sum=0
        for item in queryset_list:
            sum+=item.sub_total
        context={
            'categories': categories,
            'shops': shops,
            'suppliers': suppliers,
            'users':users,
            'queryset_list': queryset_list,
            'sum': sum
        }
        query=queryset_list.values('category', 'supplier', 'name', 'quantity', 'price', 'sub_total', 'user')
        # data=pd.DataFrame.from_records(query)
        data=pd.DataFrame(query)
        print(data)
        data.to_excel('Sale_report.xlsx', index=False)
        # data.to_excel('Sale_report.xlsx', index=True)
        return render(request, 'reports/sale_report.html', context)
    else:
        context={
        'categories': categories,
        'shops': shops,
        'suppliers': suppliers,
        'users':users,
        'queryset_list': queryset_list,
        'sum': sum
    }
        return render (request, 'reports/sale_report.html', context)

def purchase_report(request):
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    suppliers=Supplier.objects.all()
    documents=Document.objects.filter(title='Поступление ТМЦ')
    deliveries=Delivery.objects.all()
    
    
  
    context={
        'documents': documents,
        'categories': categories,
        'shops': shops,
        'suppliers': suppliers,
        'sum': sum
        }
    return render(request, 'reports/purchase_report.html', context)

def remainder_report(request):
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    queryset_list=Remainder.objects.all()
    sum=0
    for remainder in queryset_list:
        sum+=remainder.sub_total
    if request.method=="POST":
        category = request.POST['category']
        imei = request.POST['imei']
        shop = request.POST['shop']
        # start_date = request.POST['start_date']
        if imei:
            queryset_list = queryset_list.filter(imei__icontains=imei)
        if category:
            queryset_list = queryset_list.filter(category=category)
        if shop:
            queryset_list = queryset_list.filter(shop=shop)
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        # if start_date:
        #     queryset_list = queryset_list.filter(created__gte=start_date)
        sum=0
        for item in queryset_list:
            sum+=item.sub_total
        context={
            'categories': categories,
            'shops': shops,
            'queryset_list': queryset_list,
            'sum': sum
        }
        query=queryset_list.values('category', 'name', 'shop', 'quantity_remainder', 'av_price', 'sub_total', 'retail_price')
        # data=pd.DataFrame.from_records(query)
        data=pd.DataFrame(query)
        print(data)
        data.to_excel('Remainder_report.xlsx', index=False)
        # data.to_excel('Sale_report.xlsx', index=True)
        return render(request, 'reports/remainder_report.html', context)

    else:
        context={
            'queryset_list': queryset_list,
            'shops': shops,
            'queryset_list': queryset_list,
            'sum': sum
        }
        return render (request, 'reports/remainder_report.html', context)


def item_report(request):
    if request.method=="POST":
        imei=request.POST['imei']
        product=Product.objects.get(imei=imei)
        deliveries=Delivery.objects.filter(imei=imei)
        for delivery in deliveries:
            product_history=ProductHistory.objects.create(
                document=delivery.document.title,
                document_id=delivery.document.id,
                category=product.category,
                supplier=delivery.supplier,
                name=product.name,
                imei=imei,
                quantity_in=delivery.quantity,
            )
        transfers=Transfer.objects.filter(imei=imei)
        for transfer in transfers:
             product_history=ProductHistory.objects.create(
                document=transfer.document,
                name=product.name,
                imei=product.imei,
                shop=transfer.shop_receiver,
                quantity_in=transfer.quantity
            )
        sales=Sale.objects.filter(imei=imei)
        for sale in sales:
            product_history=ProductHistory.objects.create(
                document=sale.document,
                category=product.category,
                supplier=delivery.supplier,
                name=product.name,
                imei=product.imei,
                quantity_out=sale.quantity
        
            )
        queryset_list=ProductHistory.objects.filter(imei=imei)
        return redirect ('item_report')
       
        
    else:
        return render (request, 'reports/item_report.html')

def bonus_report(request):
    users=User.objects.all()
    sales=Sale.objects.all()
    for user in users:
        sales=sales.filter(user=user)
        bonus_account=BonusAccount.objects.get(user=user)
        bonus_account.smarts=0
        bonus_account.phones=0
        bonus_account.acces=0
        bonus_account.sims=0
        bonus_account.modems=0
        bonus_account.insurance=0
        bonus_account.esset=0
        bonus_account.wink=0
        bonus_account.service=0
        bonus_account.other=0
        for sale in sales:
            if sale.category.name=='Смартфоны':
                bonus_account.smarts+=sale.staff_bonus
            elif sale.category.name=='Трубки':
                bonus_account.phones+=sale.staff_bonus
            elif sale.category.name=='Аксы':
                bonus_account.acces+=sale.staff_bonus
            elif sale.category.name=='Сим_карты':
                bonus_account.sims+=sale.staff_bonus
            elif sale.category.name=='Модемы':
                bonus_account.modems+=sale.staff_bonus
            elif sale.category.name=='Страховки':
                bonus_account.insurance+=sale.staff_bonus
            elif sale.category.name=='Esset':
                bonus_account.esset+=sale.staff_bonus
            elif sale.category.name=='Подписки':
                bonus_account.wink+=sale.staff_bonus
            elif sale.category.name=='Услуги':
                bonus_account.service+=sale.staff_bonus
            else:
                bonus_account.other+=sale.staff_bonus
        bonus_account.save()
    bonus_accounts=BonusAccount.objects.all()
    context={
        'users': users,
        'bonus_accounts': bonus_accounts
    }
  
    return render (request, 'reports/bonus_report.html', context)
    

def cash_report(request):
    shops=Shop.objects.all()
    queryset_list=Cash.objects.all()
    context={
        'queryset_list': queryset_list,
        'shops': shops
    }

    return render(request, 'reports/cash_report.html', context)

def card_report(request):
    pass

def credit_report(request):
    pass