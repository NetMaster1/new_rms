from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from . models import Product
from app_product.models import RemainderHistory, RemainderCurrent
from app_clients.models import Customer
from django.contrib import messages

# Create your views here.
def reference (request):
    return render(request, 'reference.html')

def products (request):
    products=Product.objects.all()
    remainders=RemainderCurrent.objects.all()
    context={
        'products': products,
        'remainders': remainders
    }
    return render (request, 'reference/products.html', context )

def clients (request):
    clients=Customer.objects.all()
    context = {
        'clients': clients
    }
    return render (request, 'reference/payment.html', context)

