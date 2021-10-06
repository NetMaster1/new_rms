from app_reference.models import Product, ProductCategory
from django.shortcuts import render, redirect, get_object_or_404
import datetime
from datetime import datetime, date
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib import messages, auth
from django.contrib.auth import update_session_auth_hash, authenticate
from app_product.models import RemainderHistory, Sale
from app_reference.models import ProductCategory


# Create your views here.


def personnel (request):
    return render(request, 'personnel/personnel.html')

# Create your views here
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            request.session.set_expiry(0)  #user session terminates on browser close
            #request.session.set_expiry(600) #user session terminates every 10 min
            auth.login(request, user)
            # messages.success(request, 'You are logged in now')
            return redirect ('index')
        else:
            messages.error(request, "Неправильные учетные данные, попробуйте еще раз")
            return redirect('login')
    else:
        return render(request, 'personnel/login.html')

def logout(request):
        auth.logout(request)
        # messages.success(request, 'Вы вышли из системы')
        return redirect('login')

def my_bonus(request):
    if request.user.is_authenticated:
        categories=ProductCategory.objects.all()
        sales=Sale.objects.filter(user=request.user)
        #rhos_sales=RemainderHistory.objects.filter(user=request.user, rho_type='Поступление ТМЦ')
        #accessories=rhos.filter(category=3)
        accessories=sales.filter(category=3)#Аксы
        accessories_sum=0

        for accessory in accessories:
            accessories_sum+=accessory.sub_total
        category_accs=categories.get(id=3)
        bonus_accs=accessories_sum*category_accs.bonus_percent

        smarts_sum=0
        smarts=sales.filter(category=1)#Смартфоны
        for smart in smarts:
            smarts_sum+=smart.sub_total
        category_smarts=categories.get(id=1)
        bonus_smarts=smarts_sum*category_smarts.bonus_percent

        phones_sum=0
        phones=sales.filter(category=2)#Трубки
        for phone in phones:
            phones_sum+=phone.sub_total
        category_phones=categories.get(id=2)
        bonus_phones=phones_sum*category_phones.bonus_percent

        sims_sum=0
        sims=sales.filter(category=4)#Сим карты
        for sim in sims:
            sims_sum+=sim.sub_total
        category_sims=categories.get(id=4)
        bonus_sims=sims_sum*category_sims.bonus_percent

        context ={
            'accessories_sum': accessories_sum,
            'bonus_accs': bonus_accs,
            'smarts_sum': smarts_sum,
            'bonus_smarts': bonus_smarts,
            'phones_sum': phones_sum,
            'bonus_phones': bonus_phones,
            'sims_sum': sims_sum,
            'bonus_sims': bonus_sims
        }
        
        return render(request, 'personnel/my_bonus.html',  context)
    else:
        return redirect ('login')

def motivation (request):
    return render(request, 'personnel/motivation.html')