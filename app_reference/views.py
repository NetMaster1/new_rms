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
    products=Product.objects.all()
    context={
        'products': products,
    }
    return render (request, 'reference/products.html', context )

def clients (request):
    clients=Customer.objects.all()
    context = {
        'clients': clients
    }
    return render (request, 'reference/payment.html', context)

