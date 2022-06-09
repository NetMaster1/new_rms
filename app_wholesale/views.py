<<<<<<< HEAD
from django.shortcuts import render, redirect
from app_reference.models import Product, ProductCategory, Shop
from app_product.models import RemainderHistory

# Create your views here.

def wholesale_page (request):
    if request.user.is_authenticated:
        shop=Shop.objects.get(name='ООС')
        phone=Product.objects.get(imei='355064173403806')
        products=Product.objects.filter(category=1)
        array=[]
        array_names={}
        if RemainderHistory.objects.filter(shop=shop, category=1, current_remainder__gt=0).exists():
            queryset=RemainderHistory.objects.filter(shop=shop, category=1, current_remainder__gt=0)
            for product in products:
                if queryset.filter(imei=product.imei).exists():
                    rho_latest=queryset.filter(imei=product.imei).latest('created')
                    if rho_latest.current_remainder > 0:
                        array.append(rho_latest)
            print('=======================')
            a=len(array)
            print(a)
            for product in products:
                n=0
                for item in array:
                    if product.name==item.name:
                        n+=item.current_remainder
                        array_names[item.name]=n
            print('=======================')
            a=len(array_names)
            print(a)


            context = {
                'products': products,
                'array': array,
                'array_names': array_names,
                'queryset': queryset,
                'phone': phone,
            }

            return render (request, 'wholesale/wholesale.html', context)
    else:
        return redirect ('login')
=======
from django.shortcuts import render, redirect
from app_reference.models import Product, ProductCategory, Shop
from app_product.models import RemainderHistory

# Create your views here.

def wholesale_page (request):
    if request.user.is_authenticated:
        shop=Shop.objects.get(name='ООС')
        phone=Product.objects.get(imei='355064173403806')
        products=Product.objects.filter(category=1)
        array=[]
        array_names={}
        if RemainderHistory.objects.filter(shop=shop, category=1, current_remainder__gt=0).exists():
            queryset=RemainderHistory.objects.filter(shop=shop, category=1, current_remainder__gt=0)
            for product in products:
                if queryset.filter(imei=product.imei).exists():
                    rho_latest=queryset.filter(imei=product.imei).latest('created')
                    if rho_latest.current_remainder > 0:
                        array.append(rho_latest)
            print('=======================')
            a=len(array)
            print(a)
            for product in products:
                n=0
                for item in array:
                    if product.name==item.name:
                        n+=item.current_remainder
                        array_names[item.name]=n
            print('=======================')
            a=len(array_names)
            print(a)


            context = {
                'products': products,
                'array': array,
                'array_names': array_names,
                'queryset': queryset,
                'phone': phone,
            }

            return render (request, 'wholesale/wholesale.html', context)
    else:
        return redirect ('login')
>>>>>>> 07ea3dc876783f7f59e43ee8188eb24b6f47dae0
