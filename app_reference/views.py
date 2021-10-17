from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from . models import Product, ProductCategory
from app_product.models import RemainderHistory, RemainderCurrent
from app_clients.models import Customer
from django.contrib import messages

# Create your views here.
def reference (request):
    return render(request, 'reference.html')

def products (request):
    products=Product.objects.all()
    categories=ProductCategory.objects.all()
    if request.method == "POST":
        category = request.POST["category"]
        imei = request.POST["imei"]
        if imei:
            try:
                product=Product.objects.get(imei=imei)
                return redirect ('product_card', product.id )
            except:
                messages.error(request, "Наименование с данным IMEI отсутствует в базе данных")
        else:
            if category:
                category=ProductCategory.objects.get(id=category)
                products=Product.objects.filter(category=category)
                context = {
                    'categories': categories,
                    'products': products
                }
                return render (request, 'reference/products.html', context )
            else:
                context = {
                    'categories': categories,
                    'products': products
                }  
    context={
        'products': products,
        'categories': categories
    }
    return render (request, 'reference/products.html', context )

def update_product (request, id):
    if request.method == "POST":
        product=Product.objects.get(id=id)
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category=ProductCategory.objects.get(id=category)
        product.name=name
        product.category=category
        product.imei=imei
        product.save()
        if RemainderCurrent.objects.filter(imei=product.imei).exists():
            remainders=RemainderCurrent.objects.filter(imei=product.imei)
            for item in remainders:
                item.category=category
                item.save()
    return redirect ('products')

def product_card (request, id):
    categories=ProductCategory.objects.all()
    product=Product.objects.get(id=id)
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category=ProductCategory.objects.get(id=category)
        product.name=name
        product.category=category
        product.imei=imei
        product.save()
        return redirect ('products')

    context = {
        'categories': categories,
        'product': product
    }
    return render(request, 'reference/product_card.html', context)

def clients (request):
    clients=Customer.objects.all()
    context = {
        'clients': clients
    }
    return render (request, 'reference/payment.html', context)

