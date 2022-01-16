import datetime
from app_reference.models import Product, ProductCategory, Shop
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib import messages, auth
from django.contrib.auth import update_session_auth_hash, authenticate
from app_product.models import RemainderHistory, Sale
from app_reference.models import ProductCategory


def personnel (request):
    return render(request, 'personnel/personnel.html')

def login(request):
    if request.method == 'POST':
        users=Group.objects.get(name="sales").user_set.all()
        shops=Shop.objects.all()
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            request.session.set_expiry(0)  #user session terminates on browser close
            #request.session.set_expiry(600) #user session terminates every 10 min
            auth.login(request, user)
            # messages.success(request, 'You are logged in now')   
            if request.user in users:
                return redirect ('shop_choice')
            else:
                return redirect("log")
        else:
            messages.error(request, "Неправильные учетные данные, попробуйте еще раз")
            return redirect('login')
    else:
        return render(request, 'personnel/login.html')

def logout(request):
        auth.logout(request)
        # messages.success(request, 'Вы вышли из системы')
        return redirect('login')

def shop_choice (request):
    if request.user.is_authenticated:
        shops=Shop.objects.all()
        if request.method=='POST':
            shop = request.POST["shop"]
            #shop=Shop.objects.get(id=shop)
            #django has already created a session dictionnary where request.user is stored. Now we may add more info (key, value). Django session store data in JSON format which means we can't store objects. We can store only primitive data types. We can't store "shop" as an object, we can store only 'shop.id'
            request.session ["session_shop"]=shop 
            return redirect ('sale_interface')
        else:
            context = {
                'shops': shops
            }
            return render(request, 'personnel/shop_choice.html', context)
    return redirect('login')

def my_bonus(request):
    if request.user.is_authenticated:
        shops=Shop.objects.all()
        categories=ProductCategory.objects.all()
        month=datetime.datetime.now().month
        year=datetime.datetime.now().year
        rhos=RemainderHistory.objects.filter(user=request.user, created__year=year, created__month=month)
        sales_array=[]
        bonus_array=[]
        total_sales=0
        total_bonus=0
        for category in categories:
            cat_sum=0
            bonus_sum=0
            category=ProductCategory.objects.get(name=category)
            cat_rhos=rhos.filter(category=category)
            for cat_rho in cat_rhos:
                cat_sum+=cat_rho.sub_total
                bonus_sum=cat_sum*category.bonus_percent*cat_rho.shop.sale_k
            sales_array.append(cat_sum)
            bonus_array.append(bonus_sum)
        for i in sales_array:
            total_sales+=i
        for n in bonus_array:
            total_bonus+=n
        context ={
            'categories': categories,
            'sales_array': sales_array,
            'bonus_array': bonus_array,
            'total_sales': total_sales,
            'total_bonus': total_bonus
        }
        
        return render(request, 'personnel/my_bonus.html',  context)
    else:
        return redirect ('login')

def motivation (request):
    return render(request, 'personnel/motivation.html')