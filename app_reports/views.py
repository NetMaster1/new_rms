from app_personnel.models import BonusAccount
from django.db.models import query
from app_reference.models import DocumentType, ProductCategory, Shop, Supplier, Product
from app_cash.models import Cash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from app_product.models import (
    Product,
    RemainderHistory,
    RemainderCurrent,
    Sale,
    Transfer,
    Delivery,
    Document,
)
from app_clients.models import Customer
from .models import ProductHistory
from django.contrib import messages
import pandas as pd
import xlwt

# Create your views here.


def reports(request):
    return render(request, "reports/reports.html")


def close_report(request):
    return redirect("index")

def save_in_excel(request):
    pass

def sale_report(request):
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    suppliers=Supplier.objects.all()
    users = User.objects.all()
    if request.method == "POST":
        queryset_list = Sale.objects.all()
        sum = 0
        category = request.POST["category"]
        shop = request.POST["shop"]
        if shop:
            shop=Shop.objects.get(id=shop)
        supplier = request.POST["supplier"]
        if supplier:
            supplier=Supplier.objects.get(id=supplier)
        user = request.POST["user"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
            # if imei:
            #     queryset_list = queryset_list.filter(imei__icontains=imei)
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
        for item in queryset_list:
            sum += item.sub_total
       
        query = queryset_list.values(
            "category", "supplier", "imei", "name", "quantity", "price", "sub_total", "user"
        )
        data=pd.DataFrame.from_records(query)
       # data = pd.DataFrame(query)
        #indicate the directory where the file will be uploaded to
        data.to_excel("C:/Users/NetUser/Sale_report.xlsx", index=False)
        #content=myfile.read()
        context = {
            "categories": categories,
            "shops": shops,
            'suppliers': suppliers,
            "users": users,
            "queryset_list": queryset_list,
            "sum": sum,
        }
        return render(request, "reports/sale_report.html", context)
    else:
        context = {
            "categories": categories,
            "shops": shops,
            'suppliers': suppliers,
            "users": users,
        }
        return render(request, "reports/sale_report.html", context)

def delivery_report(request):
    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    #deliveries = Delivery.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    queryset_list=RemainderHistory.objects.filter(rho_type=doc_type.id)
    if request.method == "POST":
        #shop = request.POST["shop"]
        category = request.POST["category"]
        supplier = request.POST["supplier"]
        #user = request.POST["user"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        if supplier:
            queryset_list=queryset_list.filter(supplier=supplier)
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        if category:
            queryset_list=queryset_list.filter(category=category)
        context = {
            "categories": categories,
            "suppliers": suppliers,
            "queryset_list": queryset_list,
            "sum": sum,
        }
        return render(request, "reports/delivery_report.html", context)
    else:
        context = {
            "categories": categories,
            "suppliers": suppliers,
            "queryset_list": queryset_list,
        }
    return render(request, "reports/delivery_report.html", context)

def remainder_report(request):
    categories = ProductCategory.objects.all()
    products=Product.objects.all()
    shops = Shop.objects.all()
    #queryset_list = RemainderHistory.objects.all()
    queryset_list = RemainderCurrent.objects.all()
    if request.method == "POST":
        date = request.POST["date"]
        category = request.POST["category"]
        #shop = request.POST["shop"]
        #shop=Shop.objects.get(id=shop)
        imei = request.POST["imei"]
        if date:
            array=[]
            queryset_list=RemainderHistory.objects.filter(created__lte=date)
            #queryset_list = queryset_list.filter(created__lte=date)
            for product in products:
                print(product.imei)
                for shop in shops:
                    print(shop)
                    if queryset_list.filter(imei=product.imei, shop=shop).exists():
                        print('True')
                        queryset=queryset_list.filter(imei=product.imei, shop=shop)
                        rho = queryset.latest("created")
                        print(rho.created)
                        array.append(rho)
                    # else:
                    #     print('False')
            print(array)
                
                    

        # if imei:
        #     queryset_list = queryset_list.filter(imei=imei)
        # if category:
        #     category = ProductCategory.objects.get(id=category)
        #     queryset_list = queryset_list.filter(category=category)
        # if shop:
        #     shop = Shop.objects.get(id=shop)
        #     queryset_list = queryset_list.filter(shop=shop)

            context = {
                'array': array,
                #"queryset_list": queryset_list,
                "shops": shops,
                #"categories": categories,
            }
            return render(request, "reports/remainder_report.html", context)
        context = {
            "queryset_list": queryset_list,
            "shops": shops,
            #"categories": categories,
        }
        return render(request, "reports/remainder_report.html", context)
    else:
        context = {
            #"queryset_list": queryset_list,
            "shops": shops,
            "categories": categories,
        }
        return render(request, "reports/remainder_report.html", context)

def item_report(request):
    if request.method == "POST":
        imei = request.POST["imei"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        imei=request.POST['imei']
        queryset_list = RemainderHistory.objects.filter(imei=imei).order_by('created')
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        context = {
            "queryset_list": queryset_list, 
        }
        return render(request, "reports/item_report.html", context)
    else:
        return render(request, "reports/item_report.html")


def bonus_report(request):
    users = User.objects.all()
    sales = Sale.objects.all()
    for user in users:
        sales = sales.filter(user=user)
        bonus_account = BonusAccount.objects.get(user=user)
        bonus_account.smarts = 0
        bonus_account.phones = 0
        bonus_account.acces = 0
        bonus_account.sims = 0
        bonus_account.modems = 0
        bonus_account.insurance = 0
        bonus_account.esset = 0
        bonus_account.wink = 0
        bonus_account.service = 0
        bonus_account.other = 0
        for sale in sales:
            if sale.category.name == "Смартфоны":
                bonus_account.smarts += sale.staff_bonus
            elif sale.category.name == "Трубки":
                bonus_account.phones += sale.staff_bonus
            elif sale.category.name == "Аксы":
                bonus_account.acces += sale.staff_bonus
            elif sale.category.name == "Сим_карты":
                bonus_account.sims += sale.staff_bonus
            elif sale.category.name == "Модемы":
                bonus_account.modems += sale.staff_bonus
            elif sale.category.name == "Страховки":
                bonus_account.insurance += sale.staff_bonus
            elif sale.category.name == "Esset":
                bonus_account.esset += sale.staff_bonus
            elif sale.category.name == "Подписки":
                bonus_account.wink += sale.staff_bonus
            elif sale.category.name == "Услуги":
                bonus_account.service += sale.staff_bonus
            else:
                bonus_account.other += sale.staff_bonus
        bonus_account.save()
    bonus_accounts = BonusAccount.objects.all()
    context = {"users": users, "bonus_accounts": bonus_accounts}

    return render(request, "reports/bonus_report.html", context)


def cash_report(request):
    shops = Shop.objects.all()
    queryset_list = Cash.objects.all()
    context = {"queryset_list": queryset_list, "shops": shops}

    return render(request, "reports/cash_report.html", context)


def card_report(request):
    pass


def credit_report(request):
    pass
