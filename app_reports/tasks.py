from celery import shared_task
from django.shortcuts import render, redirect, get_object_or_404
import requests
from requests import request
from app_reference.models import (
    Shop,
    ProductCategory,
    Product
)
from app_product.models import (
    RemainderHistory,
)

@shared_task
def remainder_report_output_celery_task(shop_id, category_id, date):
    output_path='reports/celery_page.html'
    from django.template import loader
    date = date
    shop = Shop.objects.get(id=shop_id)
    category = ProductCategory.objects.get(id=category_id)
    array = []
    #products = Product.objects.filter(category=category).order_by("name").iterator(chunk_size=10) # order_by name lets us created an array sorted in alphabeticatl order for further processing as a table
    products = Product.objects.filter(category=category).order_by("name")# order_by name lets us created an array sorted in alphabeticatl order for further processing as a table
    n=0
    for product in products:
        imei = product.imei
        if RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).exists():
            rho=RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).latest('created')
            if rho.current_remainder > 0:
                n+=1
                print(f'{n}: {rho.name}')
                array.append(rho)
      
   