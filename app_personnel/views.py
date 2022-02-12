import datetime
from app_reference.models import Product, ProductCategory, Shop
from app_product.models import RemainderHistory
from app_clients.models import Customer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib import messages, auth
from django.contrib.auth import update_session_auth_hash, authenticate
from app_reference.models import ProductCategory
import numpy as np
import datetime



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
            #dateTime = request.POST["datеTime"] #str format received from html
            # if dateTime:
            #     request.session ["session_dateTime"]=dateTime
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                # dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                # dateTime = datetime.datetime.now()
                # dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
            #django has already created a session dictionnary where request.user is stored. Now we may add more info (key, value). Django session store data in JSON format which means we can't store objects. We can store only primitive data types. We can't store "shop" as an object, we can store only 'shop.id'
            request.session ["session_shop"]=shop
            group=Group.objects.get(name="admin").user_set.all()
            if request.user in group:
                return redirect ('identifier_sale')
            else:
                return redirect ('sale_interface')
        else:
            context = {
                'shops': shops
            }
            return render(request, 'personnel/shop_choice.html', context)
    else:
        auth.logout(request)
        return redirect('login')

def shop_choice_signing_off (request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        shops=Shop.objects.all()
        if request.method=='POST':
            shop = request.POST["shop"]
            request.session ["session_shop"]=shop
            group=Group.objects.get(name="admin").user_set.all()
            return redirect ('identifier_signing_off')
        else:
            context = {
                'shops': shops
            }
            return render(request, 'personnel/shop_choice_signing_off.html', context)
    else:
        auth.logout(request)
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

def number_of_work_days (request):
    users=User.objects.all()
    work_days={}
    for user in users:
        dates=[]
        user_rows=RemainderHistory.objects.filter(user=user)
        #user_rows_values=user_rows.values_list('created').order_by('-created')
        for row in user_rows:
            #we format 'row.created' field from <class 'datetime.datetime'> to '<str>' & cut off time values in order to receive date in <str> format for further comparaison. Then we save the date in 'dates' array
            date=row.created.strftime('%Y-%m-%d')
            dates.append(date)
            #we use 'numpy.unique' function to count unique values
            list=np.unique(dates)
        n=len(list)
        work_days[user]=n
    context = {
        'work_days': work_days,
    }
    return render (request, 'personnel/work_days.html', context)
  
def cash_back_bonus (request):
    users=User.objects.all()
    print(users)
    rhos=RemainderHistory.objects.all()
    dict={}
    for user in users:
        clients=Customer.objects.filter(user=user)
        counter=0
        for client in clients:
            client_rows=rhos.filter(client_phone=client)
            n=client_rows.count()
            if n >= 3:
                counter+=1
                #calculating sum of bonus in roubles (30 руб. за каждые три покупки)
        bonus=counter*50
        dict[user]=bonus
        
        context = {
            'dict': dict
        }
    return render(request, 'personnel/cash_back_bonus.html', context)