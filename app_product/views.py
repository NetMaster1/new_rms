from turtle import pd
from django.db.models.fields import BLANK_CHOICE_DASH, NullBooleanField
from django.http import request
from app_product.admin import RemainderHistoryAdmin
from app_clients.models import Customer
from app_personnel.models import BonusAccount
from app_error.models import ErrorLog
from app_sims.models import SimSupplierReturnRecord, SimSigningOffRecord
from django.shortcuts import render, redirect, get_object_or_404
from .smsc_api import *
from .models import (
    Document,
    # IntegratedDailySaleDoc,
    RemainderHistory,
    InventoryList,
    Register,
    Identifier,
    RemainderCurrent,
    AvPrice,
)
from app_cash.models import Cash, Credit, Card, PaymentRegister
from app_reports.models import SaleReport, ReportTempId
from app_reference.models import (
    Shop,
    Supplier,
    Product,
    ProductCategory,
    Services,
    DocumentType,
    Expense,
    Teko_pay,
    Voucher,
    Contributor,
    SKU,
)
from app_cash.models import Cash, Credit, Card #CashRemainder
from app_cashback.models import Cashback
from django.contrib.auth.models import User, Group
from django.contrib import messages, auth
from django.utils import timezone
from django.contrib import messages
import decimal
import random
import pandas
import openpyxl as xls
import xlwt
from openpyxl import Workbook, load_workbook
import datetime
from datetime import date, timedelta
import pytz
from django.http import HttpResponse
from django.views import View
from twilio.rest import Client
from .utils import render_to_pdf
import xhtml2pdf.pisa as pisa
from django.db.models import Q
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import requests
from requests.auth import HTTPBasicAuth
import uuid
import time


# Create your views here.

def log(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        month=datetime.datetime.now().month
        year=datetime.datetime.now().year
        #queryset_list = Document.objects.filter(created__year=year).order_by("-created")
        queryset_list = Document.objects.all().order_by("-created")
        #============paginator module=================
        paginator = Paginator(queryset_list, 50)
        page = request.GET.get('page')
        paged_queryset_list = paginator.get_page(page)
        #=============end of paginator module===============
        doc_types = DocumentType.objects.all()
        users = User.objects.all().order_by('last_name')
        suppliers = Supplier.objects.all()
        shops = Shop.objects.all()
        if request.method == "POST":
            #shop = request.POST['shop']
            #if shop.value in request.GET:
            #shop = request.GET['shop']
            shop = request.POST.get("shop", False)
            #start_date = request.POST["start_date"]
            start_date = request.POST.get("start_date", False)
            #if start_date in request.GET:
            #start_date = request.GET['start_date']
            if start_date:
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            #if end_date in request.GET:
            #end_date = request.GET["end_date"]
            end_date = request.POST.get("end_date", False)
            if end_date:
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                end_date = end_date + timedelta (days=1)
            #if user in request.GET:
            #user = request.POST["user"]
            user = request.POST.get("user", False)
            #if supplier in request.GET:
            #supplier = request.POST["supplier"]
            supplier = request.POST.get("supplier", False)
            #if doc_type in request.GET:
            #doc_type = request.GET["doc_type"]
            doc_type = request.POST.get("doc_type", False)
            if start_date:
                queryset_list = queryset_list.filter(created__gte=start_date)
            if end_date:
                queryset_list = queryset_list.filter(created__lte=end_date)
            if doc_type:
                doc_type = DocumentType.objects.get(id=doc_type)
                queryset_list = queryset_list.filter(title=doc_type)
            if shop:
                shop=Shop.objects.get(id=shop)
                queryset_list = queryset_list.filter(Q(shop_sender=shop) | Q (shop_receiver=shop))
            if user:
                queryset_list = queryset_list.filter(user=user)
            if supplier:
                supplier = Supplier.objects.get(id=supplier)
                #doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
                queryset_list = queryset_list.filter(supplier=supplier)
              
                
            context = {
                "queryset_list": queryset_list,
                "doc_types": doc_types,
                "users": users,
                "suppliers": suppliers,
                "shops": shops,

            }
            return render(request, "documents/log.html", context)

        else:
            if 'app_productlog' in request.path:

                context = {
                    "queryset_list": paged_queryset_list,
                    "doc_types": doc_types,
                    "users": users,
                    "suppliers": suppliers,
                    "shops": shops,

                }
                return render(request, "documents/log.html", context)
       
    
    else:
        auth.logout(request)
        return redirect("login")

def sale_interface (request):
    if request.user.is_authenticated:
        # date=datetime.datetime.now()
        date=datetime.date.today()
        date_before = date - timedelta (days=1)
        #getting access of session_shop variable stored in session dictionnary
        session_shop=request.session['session_shop']
        shop=Shop.objects.get(id=session_shop)
        # idsd=IntegratedDailySaleDoc.objects.get(created=date, shop=shop)
# #======================Making a List of sales per day==================================
        doc_type=DocumentType.objects.get(name="Продажа ТМЦ")
        rhos = RemainderHistory.objects.filter(created__date=date, rho_type=doc_type, shop=shop).order_by("-category").order_by('name')
        sales_sum=0
        for rho in rhos:
            sales_sum+=rho.sub_total
         
#==============Making a list of docs per pay=====================================================
        #queryset_list = Document.objects.filter(user=request.user, created__date=date, posted=True)
        queryset_list = Document.objects.filter(created__date=date, posted=True)
        queryset_list=queryset_list.filter( Q(shop_sender=shop) | Q(shop_receiver=shop)).order_by("-created")
        cashback=0
        for doc in queryset_list:
            cashback+=doc.cashback_off

#==================Calculating Cash Remainder==========================================
        if Cash.objects.filter(shop=shop, created__lt=date).exists():
            cho_before=Cash.objects.filter(shop=shop, created__lt=date).latest("created")
            cash_remainder_start=cho_before.current_remainder
        else:
            cash_remainder_start=0
        if Cash.objects.filter(shop=shop).exists():
            cho_current=Cash.objects.filter(shop=shop).latest("created")
            current_cash_remainder=cho_current.current_remainder
        else:
            current_cash_remainder=0
#============================Calculating Pay_Cards_Remainders per day======================= 
        product=Product.objects.get(imei='11111')    
        if RemainderHistory.objects.filter(shop=shop, imei=product.imei, created__lt=date).exists():
            rho_before=RemainderHistory.objects.filter(shop=shop, imei=product.imei, created__lt=date).latest("created")
            pay_card_remainder_start=rho_before.current_remainder
        else:
            pay_card_remainder_start=0
        if RemainderHistory.objects.filter(shop=shop, imei=product.imei).exists():
            rho_current=RemainderHistory.objects.filter(shop=shop, imei=product.imei).latest("created")
            pay_card_remainder_current=rho_current.current_remainder
        else:
            pay_card_remainder_current=0
#=====================Calculating Incoming Cash per day=============================
        cash_sum=0
        if Cash.objects.filter(shop=shop, created__date=date).exists():
            chos=Cash.objects.filter(shop=shop, created__date=date)
            for i in chos:
                cash_sum+=i.cash_in
#===========================Calculaing Incoming Card Payments per day=====================
        card_sum=0
        if Card.objects.filter(shop=shop, created__date=date).exists():
            cards=Card.objects.filter(shop=shop, created__date=date)
            for i in cards:
                card_sum+=i.sum
#====================Calculating Incoming Credit Payments per day=====================
        credit_sum=0
        if Credit.objects.filter(shop=shop, created__date=date).exists():
            credits=Credit.objects.filter(shop=shop, created__date=date)
            for i in credits:
                credit_sum+=i.sum
  
        context = {
            'cash_remainder_start': cash_remainder_start,
            'current_cash_remainder': current_cash_remainder,
            'queryset_list': queryset_list,
            'shop': shop,
            'date': date,
            'card_sum': card_sum,
            'credit_sum': credit_sum,
            'cash_sum': cash_sum,
            'pay_card_remainder_start': pay_card_remainder_start,
            'pay_card_remainder_current': pay_card_remainder_current,
            'sales_sum': sales_sum,
            'rhos': rhos,
            'cashback': cashback,
        }
        return render (request, 'documents/sale_interface.html', context)
    else:
        return redirect ('login')

def search(request):
    users=Group.objects.get(name="sales").user_set.all()
    #admins=Group.objects.get(name="admin").user_set.all()
    if request.method == "POST":
        remainders_array = []
        remainders_array_final = []
        keyword = request.POST["keyword"]
        if request.user in users:
            session_shop=request.session['session_shop']
            #session_shop=request.session.get['session_shop']
            shop=Shop.objects.get(id=session_shop)
            if RemainderHistory.objects.filter(shop=shop, name__icontains=keyword).exists():
                remainders=RemainderHistory.objects.filter(name__icontains=keyword, shop=shop)
                for remainder in remainders:
                    remainders_array.append(remainder.imei)
                remainders_array = set(remainders_array)
                for i in remainders_array:
                    remainder=RemainderHistory.objects.filter(shop=shop, imei=i).latest('created')
                    if remainder.current_remainder > 0:
                        remainders_array_final.append(remainder)
            else:
                messages.error(request, "УУУУУПС. Такое наименование не найдено")
                return redirect("search")
        else:
            shops=Shop.objects.all()
            for shop in shops:
                if RemainderHistory.objects.filter(shop=shop, name__icontains=keyword).exists():
                    remainders=RemainderHistory.objects.filter(shop=shop, name__icontains=keyword)
                    for remainder in remainders:
                        remainders_array.append(remainder.imei)
            if len(remainders_array) == 0:
                messages.error(request, "УУУУУПС. Такое наименование не найдено")
                return redirect("search")
            remainders_array = set(remainders_array)
            for shop in shops:
                for i in remainders_array:
                    if RemainderHistory.objects.filter(shop=shop, imei=i).exists():
                        remainder=RemainderHistory.objects.filter(shop=shop, imei=i).latest('created')
                        if remainder.current_remainder > 0:
                            remainders_array_final.append(remainder)     
        context = {
                "remainders_array_final": remainders_array_final
                }
        return render(request, "documents/search_results.html", context)

    else:
        return render(request, "documents/search.html")

def close_search(request):
    return redirect("log")

def close_without_save(request, identifier_id):
    users=Group.objects.get(name='sales').user_set.all()
    identifier = Identifier.objects.get(id=identifier_id)
    if Register.objects.filter(identifier=identifier).exists():
        registers = Register.objects.filter(identifier=identifier)
        for register in registers:
            register.delete()
        identifier.delete()
        if request.user in users:
            return redirect ('sale_interface')
        else:
            return redirect("log")
    else:
        identifier.delete()
        if request.user in users:
            return redirect ('sale_interface')
        else:
            return redirect("log")

def close_edited_document(request, document_id):
    users=Group.objects.get(name='sales').user_set.all()
    document = Document.objects.get(id=document_id)
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document)
        for register in registers:
            register.delete()
        if request.user in users:
            return redirect("sale_interface")
        else:
            return redirect ('log')
    else:
        if request.user in users:
            return redirect("sale_interface")
        else:
            return redirect ('log')

def close_unposted_document(request, document_id):
    document = Document.objects.get(id=document_id)
    users=Group.objects.get(name="sales").user_set.all()
    #getting rid of registers which has been added but not saved yet
    registers = Register.objects.filter(document=document, new=True)
    for register in registers:
        register.delete()
    #restoring registers which has been deleted but not yet saved
    registers = Register.objects.filter(document=document, deleted=True)
    for register in registers:
        register.deleted = False
        register.save()
    if request.user in users:
        return redirect ('sale_interface')
    else:
        return redirect("log")

def clear_transfer(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("transfer", identifier.id)

def clear_delivery(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("delivery", identifier.id)

def clear_sale(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("sale", identifier.id)

def clear_recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("recognition", identifier.id)

def delete_unposted_document(request, document_id):
    document = Document.objects.get(id=document_id)
    users=Group.objects.get(name="sales").user_set.all()
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document)
        for register in registers:
            register.delete()
    if RemainderHistory.objects.filter(inventory_doc=document).exists():
        rhos=RemainderHistory.objects.filter(inventory_doc=document)
        for rho in rhos:
            #rho.update(inventory_doc = None)
            rho.inventory_doc = None
            rho.save()
    if PaymentRegister.objects.filter(document=document).exists():
        cash_temp_reg=PaymentRegister.objects.get(document=document)
        cash_temp_reg.delete()
    if Document.objects.filter(base_doc=document).exists():
        docs=Document.objects.filter(base_doc=document)
        for doc in docs:
            doc.delete()
    document.delete()
    if request.user in users:
        return redirect ('sale_interface')
    else:
        return redirect("log")

def close_log(request):
    return redirect ('log')

def open_document(request, document_id):
    document = Document.objects.get(id=document_id)
    if document.title == "Продажа ТМЦ":
        sales = document.sale_set.all()
        sales = sales.filter(document=document)
        documents = sales
    elif document.title == "Поступление ТМЦ":
        deliveries = document.delivery.all()
        deliveries = deliveries.filter(document=document)
        documents = deliveries
    else:
        transfers = document.transfer_set.all()
        transfer = transfers.filter(document=document)
        documents = transfers
    context = {"document": document, "documents": documents}
    return render(request, "documents/open_document.html", context)

#===============================================================================
def remainder_input (request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        shops=Shop.objects.all()
        categories=ProductCategory.objects.all()
        doc_type = DocumentType.objects.get(name="Ввод остатков ТМЦ")
        if request.method == "POST":
            file = request.FILES["file_name"]
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
            dateTime = request.POST["dateTime"]
            # converting dateTime from str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
            #==================End of time module================================
            # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
            df1 = pandas.read_excel(file)
            cycle = len(df1)#returns number of rows
            document = Document.objects.create(
                shop_receiver=shop,
                created=dateTime, 
                user=request.user, 
                title=doc_type,
                posted=True
            )
            document_sum = 0
            for i in range(cycle):
                row = df1.iloc[i]#reads rows of excel file one by one
                imei=row.Imei
                # if '/' in imei
                #     imei=imei.replace('/', '_')
                try:
                    product=Product.objects.get(imei=row.Imei)
                except Product.DoesNotExist:
                    product = Product.objects.create(
                        created=dateTime,
                        imei=imei, 
                        category=category, 
                        name=row.Title
                    )
                product = Product.objects.get(imei=row.Imei)
                # checking docs before remainder_history
                if RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=dateTime).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=dateTime).latest ('created')
                    pre_remainder=rho_latest_before.current_remainder
                else:
                    pre_remainder=0
                #=============Calculating av_price========================
                if AvPrice.objects.filter(imei=imei).exists():
                    av_price_obj = AvPrice.objects.get(imei=imei)
                    av_price_obj.current_remainder += int(row.Quantity)
                    av_price_obj.sum += int(row.Quantity) * int(row.Av_price)
                    av_price_obj.av_price = int(av_price_obj.sum) / int(av_price_obj.current_remainder)
                    av_price_obj.save()
                else:
                    av_price_obj = AvPrice.objects.create(
                        name=row.Title,
                        imei=imei,
                        current_remainder=int(row.Quantity),
                        sum=int(row.Quantity) * int(row.Av_price),
                        av_price=int(row.Av_price),
                    )

                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    user=request.user,
                    document=document,
                    rho_type=document.title,
                    created=dateTime,
                    shop=shop,
                    category=product.category,
                    product_id=product,
                    imei=product.imei,
                    name=product.name,
                    pre_remainder=pre_remainder,
                    incoming_quantity=row.Quantity,
                    outgoing_quantity=0,
                    current_remainder=pre_remainder + int(row.Quantity),
                    av_price=int(row.Av_price),
                    retail_price=int(row.Price),
                    sub_total=int(row.Price) * int(row.Quantity),
                )
                document_sum += int(rho.sub_total)

                # checking docs after remainder_history
                if RemainderHistory.objects.filter(imei=imei, shop=shop, created__gt=rho.created).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=imei, shop=shop, created__gt=dateTime)
                    sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                    pre_remainder=rho.current_remainder
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = pre_remainder
                        obj.current_remainder = (
                            pre_remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        pre_remainder = obj.current_remainder
            document.sum = document_sum
            document.save()
            return redirect("log")
        context = {
            'shops': shops,
            'categories': categories
        }
        return render(request, "documents/remainder_input.html", context)

    else:
        auth.logout(request)
        return redirect("login")

def change_remainder_input_posted (request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        shop=document.shop_receiver
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")

        context = {
            "document": document,
            "shop": shop,
            "dateTime": dateTime,
            'rhos': rhos
        }
        return render(request, "documents/change_remainder_input_posted.html", context)
    else:
        return redirect ('login')

def remainder_input_excel (request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        shop=document.shop_receiver
        rhos=RemainderHistory.objects.filter(document=document_id)

        #query=rhos.values ('name', 'imei', 'incoming_quantity')
        #data=pandas.DataFrame.from_records(query)
        #data.to_excel('D:/Soft/Files/Remainder.xlsx', index='False')
        #return redirect ('change_remainder_input_posted', document_id)

#=======================Uploading to Excel Module===================================
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = (
            "attachment; filename=Remainder_" + str(datetime.date.today()) + ".xls"
        )

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Remainder")

        # sheet header in the first row
        row_num = 0
        font_style = xlwt.XFStyle()

        columns = ["Name", "IMEI", "Quantity"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # sheet body, remaining rows
        font_style = xlwt.XFStyle()
        query = rhos.values_list("name", "imei", "incoming_quantity")

        for row in query:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response
#=======================End of Excel Upload Module================================

    else:
        return redirect ('login')

def unpost_remainder_input (request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        shop=document.shop_receiver
        rhos=RemainderHistory.objects.filter(document=document_id)
        for rho in rhos:
            product=Product.objects.get(imei=rho.imei)
            #checking rhos before
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
                remainder=rho_latest_before.current_remainder
            else:
                remainder=0
             #checking rhos after
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
                sequence_rhos_after = RemainderHistory.objects.filter( shop=rho.shop, imei=rho.imei, created__gt=rho.created).order_by('created')
                for obj in sequence_rhos_after:
                    obj.pre_remainder = remainder
                    obj.current_remainder = (
                        remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    obj.save()
                    remainder = obj.current_remainder
            #=============Av_price_module==================================
            av_price_obj = AvPrice.objects.get(imei=rho.imei)
            av_price_obj.current_remainder -= rho.incoming_quantity
            av_price_obj.sum -= int(rho.incoming_quantity) * int(rho.av_price)
            if av_price_obj.current_remainder > 0:
                av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
            else:
                av_price_obj.av_price=0
            rho.delete()
        document.delete()
        #document.posted=False
        #document.save()
        return redirect ('log')

    else:
        return redirect ('login')

# ================================Sale Operations=================================
def identifier_sale(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("sale", identifier.id)
    else:
        return redirect("login")

def check_sale(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    users=Group.objects.get(name="sales").user_set.all()
    if request.user.is_authenticated:
        if request.method == "POST":
            imei = request.POST["imei"]
            if '/' in imei:
                imei=imei.replace('/', '_')
            quantity = request.POST["quantity"]
            quantity = int(quantity)
            if Product.objects.filter(imei=imei).exists():
                product=Product.objects.get(imei=imei)
                session_shop=request.session['session_shop']
                shop = Shop.objects.get(id=session_shop)
                if RemainderHistory.objects.filter(imei=imei, shop=shop).exists():
                    rho_latest_before=RemainderHistory.objects.filter(imei=imei, shop=shop).latest('created')
                    if rho_latest_before.current_remainder < quantity:
                        messages.error(request,"Количество, необходимое для продажи отсутствует на данном складе",)
                        return redirect("sale", identifier.id)
                    #     if RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=dateTime).exists():
                    #         rhos_before=RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=dateTime)
                    #         remainder_history = rhos_before.latest("created")
                    #         if remainder_history.current_remainder < quantity:
                    if Register.objects.filter(identifier=identifier, product=product).exists():
                        messages.error(request,"Вы уже ввели данное наименование. Если вы хотите изменить кол-во, удалите соответствующую строку и введит IMEI еще раз, изменив кол-во.")
                        return redirect("sale", identifier.id)
                    else:
                        register = Register.objects.create(
                            #shop=shop,
                            quantity=quantity,
                            identifier=identifier,
                            product=product,
                            price=rho_latest_before.retail_price,
                            sub_total=quantity * rho_latest_before.retail_price,
                            real_quantity=rho_latest_before.current_remainder
                        )
                        return redirect("sale", identifier.id)

                else:
                    messages.error(request, "Данное наименование отсутствует на данной торговой точке")
                    return redirect("sale", identifier.id)
            else:
                messages.error(request, "Данное наименование для продажи отсутствует в базе данных")
                return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect ('login')

def sale(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all()
        sum = 0
        if Register.objects.filter(identifier=identifier).exists():
            registers = Register.objects.filter(identifier=identifier)
            numbers = registers.count()
            for register, i in zip(registers, range(numbers)):
                register.number = i + 1
                sum+=register.sub_total
                register.save()
                
            context = {
                "identifier": identifier,
                "registers": registers,
                "sum": sum,
            }
            return render(request, "documents/sale.html", context)
        else:
            context = {
            "identifier": identifier,
            "shops": shops,
            }
            return render(request, "documents/sale.html", context)
    else:
        return redirect("login")

def delete_line_sale(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.filter(identifier=identifier, product=product)
    item.delete()
    return redirect("sale", identifier.id)

def sale_input_cash(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
    #==============idsd_module======================================
        date=datetime.date.today()
        session_shop=request.session['session_shop']
        shop=Shop.objects.get(id=session_shop)
        # idsd=IntegratedDailySaleDoc.objects.get(created=date, shop=shop)
    #===================================================================
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        sum=0
        for register in registers:
            sum+=register.sub_total
        sum_minus_cashback= sum - cashback_off
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            #checking availability of items to sell
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("sale", identifier.id)

            #First Section of Cash Register Module (Checking if the shift if open less than 12 hours. Otherwise it won't print)===========
            #Checking if the shop is equipped with cash register working through web requests server
            if shop.cash_register==False:
                #checking if shift is open for more than 12 hours
                if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                    print ('Смена открыта более 12 часов')
                    messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                    return redirect ('sale_interface')
            #=============End of First Section of Cash Register Module========================================

            n = len(names)
            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    if rho_latest_before.current_remainder < int(quantities[i]):
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("sale", identifier.id)
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                    messages.error(request,  string)
                    return redirect("sale", identifier.id)
            document = Document.objects.create(
                created=dateTime,
                shop_sender=shop,
                title=doc_type,
                user=request.user,
                posted=True,
                cashback_off=cashback_off,
                client=client,
            )
            jsonData=[]#list for json structure for cash register
            document_sum = 0
            n = len(names)
            for i in range(n):
                product = Product.objects.get(imei=imeis[i])
                av_price_obj=AvPrice.objects.get(imei=imeis[i])
                # checking docs before remainder_history
                rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=document.created).latest('created')
                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    document=document,
                    created=document.created,
                    rho_type=doc_type,
                    user=request.user,
                    shop=shop,
                    product_id=product,
                    category=product.category,
                    imei=imeis[i],
                    name=names[i],
                    retail_price=prices[i],
                    av_price=av_price_obj.av_price,
                    pre_remainder=rho_latest_before.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=rho_latest_before.current_remainder
                    - int(quantities[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )

                document_sum += int(quantities[i]) * int(prices[i])
                #calculating av_price for the remainder
                av_price_obj.current_remainder -= int(quantities[i])
                av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                av_price_obj.save()
                #cash back is calculated based on the subtotal for each item not depending on the total sum
                if client.f_name != "default":
                    cashback = Cashback.objects.get(category=product.category)
                    cash_back_awarded=decimal.Decimal(int(sub_totals[i]) / 100 * int(cashback.size))
                    client.accum_cashback += cash_back_awarded
                    client.save()
                    rho.cash_back_awarded=cash_back_awarded
                    rho.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder

                #===============creating dictionaries to insert in json structure for cash register 
                retail_price=round(float(rho.retail_price), 2)#converts integer number to float number with two digits after divider
                sub_total=round(float(rho.sub_total), 2)#converts integer number to float number with two digits after divider  
                quantity=round(float(rho.outgoing_quantity), 3)#converts integer number to float number with three digits after divider
                json_dict={
                    "type": "position",
                    "name": rho.name,
                    "price": retail_price,
                    "quantity": quantity,
                    "amount": sub_total,
                    "tax": {
                        "type": "none"
                    }
                    }
                json_type = {
                    "type": "text"
                    }
                jsonData.append(json_dict)
                jsonData.append(json_type)
                #==================end of dictionnaries to insert to json structure for cash register
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
            #================Cash Register Module / Sell ===================
            if shop.cash_register==False:
                sum_to_pay_json=round(float(sum_to_pay), 2)#total sum to pay to be inserted in json structure for cash register
                #time.sleep(1)
                auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                uuid_number=uuid.uuid4()#creatring a unique identification number
                task = {
                "uuid": str(uuid_number),
                "request": [   
                {
                "type": "sell",
                "items": jsonData,

                    "payments":[{
                            "type": "cash",
                            "sum": sum_to_pay_json
                        }]
                }]}
                response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                # status_code=response.status_code
                # print(status_code)
                # text=response.text
                # print(text)
                # url=response.url
                # json=response.json()
                if shop.shift_status == True:
                    shop.shift_status = False #False means the shift is open
                    shop.save()
            #=================End of Cash Register Module==============	

            #checking chos before
            if Cash.objects.filter(shop=shop, created__lt=document.created).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=document.created).latest('created')
                cash_remainder = cho_latest_before.current_remainder
            else:
                cash_remainder = 0
            cho = Cash.objects.create(
                shop=shop,
                cho_type=doc_type,
                created=document.created,
                document=document,
                user=request.user,
                pre_remainder=cash_remainder,
                cash_in=sum_to_pay,
                current_remainder=cash_remainder + sum_to_pay,
            )
            if Cash.objects.filter(shop=shop, created__gt=document.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
            # end of operations with cash
            for register in registers:
                register.delete()
            identifier.delete()

            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect ('log')       
    else:
        auth.logout(request)
        return redirect("login")

def sale_input_credit(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        sum=0
        for register in registers:
            sum+=register.sub_total
        sum_minus_cashback = sum - cashback_off
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
            #==================End of time module================================
            #checking availability of items to sell
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("sale", identifier.id)
            n = len(names)

            #==First Section of Cash Register Module (Checking if the shift if open less than 12 hours. Otherwise it won't print)===========
            if shop.cash_register==False:
                #checking if shift is open for more than 12 hours
                if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                    print ('Смена открыта более 12 часов')
                    messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                    return redirect ('sale_interface')
            #=============End of First Section of Cash Register Module========================================
                
            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    if rho_latest_before.current_remainder < int(quantities[i]):
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("sale", identifier.id)
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                    messages.error(request,  string)
                    return redirect("sale", identifier.id)
            document = Document.objects.create(
                title=doc_type,
                shop_sender=shop,
                user=request.user, 
                created=dateTime,
                posted=True,
                cashback_off=cashback_off,
                client=client
            )
            document_sum=0
            n = len(names)
            jsonData=[]#list for json structure for cash register
            for i in range(n):
                product = Product.objects.get(imei=imeis[i])
                av_price_obj=AvPrice.objects.get(imei=imeis[i])
                # checking docs before remainder_history
                rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=document.created).latest('created')
                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    document=document,
                    created=document.created,
                    rho_type=doc_type,
                    user=request.user,
                    shop=shop,
                    product_id=product,
                    category=product.category,
                    imei=imeis[i],
                    name=names[i],
                    retail_price=prices[i],
                    av_price=av_price_obj.av_price,
                    pre_remainder=rho_latest_before.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=rho_latest_before.current_remainder
                    - int(quantities[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )
                document_sum+=int(quantities[i]) *  int (prices[i])
                #calculating av_price for the remainder
                av_price_obj.current_remainder -= int(quantities[i])
                av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                av_price_obj.save()
                #cash back is calculated based on the subtotal for each item not depending on the total sum
                if client.f_name != "default":
                    cashback = Cashback.objects.get(category=product.category)
                    cash_back_awarded=decimal.Decimal(int(sub_totals[i]) / 100 * int(cashback.size))
                    client.accum_cashback += cash_back_awarded
                    client.save()
                    rho.cash_back_awarded=cash_back_awarded
                    rho.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder
                #===============creating dictionaries to insert in json structure for cash register 
                retail_price=round(float(rho.retail_price), 2)#converts integer number to float number with two digits after divider
                sub_total=round(float(rho.sub_total), 2)#converts integer number to float number with two digits after divider  
                quantity=round(float(rho.outgoing_quantity), 3)#converts integer number to float number with three digits after divider
                json_dict={
                    "type": "position",
                    "name": rho.name,
                    "price": retail_price,
                    "quantity": quantity,
                    "amount": sub_total,
                    "tax": {
                        "type": "none"
                    }
                    }
                json_type = {
                    "type": "text"
                    }
                jsonData.append(json_dict)
                jsonData.append(json_type)
                #==================end of dictionnaries to insert to json structure for cash register
            
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback

            #================Cash Register Module / Sell ===================
            if shop.cash_register==False:
                sum_to_pay_json=round(float(sum_to_pay), 2)#total sum to pay to be inserted in json structure for cash register
                #time.sleep(1)
                auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                uuid_number=uuid.uuid4()#creatring a unique identification number
                task = {
                "uuid": str(uuid_number),
                "request": [   
                {
                "type": "sell",
                "items": jsonData,

                    "payments":[{
                            "type": "credit",
                            "sum": sum_to_pay_json
                        }]
                }]}
                response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                # status_code=response.status_code
                # print(status_code)
                # text=response.text
                # print(text)
                # url=response.url
                # json=response.json()
                if shop.shift_status == True:
                    shop.shift_status = False
                    shop.save()
            #=================End of Cash Register Module=============

            #operations with credit
            credit = Credit.objects.create(
                shop=shop,
                document=document,
                created=document.created,
                user=request.user, 
                sum=sum_to_pay
                )
            for register in registers:
                register.delete()
            identifier.delete()
            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def sale_input_card(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        client = Customer.objects.get(id=client_id)
        sum=0
        for register in registers:
            sum+=register.sub_total
        sum_minuns_cashback=sum-cashback_off
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            sub_totals = request.POST.getlist("sub_total", None)
            prices = request.POST.getlist("price", None)
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            #checking availability of items to sell
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("sale", identifier.id)
            n = len(names)
            #==First Section of Cash Register Module (Checking if the shift if open less than 12 hours. Otherwise it won't print)===========
            if shop.cash_register==False:
                #checking if shift is open for more than 12 hours
                if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                    print ('Смена открыта более 12 часов')
                    messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                    return redirect ('sale_interface')
            #=============End of First Section of Cash Register Module=======================================

            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    if rho_latest_before.current_remainder < int(quantities[i]):
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("sale", identifier.id)
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                    messages.error(request,  string)
                    return redirect("sale", identifier.id)
            document = Document.objects.create(
                title=doc_type,
                shop_sender=shop,
                user=request.user, 
                created=dateTime,
                posted=True,
                cashback_off=cashback_off,
                client=client
            )
            n = len(names)
            document_sum = 0
            jsonData=[]#list for json structure for cash register
            for i in range(n):
                product = Product.objects.get(imei=imeis[i])
                rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=document.created).latest('created')
                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    document=document,
                    created=document.created,
                    rho_type=doc_type,
                    user=request.user,
                    shop=shop,
                    product_id=product,
                    category=product.category,
                    imei=imeis[i],
                    name=names[i],
                    retail_price=prices[i],
                    #av_price=av_price_obj.av_price,
                    pre_remainder=rho_latest_before.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=rho_latest_before.current_remainder
                    - int(quantities[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )
                document_sum+=int(quantities[i]) *  int (prices[i])
                #calculating av_price for the remainder
                if AvPrice.objects.filter(imei=imeis[i]).exists():
                    av_price_obj=AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()
                else:
                    av_price_obj=AvPrice.objects.create(
                        imei=imeis[i],
                        name=names[i],
                        current_remainder=0,
                        av_price=0,
                        sum=0
                        )
                rho.av_price=av_price_obj.av_price
                rho.save()
                #cash back is calculated based on the subtotal for each item not depending on the total sum
                if client.f_name != "default":
                    cashback = Cashback.objects.get(category=product.category)
                    cash_back_awarded=decimal.Decimal(int(sub_totals[i]) / 100 * int(cashback.size))
                    client.accum_cashback += cash_back_awarded
                    client.save()
                    rho.cash_back_awarded=cash_back_awarded
                    rho.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder
                #===============creating dictionaries to insert in json structure for cash register 
                retail_price=round(float(rho.retail_price), 2)#converts integer number to float number with two digits after divider
                sub_total=round(float(rho.sub_total), 2)#converts integer number to float number with two digits after divider  
                quantity=round(float(rho.outgoing_quantity), 3)#converts integer number to float number with three digits after divider
                json_dict={
                    "type": "position",
                    "name": rho.name,
                    "price": retail_price,
                    "quantity": quantity,
                    "amount": sub_total,
                    "tax": {
                        "type": "none"
                    }
                    }
                json_type = {
                    "type": "text"
                    }
                jsonData.append(json_dict)
                jsonData.append(json_type)
                #==================end of dictionnaries to insert to json structure for cash register
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
           #================Cash Register Module / Sell ===================
            if shop.cash_register==False:
                sum_to_pay_json=round(float(sum_to_pay), 2)#total sum to pay to be inserted in json structure for cash register
                #time.sleep(1)
                auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                uuid_number=uuid.uuid4()#creatring a unique identification number
                task = {
                "uuid": str(uuid_number),
                "request": [   
                {
                "type": "sell",
                "items": jsonData,

                    "payments":[{
                            "type": "electronically",
                            "sum": sum_to_pay_json
                        }]
                }]}
                response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                # status_code=response.status_code
                # print(status_code)
                # text=response.text
                # print(text)
                # url=response.url
                # json=response.json()

                if shop.shift_status == True:
                    shop.shift_status = False
                    shop.save()
            #=================End of Cash Register Module==============	
            #operations with card
            card = Card.objects.create(
                shop=shop,
                document=document,
                created=document.created,
                user=request.user, 
                sum=sum_to_pay
                )
            for register in registers:
                register.delete()
            identifier.delete()
            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def sale_input_complex(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        client = Customer.objects.get(id=client_id)
        sum=0
        for register in registers:
            sum+=register.sub_total
        sum_minuns_cashback=sum-cashback_off
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            #cash = request.POST["cash"]
            cash=request.POST.get('cash', False)
            if cash:
                cash=int(cash)
            else:
                cash=0
            #credit = request.POST["credit"]
            credit=request.POST.get('credit', False)
            if credit:
                credit=int(credit)
            else:
                credit=0
            #card = request.POST["card"]
            card=request.POST.get('card', False)
            if card:
                card=int(card)
            else:
                card=0
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            sum_to_pay=0
            for sub_total in sub_totals:
                sum_to_pay += int(sub_total)
            if card+cash+credit+cashback_off != sum_to_pay:
                messages.error(request,  'Документ не сформирован. Сумма в чеке не совпадает с суммой продажи.')
                return redirect("payment", identifier.id, client.id, cashback_off)
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            #checking availability of items to sell
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("sale", identifier.id)
            n = len(names)
            #==First Section of Cash Register Module (Checking if the shift if open less than 12 hours. Otherwise it won't print)===========
            if shop.cash_register==False:
                #checking if shift is open for more than 12 hours
                if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                    print ('Смена открыта более 12 часов')
                    messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                    return redirect ('sale_interface')    
            #=============End of First Section of Cash Register Module========================================

            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    if rho_latest_before.current_remainder < int(quantities[i]):
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("sale", identifier.id)
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                    messages.error(request,  string)
                    return redirect("sale", identifier.id)

            #create document
            document = Document.objects.create(
                title=doc_type,
                shop_sender=shop,
                user=request.user, 
                created=dateTime,
                posted=True,
                cashback_off=cashback_off,
                client=client
            )
            jsonData=[]#list for json structure for cash register
            n = len(names)
            document_sum = 0
            for i in range(n):
                product = Product.objects.get(imei=imeis[i])
                av_price_obj=AvPrice.objects.get(imei=imeis[i])
                rho_latest_before = RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=document.created).latest('created')
                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    document=document,
                    created=document.created,
                    rho_type=doc_type,
                    user=request.user,
                    shop=shop,
                    product_id=product,
                    category=product.category,
                    imei=imeis[i],
                    name=names[i],
                    retail_price=prices[i],
                    av_price=av_price_obj.av_price,
                    pre_remainder=rho_latest_before.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=rho_latest_before.current_remainder
                    - int(quantities[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )
                document_sum+=int(quantities[i]) *  int (prices[i])
                #calculating av_price for the remainder
                av_price_obj.current_remainder -= int(quantities[i])
                av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                av_price_obj.save()
                #cash back is calculated based on the subtotal for each item not depending on the total sum
                if client.f_name != "default":
                    cashback = Cashback.objects.get(category=product.category)
                    cash_back_awarded=decimal.Decimal(int(sub_totals[i]) / 100 * int(cashback.size))
                    client.accum_cashback += cash_back_awarded
                    client.save()
                    rho.cash_back_awarded=cash_back_awarded
                    rho.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=rho.created ).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder
                #===============creating dictionaries to insert in json structure for cash register 
                retail_price=round(float(rho.retail_price), 2)#converts integer number to float number with two digits after divider
                sub_total=round(float(rho.sub_total), 2)#converts integer number to float number with two digits after divider  
                quantity=round(float(rho.outgoing_quantity), 3)#converts integer number to float number with three digits after divider
                json_dict={
                    "type": "position",
                    "name": rho.name,
                    "price": retail_price,
                    "quantity": quantity,
                    "amount": sub_total,
                    "tax": {
                        "type": "none"
                    }
                    }
                json_type = {
                    "type": "text"
                    }
                jsonData.append(json_dict)
                jsonData.append(json_type)
                #==================end of dictionnaries to insert to json structure for cash register
               
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
            #================Cash Register Module / Sell ===================
            if shop.cash_register==False:
                sum_to_pay_json=round(float(sum_to_pay), 2)#total sum to pay to be inserted in json structure for cash register
                #time.sleep(1)
                auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                uuid_number=uuid.uuid4()#creatring a unique identification number
                task = {
                "uuid": str(uuid_number),
                "request": [   
                {
                "type": "sell",
                "items": jsonData,

                    "payments":[{
                            "type": "electronically",
                            "sum": sum_to_pay_json
                        }]
                }]}
                response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                # status_code=response.status_code
                # print(status_code)
                # text=response.text
                # print(text)
                # url=response.url
                # json=response.json()
                if shop.shift_status == True:
                    shop.shift_status = False
                    shop.save()
            #=================End of Cash Register Module=============
        
            # checking chos before
            if cash > 0:
                if Cash.objects.filter(shop=shop, created__lt=document.created).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=document.created).latest('created')
                    cash_remainder=cho_latest_before.current_remainder  
                else:
                    cash_remainder = 0
                cho = Cash.objects.create(
                    shop=shop,
                    cho_type=doc_type,
                    created=document.created,
                    document=document,
                    user=request.user,
                    pre_remainder=cash_remainder,
                    cash_in=cash,
                    current_remainder=cash_remainder + int(cash),
                )
                #checking chos after
                if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder+ obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder= obj.current_remainder
                # end of operations with cash

            if card > 0:
                card = Card.objects.create(
                    shop=shop, 
                    document=document,
                    created=document.created,
                    user=request.user, 
                    sum=card)
            if credit > 0:
                credit = Credit.objects.create(
                    shop=shop,
                    created=document.created,
                    document=document, 
                    user=request.user, 
                    sum=credit
                )
            for register in registers:
                register.delete()
            identifier.delete()

            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def change_sale_unposted (request, document_id):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group = Group.objects.get(name='admin')
        document=Document.objects.get(id=document_id)
        cashback_off=document.cashback_off
        client=document.client
        doc_type=DocumentType.objects.get(name="Продажа ТМЦ")
        categories=ProductCategory.objects.all()
        registers=Register.objects.filter(document=document).exclude(deleted=True)
        temp_cash_reg=PaymentRegister.objects.get(document=document)
        shop=document.shop_sender
        shops=Shop.objects.all()
        numbers = registers.count()
        document_datetime=document.created
        document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method == "POST":
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            #cash = request.POST["cash"]
            cash=request.POST.get('cash', False)
            if cash:
                cash=int(cash)
            else:
                cash=0
            #credit = request.POST["credit"]
            credit=request.POST.get('credit', False)
            if credit:
                credit=int(credit)
            else:
                credit=0
            #card = request.POST["card"]
            card=request.POST.get('card', False)
            if card:
                card=int(card)
            else:
                card=0
            if cashback_off:
                cashback_off=int(cashback_off)
            else:
                cashback_off=0
            #===================DateTime module for Change Unposted===============================
            dateTime=request.POST['dateTime']
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #============End of DateTime module for change unposted=======================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("change_sale_unposted", document.id)
            # posting the document
            if post_check == True:
                #compairing cash, card & credit sums to document.sum
                sum=0
                n=len(sub_totals)
                for i in range(n):
                    sum+=int(sub_totals[i])
                cash_sum = int(cash) + int(credit) + int(card) + int (cashback_off)
                if cash_sum != sum:
                    messages.error(request, "Сумма в чеке не совпадает с суммой продажи.")
                    return redirect("change_sale_unposted", document.id)
                document_sum=0
                #calculating remainder_history
                n=len(names)
                for i in range(n):
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                        rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                        if rho_latest_before.current_remainder < int(quantities[i]):
                            string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                            messages.error(request,  string)
                            return redirect("change_sale_unposted", document.id)
                    else:
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("change_sale_unposted", document.id)
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj=AvPrice.objects.get(imei=imeis[i])
                    else:
                        string=f'Документ не проведен. Для товара с {imeis[i]} отсутствует av_price.'
                        messages.error(request,  string)
                        return redirect("change_sale_unposted", document.id)
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    #calculating av_price for the remainder
                    av_price_obj=AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum = av_price_obj.current_remainder * av_price_obj.av_price
                    # if av_price_obj.sum<=0:
                    #     av_price_obj.sum=0
                    #     av_price_obj.av_price = 0
                    av_price_obj.save()
                    #checking rhos before
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    # creating remainder_history
                    rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        rho_type=doc_type,
                        user=document.user,
                        shop=shop,
                        product_id=product,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        retail_price=prices[i],
                        av_price=av_price_obj.av_price,
                        pre_remainder=rho_latest_before.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=rho_latest_before.current_remainder
                        - int(quantities[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    document_sum+=rho.sub_total
                    #checking rhos after
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                        remainder=rho.current_remainder
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).order_by('created')
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder
                                + obj.incoming_quantity
                                - obj.outgoing_quantity
                            )
                            obj.save()
                            remainder = obj.current_remainder
                    # editing cashback awarded to client's account
                    #client=Customer.objects.get(phone=client_phones[i])
                    if client.f_name != "default":
                        cashback = Cashback.objects.get(category=product.category)
                        cash_back_awarded=decimal.Decimal(int(sub_totals[i]) / 100 * int(cashback.size))
                        client.accum_cashback += cash_back_awarded
                        client.save()
                        rho.cash_back_awarded=cash_back_awarded
                        rho.save()

                client.accum_cashback-=cashback_off
                client.save()
                document.sum=document_sum
                #document.sum_minus_cashback-=(int(document.sum)-int(cashback_off))
                document.posted=True
                document.created=dateTime
                document.shop_sender=shop
                document.save()
                
                if cash > 0:
                # operations with cash
                    if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                        cho_before_latest = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                        cash_pre_remainder = cho_before_latest.current_remainder
                    else:
                        cash_pre_remainder = 0
                    cho = Cash.objects.create(
                        shop=shop,
                        created=dateTime,
                        cho_type=doc_type,
                        document=document,
                        user=document.user,
                        pre_remainder=cash_pre_remainder,
                        cash_in=cash,
                        current_remainder=cash_pre_remainder + cash,
                    )
                    if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                        sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                        cash_remainder=cho.current_remainder
                        for obj in sequence_chos_after:
                            obj.pre_remainder = cash_remainder
                            obj.current_remainder = (
                                cash_remainder + obj.cash_in - obj.cash_out
                            )
                            obj.save()
                            cash_remainder = obj.current_remainder
                if credit > 0:
                    credit = Credit.objects.create(
                        user=document.user,
                        created=dateTime,
                        document=document,
                        shop=shop,
                        sum=credit
                    )
                if card >0:
                    card=Card.objects.create(
                        user=document.user,
                        created=dateTime,
                        document=document,
                        shop=shop,
                        sum=card
                    )
                #deleting reg where cash/credit/card values have been stored in order do display them in html template
                if PaymentRegister.objects.filter(document=document).exists():
                    temp_cash_reg=PaymentRegister.objects.get(document=document)
                    temp_cash_reg.delete()
            
                registers=Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
                return redirect("log")

            #saving unposted document
            else:
                payment_register=PaymentRegister.objects.get(document=document)
                if cash >=0:
                    payment_register.cash=cash
                if card >=0:
                    payment_register.card=card
                if credit >=0:
                    payment_register.credit=credit
                payment_register.save()
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    if Register.objects.filter(document=document, deleted=True).exists():
                        registers = Register.objects.filter(document=document, deleted=True)
                        for register in registers:
                            register.delete()
                    else:
                        if Register.objects.filter(document=document).exists():
                            register = Register.objects.get(document=document, product=product) 
                            register.price = prices[i]
                            register.quantity = quantities[i]
                            register.sub_total = sub_totals[i]
                            register.document = document
                            register.new = False
                            register.save()
                            document_sum += int(register.sub_total)
                document.sum = document_sum
                document.shop=shop
                document.created=dateTime
                document.save()
                # if request.user in users:
                #     return redirect ('sale_interface')
                # else:
                return redirect("log")
        else:       
            context = {
                'registers': registers,
                'document': document,
                'temp_cash_reg': temp_cash_reg,
                'shops': shops,
                'shop': shop,
                'categories': categories,
                'document_datetime': document_datetime,
                'group': group,
            }
            return render (request, 'documents/change_sale_unposted.html', context)
    else:
        auth.logout(request)
        return redirect("login")

def change_sale_posted(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        if Cash.objects.filter(document=document).exists():
            cash=Cash.objects.get(document=document)
        else:
            cash=None
        if Card.objects.filter(document=document).exists():
            card=Card.objects.get(document=document)
        else:
            card=None
        if Credit.objects.filter(document=document).exists():
            credit=Credit.objects.get(document=document)
        else:
            credit=None
        creator = document.user
        rhos = RemainderHistory.objects.filter(document=document)
        shops = Shop.objects.all()
        shop = document.shop_sender
    
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        document_datetime=document.created
        document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
        context = {
            "rhos": rhos,
            "document": document,
            "shops": shops,
            "shop_current": shop,
            "cash": cash,
            "card": card,
            "credit": credit,
            "document_datetime": document_datetime,
        }
        return render(request, "documents/change_sale_posted.html", context)

def change_payment_type(request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        doc_type=DocumentType.objects.get(name="Продажа ТМЦ")
        if document.cashback_off:
            cashback=document.cashback_off
        else:
            cashback=0
        if request.method == "POST":
            # cash = request.POST["cash"]
            # credit = request.POST["credit"]
            # card = request.POST["card"]
            cash=request.POST.get('cash', False)
            card=request.POST.get('card', False)
            credit=request.POST.get('credit', False)

            new_sum=cashback
            if cash:
                new_sum = new_sum+int(cash)
            if card:
                new_sum= new_sum+int(card)
            if credit:
                new_sum=new_sum+int(credit)
            if new_sum != document.sum:
                messages.error(request, "Введённая сумма не соответствуей изначальной. Документ не был изменён.")
                return redirect("change_sale_posted", document.id)
            
        if cash:
            if Cash.objects.filter(document=document).exists():
                cho = Cash.objects.get(document=document)
                cho.cash_in=cash
                cho.save()
            else:
                cho=Cash.objects.create (
                    document=document,
                    user=document.user,
                    created=document.created,
                    cho_type=doc_type,
                    shop=document.shop_sender,
                    cash_in=cash,
                    # pre_remainder=cash_pre_remainder,
                    # current_remainder=cash_pre_remainder + cash,
                )

            if Cash.objects.filter(shop=document.shop_sender, created__lt=document.created).exists():
                cho_before_latest = Cash.objects.filter(shop=document.shop_sender, created__lt=document.created).latest('created')
                print(cho_before_latest.document)
                cash_pre_remainder = cho_before_latest.current_remainder
            else:
                cash_pre_remainder = 0
            cho.pre_remainder=cash_pre_remainder
            cho.current_remainder=cash_pre_remainder + int(cash)
            cho.save()

            if Cash.objects.filter(shop=document.shop_sender, created__gt=document.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=document.shop_sender, created__gt=document.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
        else:
            if Cash.objects.filter(document=document).exists():
                cho = Cash.objects.get(document=document)
                cho.delete()
                if Cash.objects.filter(shop=document.shop_sender, created__lt=document.created).exists():
                    cho_before_latest = Cash.objects.filter(shop=document.shop_sender, created__lt=document.created).latest('created')
                    cash_pre_remainder = cho_before_latest.current_remainder
                else:
                    cash_pre_remainder = 0
                if Cash.objects.filter(shop=document.shop_sender, created__gt=document.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=document.shop_sender, created__gt=document.created).order_by('created')
                    cash_remainder=cash_pre_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder + obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder = obj.current_remainder

        if credit:
            if Credit.objects.filter(document=document).exists():
                credit_doc=Credit.objects.get(document=document)
                credit_doc.sum=credit
                credit_doc.save()
            else:
                credit=Credit.objects.create(
                    document=document,
                    user=document.user,
                    created=document.created,
                    shop=document.shop_sender,
                    sum=credit
                )
        else:
            if Credit.objects.filter(document=document).exists():
                credit_doc=Credit.objects.get(document=document)
                credit_doc.delete()

        if card:
            if Card.objects.filter(document=document).exists():
                card_doc=Card.objects.get(document=document)
                card_doc.sum=card
                card_doc.save()
            else:
                card_doc=Card.objects.create (
                    document=document,
                    user=document.user,
                    created=document.created,
                    shop=document.shop_sender,
                    sum=card
                )
        else:
            if Card.objects.filter(document=document).exists():
                card_doc=Card.objects.get(document=document)
                card_doc.delete()

        return redirect ('change_sale_posted', document.id)
    else:
        auth.logout(request)
        return redirect("login")

def unpost_sale (request, document_id):
    group=Group.objects.get(name='admin').user_set.all()
    document=Document.objects.get(id=document_id)
    client=document.client
    if request.user in group:
        # if request.method=='POST':
        rhos = RemainderHistory.objects.filter(document=document)
        shop=document.shop_sender
        if Cash.objects.filter(document=document).exists():
            cash = Cash.objects.get(document=document)
        else:
            cash=None
        if Credit.objects.filter(document=document).exists():
            credit=Credit.objects.get(document=document)
        else:
            credit=None
        if Card.objects.filter(document=document).exists():
            card=Card.objects.get(document=document)
        else:
            card=None
        for rho in rhos:
            # deleting existing rhos
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
                remainder=rho_latest_before.current_remainder
            else:
                remainder=0
            #checking rhos after the one being deleted
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
                sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created )
                sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                for obj in sequence_rhos_after:
                    obj.pre_remainder = remainder
                    obj.current_remainder = (
                        remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    obj.save()
                    remainder = obj.current_remainder
            product=Product.objects.get(imei=rho.imei)
            #correcting av_price model
            av_price_obj=AvPrice.objects.get(imei=rho.imei)
            av_price_obj.current_remainder+= rho.outgoing_quantity
            av_price_obj.sum=av_price_obj.current_remainder*rho.av_price
            #if av_price_obj.current_remainder > 0:
            #    av_price_obj.av_price=av_price_obj.sum / av_price_obj.current_remainder
            #else:
            #    av_price_obj.av_price =0
            av_price_obj.save()

            register=Register.objects.create(
                created=document.created,
                document=document,
                imei=rho.imei,
                product=product,
                quantity=rho.outgoing_quantity,
                price=rho.retail_price,
                sub_total=rho.sub_total,
            )
            #cashback operations
            if client.f_name != "default":
                client.accum_cashback-=rho.cash_back_awarded
                client.save()
            rho.delete()
        document.posted=False
        if client.f_name != "default":
            client.accum_cashback=client.accum_cashback+document.cashback_off
            client.save()
        #document.cashback_off=0
        document.save()

        #correcting cash/credit/card operations
        payment_register=PaymentRegister.objects.create (
            document=document
        )
        if cash:
            #checking chos before
            if Cash.objects.filter(shop=shop, created__lt=cash.created).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=cash.created).latest('created')  
                cash_remainder=cho_latest_before.current_remainder
            else:
                cash_remainder = 0 
            #checking chos after
            if Cash.objects.filter(shop=shop, created__gt=cash.created).exists():
                cash_remainder=cash_remainder
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cash.created).order_by('created')
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
            payment_register.cash=cash.cash_in
            cash.delete()
        if credit:
            payment_register.credit=credit.sum
            credit.delete()
        if card:
            payment_register.card=card.sum
            card.delete()
        payment_register.save()
        return redirect("log")
    return redirect ('login')
            
def check_sale_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    shop=document.shop_sender
    if request.method == "POST":
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if RemainderHistory.objects.filter(imei=imei, shop=shop).exists():
                rho_latest_before=RemainderHistory.objects.filter(imei=imei, shop=shop).latest('created')
                if Register.objects.filter(document=document, product=product).exists():
                    messages.error(request, "Вы уже ввели данное наименование.")
                    return redirect("change_sale_unposted", document.id)
                else:
                    register = Register.objects.create(
                        document=document, 
                        product=product,
                        price=rho_latest_before.retail_price,
                        new=True,
                        sub_total=rho_latest_before.retail_price
                    )
                    return redirect("change_sale_unposted", document.id)
            else:
                messages.error(request, "Данное наименование отсутствует на складе.")
                return redirect("change_sale_unposted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_sale_unposted", document.id)

def delete_line_change_sale_unposted(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.delete()
    return redirect("change_sale_unposted", document.id)

def delete_sale_input(request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        document = Document.objects.get(id=document_id)
        if PaymentRegister.objects.filter(document=document).exists():
            temp_cash_regs=PaymentRegister.objects.filter(document=document)
            for temp_cash_reg in temp_cash_regs:
                temp_cash_reg.delete()
        if Register.objects.filter(document=document).exists():
            registers=Register.objects.filter(document=document)
            for register in registers:
                register.delete()
        document.delete()
        return redirect ('log')
    return redirect ('login')

#==================================Services ===================================================
def identifier_service (request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("service", identifier.id)
    else:
        return redirect("login")

def service(request, identifier_id):
    if request.user.is_authenticated:
        services=Services.objects.all()
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all()
        sum = 0
        if Register.objects.filter(identifier=identifier).exists():
            registers = Register.objects.filter(identifier=identifier)
            numbers = registers.count()
            for register, i in zip(registers, range(numbers)):
                register.number = i + 1
                sum+=register.sub_total
                register.save()
                
            context = {
                "identifier": identifier,
                "registers": registers,
                "sum": sum,
            }
            return render(request, "documents/service.html", context)
        else:
            context = {
            "identifier": identifier,
            "shops": shops,
            'services': services
            }
            return render(request, "documents/service.html", context)
    else:
        return redirect("login")

def check_service(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    users=Group.objects.get(name="sales").user_set.all()
    services=Services.objects.all()
    if request.user.is_authenticated:
        if request.method == "POST":
            service = request.POST["service"]
            register = Register.objects.create(
                
            )
            return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect ('login')

#===============================CashBack Operations======================================================
#При проведении докумена с кэшбэк, списанный со счета клиента сохраняется в document.cashback_off.
#При отмене проведения документа (продажа) начисленный кэшбэк обнуляется со счета клиента (customer.accum_cashback); списанный кэшбэк возвращается на счет клиента, но одновременно остется в непроведенном в document.cashback_off.
#При проведении change_sale_unposted рассчитывается новый начисленный кэшбэк, который идет на счет клиенту; списываемый кэшбэк списывается со счета клиента (сумма берется из document.cashback_off). Таким образом, при редактировании документа change_sale_posted сумма кэшбэка к списанию не редактируется.
#При удалении документа кэшбэк с покупки не начисляется; списываемый кэшбэк не списывается со счета клиент, и одновременно удаляется из document.cashback_off вместе с документом.
#Новые клиенты кэшбэк сохраняются в таблице Cusomers. Для создания отчета по новым качественным клиентам мы берем выборку клиентов по полю cretated за данный месяц и прогоняем их по всем документам (продажа) за данный месяц. Таблица Document имеет поле client. Т.е. если мы видим, что новый клиент отметился в документе продажа за текущий месяцы, то он считается качественным.

#продажа с начислением кэшбэк 
def cashback(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        if not Register.objects.filter(identifier=identifier).exists():
            messages.error (request, 'Вы не ввели ни одного наименования для продажи.')
            return redirect ("sale", identifier.id)
        if request.method=="POST":
            phone = request.POST["phone"]
            if Customer.objects.filter(phone=phone).exists():
                client = Customer.objects.get(phone=phone)
                return redirect("cashback_off_choice", identifier.id, client.id)
            else:
                messages.error(request,"Клиент не зарегистрирован в системе. Введите данные клиента.",)
                return redirect("sale", identifier.id)
        else: 
            return redirect("sale", identifier_id)
    else:
        auth.logout(request)
        return redirect("login")
    
#продажа со списанием кэшбэк
def cashback_off_choice(request, identifier_id, client_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        client = Customer.objects.get(id=client_id)
        sum = 0
        for register in registers:
            sum += register.sub_total
        max_cashback_off = sum * 0.2
        if max_cashback_off <= client.accum_cashback:
            cashback_off = max_cashback_off
        else:
            cashback_off = client.accum_cashback

        context = {
            "identifier": identifier,
            "client": client,
            "cashback_off": cashback_off,
        }
        return render(request, "payment/cashback.html", context)

def security_code(request, identifier_id, client_id):
    import requests
    import json

    if request.user.is_authenticated:
        client = Customer.objects.get(id=client_id)
        cashback_off=client.accum_cashback
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)

        #=============SMSC API (phone calls) ()==================================
        phone=client.phone
        #api_request=requests.get("https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={}&mes=code&call=1&fmt=3")
        #url=f"https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={phone}&mes=code&call=1&fmt=3"
        #variable can't be placed directly in url string. That's why I use .format() or f'
        #base_url=f"https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={phone}&mes=code&call=1&fmt=3"
        base_url="https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={}&mes=code&call=1&fmt=3"
        url=base_url.format(phone)
        api_request=requests.get(url)
        #server's response is returned in json format

        try:
            api=json.loads(api_request.content)
            code_string=api['code']
            messages.success(request, "Сейчас покупатель получит звонок. Нужно снять трубку и выслушать код. Введите этот код.")
            print(api)
            print(code_string)
        except Exception as e:
            messages.error(request, 'Ошибка ответа сервера. В данный момент списание кэш-бэка не возможно. Попробуйте продажу без списания кэш-бэка')
            return redirect("sale", identifier.id)
        #try:
        #    api=json.loads(api_request.content)
        #    messages.error(request, api)
        #except Exception as e:
        #    api =  'Error…'
        #    messages.error(request, api)
    #========================================================================

        # if request.method=="POST":
        #==================Creating Security Code Module=================================
        #security_code = []
        #for i in range(4):
        #    a = random.randint(0, 9)
        #    security_code.append(a)
        # transforming every integer into string
        #code_string = "".join(str(i) for i in security_code)  
        #print(code_string)
        #=======================================================

        #==================SMSC API (sms)===========================
        #smsc=SMSC()
        #r=smsc.send_sms('79200711112', 'Тестовое сообщение', sender='sms')
        #r = smsc.send_sms("79200711112", "http://smsc.ru\nSMSC.RU", query="maxsms=3")
        #===============================================

        # ===========Twilio API==================
        #account_sid = "ACb9a5209252abd7219e19a812f8108acc"
        #auth_token = ""
        #client_twilio = Client(account_sid, auth_token)
        #message = client_twilio.messages.create(
        #    body=code_string, 
        #    from_="+16624993114", 
        #    to="+79200711112"
        #)
        # ================================
        context = {
            "identifier": identifier,
            "client": client,
            "cashback_off" : cashback_off,
            "code_string": code_string,
        }
        return render(request, "payment/security_code.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def sec_code_confirm(request, identifier_id, client_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    client = Customer.objects.get(id=client_id)
    if request.method == "POST":
        code_string = request.POST["code_string"]
        code = request.POST["code"]
        if code == code_string:
            messages.success(request, "Кэшбэк был списан с лицевого счета покупателя.")
            sum = 0
            for register in registers:
                sum += register.sub_total
            max_cashback_off = sum * 0.2

            if max_cashback_off <= client.accum_cashback:
                cashback_off = max_cashback_off
            else:
                cashback_off = client.accum_cashback
            cashback_off = int(cashback_off)
            client.accum_cashback = client.accum_cashback - cashback_off
            client.save()

            return redirect("payment", identifier.id, client.id, cashback_off)
        else:
            messages.error(request, "Вы ввели неверный код. Попробуйте еще раз.")
            return redirect("sale", identifier.id)

def cashback_off(request, identifier_id, client_id):
    client = Customer.objects.get(id=client_id)
    registers = Register.objects.filter(identifier=identifier_id)
    doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
    sum = 0
    for register in registers:
        sum += register.sub_total
    max_cashback_off = sum * 0.2
    if max_cashback_off <= client.accum_cashback:
        cashback_off = max_cashback_off
    else:
        cashback_off = client.accum_cashback
    cashback_off = int(cashback_off)
    client.accum_cashback = client.accum_cashback - cashback_off
    client.save()

    return redirect("payment", identifier_id, client.id, cashback_off)

def no_cashback_off(request, identifier_id, client_id):
    identifier = Identifier.objects.get(id=identifier_id)
    client = Customer.objects.get(id=client_id)
    cashback_off = 0
    return redirect("payment", identifier.id, client.id, cashback_off)

def noCashback(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(f_name="default")
        if Register.objects.filter(identifier=identifier).exists():
            cashback_off = 0
            return redirect("payment", identifier.id, client.id, cashback_off)
        else:
            messages.error (request, 'Вы не ввели ни одного наименования для продажи')
            return redirect ('sale', identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

# ================================Payment Operations=============================================
def payment(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        shops=Shop.objects.all()
        session_shop=request.session['session_shop']
        shop = Shop.objects.get(id=session_shop)
        sum = 0
        n = registers.count()
        for register in registers:
            sum += register.sub_total
        sum_to_pay = sum - cashback_off

        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        context = {
            "identifier": identifier,
            "registers": registers,
            "client": client,
            "sum": sum,
            "cashback_off": cashback_off,
            "sum_to_pay": sum_to_pay,
            'shops': shops,
            'shop': shop,
        }
        return render(request, "payment/payment.html", context)
    else:
        return redirect("login")

# ====================================Delivery Operations==============================================
def delivery_auto(request):
    shops = Shop.objects.all()
    shop_default=Shop.objects.get(name='ООС')
    suppliers = Supplier.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    if request.method == "POST":
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        try:
            supplier = request.POST["supplier"]
            supplier = Supplier.objects.get(id=supplier)
        except:
            messages.error(request, "Введите поставщика.")
            return redirect("delivery_auto")
        try:
            category = request.POST["category"]
            category = ProductCategory.objects.get(id=category)
        except:
            messages.error(request, "Введите категорию.")
            return redirect("delivery_auto")
        file = request.FILES["file_name"]
        # print(file)
        # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        document = Document.objects.create(
            created=dateTime,
            shop_receiver=shop,
            supplier=supplier,
            user=request.user, 
            title=doc_type,
            posted=True
        )
        document_sum = 0
        n=0
        for i in range(cycle):
            n += 1
            row = df1.iloc[i]#reads each row of the df1 one by one
            imei=row.Imei
            if '/' in str(imei):
                imei=imei.replace('/', '_')
           
            if Product.objects.filter(imei=imei).exists():
                product=Product.objects.get(imei=imei)
            else:
                product = Product.objects.create(
                    name=row.Title,
                    imei=imei, 
                    category=category,
                    EAN=imei      
                )
            # checking docs before remainder_history
            if RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=document.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=document.created).latest('created')
                pre_remainder=rho_latest_before.current_remainder
            else:
                pre_remainder=0
            # creating remainder_history
            rho = RemainderHistory.objects.create(
                user=request.user,
                document=document,
                rho_type=document.title,
                created=document.created,
                shop=shop,
                category=product.category,
                supplier=supplier,
                product_id=product,
                #imei=row.Imei,
                imei=product.imei,
                #name=row.Title,
                name=product.name,
                pre_remainder=pre_remainder,
                incoming_quantity=row.Quantity,
                outgoing_quantity=0,
                current_remainder=pre_remainder + int(row.Quantity),
                wholesale_price=int(row.Price),
                sub_total=int(row.Price) * int(row.Quantity),
            )
            document_sum += int(rho.sub_total)
          
    #============Av_price_module====================
            if AvPrice.objects.filter(imei=imei).exists():
                av_price_obj = AvPrice.objects.get(imei=product.imei)
                av_price_obj.current_remainder += int(row.Quantity)
                av_price_obj.sum += int(row.Quantity) * int(row.Price)
                if av_price_obj.current_remainder > 0:
                    av_price_obj.av_price = int(av_price_obj.sum) / int(av_price_obj.current_remainder)
                else:
                    av_price_obj.av_price=int(row.Price)
                av_price_obj.save()
            else:
                av_price_obj = AvPrice.objects.create(
                    name=product.name,
                    imei=product.imei,
                    current_remainder=int(row.Quantity),
                    sum=int(row.Quantity) * int(row.Price),
                    av_price=int(row.Price),
                )
            rho.av_price=av_price_obj.av_price
            rho.save()
            # checking docs after remainder_history
            if RemainderHistory.objects.filter(imei=imei, shop=shop, created__gt=rho.created).exists():
                sequence_rhos_after = RemainderHistory.objects.filter(imei=product.imei, shop=shop, created__gt=rho.created).order_by('created')
                pre_remainder=rho.current_remainder
                for obj in sequence_rhos_after:
                    obj.pre_remainder = pre_remainder
                    obj.current_remainder = (
                        pre_remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    obj.save()
                    pre_remainder = obj.current_remainder
                mp_quantity=pre_remainder
            else:
                mp_quantity=rho.current_remainder
            #Сначала мы создаём новую позицию на площадке озон в функции (def ozon_product_create), которая содержит API метод
            #response=requests.post('https://api-seller.ozon.ru/v3/product/import', json=task, headers=headers)
            #мы не можем сразу ввести количество на маркетплейсе Ozon, так как ему требуется время для модерации

            #В процессе содания нового товара Ozon присваивает ему уникальный Ozon_id
            #Мы получаем ozon_id посредством метода: response=requests.post('https://api-seller.ozon.ru/v2/product/list', 
            # json=task_2, headers=headers) (def getting_ozon_id) и сохраняем ozon_id в модели Product

            #Ozon_id и offer_id нужны для редактирования количества товара на стоке озон посредством метода:
            #response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task_3, headers=headers)
            #offer_id это номер товара уникальный в erms. В качестве offer_id мы используем EAN товара. Для аксов EAN = IMEi

            #я пытался создать товар и задать ему количество в одной функции, но Озону нужно время для того, чтобы проверить,
            #что я создал у него на площадке, и он возвращает нужныйм нам ozon_id только через какое-то время, а не сразу
            #поэтому я разделил процесс создания товара на озоне, получения ozon_id и ввода кол-ва на озон на три отдельных функции
            #Сначала мы создаем товар (def ozon_product_create), а 
            #Затем получаем ozon_id (def getting_ozon_id)
            #Вводим документ (def deliver_auto), где загружаем поступившее кол-во товара на ООС и одновременно на озон

            #бланки "Поступление ТМЦ" и "Ввод новой номенклатуры Озон" отличаются

            #checking if product already has Ozon_id & does not have to be created again
            if product.ozon_id:
            #if product.for_mp_sale == False:
                headers = {
                    "Client-Id": "867100",
                    "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                }
        
                #update quantity of products at ozon warehouse making it equal to OOC warehouse
                task_3 = {
                    "stocks": [
                        {
                            "offer_id": str(product.EAN),
                            "product_id": str(product.ozon_id),
                            "stock": str(mp_quantity),
                            #warehouse (Гордеевская)
                            "warehouse_id": 1020001938106000
                        }
                    ]
                }
                response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task_3, headers=headers)
                #json=response.json()
                #status_code=response.status_code
                #print(status_code)
                #print(json)
             
        document.sum = document_sum
        document.save()
        return redirect("log")
    else:
        context = {
            "shops": shops,
            'shop_default': shop_default,
            "suppliers": suppliers, 
            "categories": categories,
            }
        return render(request, "documents/delivery_auto.html", context)

def identifier_delivery(request):
    identifier = Identifier.objects.create()
    return redirect("delivery", identifier.id)

def identifier_delivery_smartphones(request):
    identifier = Identifier.objects.create()
    return redirect("delivery_smartphones", identifier.id)

def check_delivery(request, identifier_id):
    suppliers = Supplier.objects.all()
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("delivery", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, 
                    product=product
                )
                return redirect("delivery", identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("delivery", identifier.id)

def check_delivery_ean(request, identifier_id):
    suppliers = Supplier.objects.all()
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        ean = request.POST["ean"]
        # if '/' in imei:
        #     imei=imei.replace('/', '_')
        if Product.objects.filter(ean=ean).exists():
            product=Product.objects.filter(ean=ean)

            if Register.objects.filter(identifier=identifier, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("delivery_smartphones", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, 
                    product=product
                )
                return redirect("delivery_smartphones", identifier.id)
            

            #return redirect("ean_list", identifier.id)
        else:
            messages.error(request, "Такого EAN не существует. Сначала введите его.")
            return redirect("delivery_smartphones", identifier.id)

def check_delivery_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_delivery_unposted", document.id)
            else:
                register = Register.objects.create(
                    document=document,
                    product=product,
                    new=True
                )
                return redirect("change_delivery_unposted", document.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("change_delivery_unposted", document.id)

def delivery(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    shop=Shop.objects.get(name='ООС')
    #shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier).order_by("-created")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "suppliers": suppliers,
        "shop": shop,
        "registers": registers,
    }
    return render(request, "documents/delivery.html", context)

def delivery_smartphones(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    shop=Shop.objects.get(name='ООС')
    #shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier).order_by("-created")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "suppliers": suppliers,
        "shop": shop,
        "registers": registers,
    }
    return render(request, "documents/delivery.html", context)

def delete_line_delivery(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("delivery", identifier.id)

def delete_line_unposted_delivery(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.delete()
    return redirect("change_delivery_unposted", document.id)

def enter_new_product(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        ean = request.POST["EAN"]
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        #category = request.POST["category"]
        #category = ProductCategory.objects.get(id=category)
        if Product.objects.filter(imei=imei).exists():
            messages.error(
                request,
                "Наименование в базу данных не введено, так как IMEI не является уникальным",
            )
            return redirect("delivery", identifier.id)
        else:
            sku=SKU.objects.get(ean=ean)
            category=sku.category
            category=ProductCategory.objects.get(id=category)
            name=str(sku.name)

            product = Product.objects.create(name=name, ean=ean, imei=imei, category=category)
            return redirect("delivery", identifier.id)
    else:
        return redirect("delivery", identifier.id)

def enter_new_product_from_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)

        if Product.objects.filter(imei=imei).exists():
            messages.error(
                request,
                "Наименование в базу данных не введено, так как IMEI не является уникальным",
            )
            return redirect("change_delivery_unposted", document.id)
        else:
            product = Product.objects.create(
                name=name,
                imei=imei,
                category=category,
            )
            return redirect("change_delivery_unposted", document.id)

def delivery_input(request, identifier_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier).order_by("created")
        doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
        if request.method == "POST":
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                supplier = request.POST["supplier"]
            except:
                messages.error(request, "Введите поставщика")
                return redirect("delivery", identifier.id)
            supplier = Supplier.objects.get(id=supplier)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("delivery", identifier.id)
            # posting delivery document
            if post_check == True:
                document = Document.objects.create(
                    title=doc_type, 
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime, 
                    posted=True,
                    supplier=supplier
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    # checking rhos before
                    product = Product.objects.get(imei=imeis[i])
                    #==============av_price module====================
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        if av_price_obj.current_remainder > 0:
                            av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                        elif av_price_obj.current_remainder == 0:
                            av_price_obj.av_price= 0
                            av_price_obj.sum =0
                        else:
                            #av_price_obj.av_price=0
                            #av_price_obj.sum_price=0
                            document.delete()
                            rho.delete()
                            # av_price_obj.save()
                            messages.error(request, "Отрицательный остаток в таблице Av_price. Документ не проведен.")
                            return redirect("delivery", identifier.id)
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )
                    #=============End of Av_price Module=================
                    # creating remainder_history
                    rho = RemainderHistory.objects.create(
                        document=document,
                        user=request.user,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        supplier=supplier,
                        imei=imeis[i],
                        name=names[i],
                        #pre_remainder= rho_latest_before.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        #current_remainder=rho_latest_before.current_remainder + int(quantities[i]),
                        av_price=av_price_obj.av_price,
                        wholesale_price=int(prices[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                   
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=rho.created).exists():
                        rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=rho.created).latest('created')
                        rho.pre_remainder=rho_latest_before.current_remainder
                        rho.current_remainder=rho_latest_before.current_remainder + int(quantities[i])  
                    else:
                        rho.pre_remainder=0
                        rho.current_remainder= int(quantities[i])
                    rho.save()
                    document_sum+=rho.sub_total
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime).exists():
                        remainder=rho.current_remainder
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime).order_by('created')
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder 
                                + obj.incoming_quantity 
                                - obj.outgoing_quantity
                            )
                            obj.save()
                            remainder = obj.current_remainder
                document.sum = document_sum
                document.save()
                registers = Register.objects.filter(identifier=identifier)
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")
            # saving uposted delivery document
            else:
                document = Document.objects.create(
                    title=doc_type,
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime, 
                    posted=False,
                    supplier=supplier,
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    if Register.objects.filter(document=document, deleted=True).exists():
                        registers = Register.objects.filter(document=document, deleted=True)
                        for register in registers:
                                register.delete()
                    else:
                        register = Register.objects.get(identifier=identifier, product=product)
                        register.price = prices[i]
                        register.quantity = quantities[i]
                        register.sub_total = sub_totals[i]
                        register.document = document
                        register.supplier = supplier
                        register.identifier = None
                        register.sub_total = int(prices[i]) * int(quantities[i])
                        register.save()
                        document_sum += int(register.sub_total)
                document.sum = document_sum
                document.save()
                identifier.delete()
                return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def change_delivery_posted(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        supplier = document.supplier
        shop=document.shop_receiver
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        rhos = RemainderHistory.objects.filter(document=document).order_by("-name")
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        rhos = RemainderHistory.objects.filter(document=document).order_by("-name")

        context = {
            "document": document,
            "shop": shop,
            "supplier": supplier,
            "dateTime": dateTime,
            'rhos': rhos
        }
        return render(request, "documents/change_delivery_posted.html", context)
    else:
        return redirect ('login')

def change_delivery_unposted(request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:               
        document = Document.objects.get(id=document_id)
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("-created")
        suppliers = Supplier.objects.all()
        shops = Shop.objects.all()
        categories=ProductCategory.objects.all()
        doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
        numbers = registers.count()
        document_datetime=document.created
        document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method == "POST":
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            supplier=request.POST['supplier']
            supplier=Supplier.objects.get(id=supplier)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_delivery_unposted", document.id)
            else:
                # posting the document
                n = len(names)
                document_sum = 0
                if post_check == True:
                    document.created=dateTime
                    document.shop_receiver=shop
                    document.posted=True
                    document.supplier=supplier
                    document.save()
                    for i in range(n):
                        product = Product.objects.get(imei=imeis[i])
                        #==============av_price module====================
                        if AvPrice.objects.filter(imei=imeis[i]).exists():
                            av_price_obj = AvPrice.objects.get(imei=imeis[i])
                            av_price_obj.current_remainder += int(quantities[i])
                            av_price_obj.sum += int(quantities[i]) * int(prices[i])
                            if av_price_obj.current_remainder > 0:
                                av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                            elif av_price_obj.current_remainder == 0:
                                av_price_obj.av_price= 0
                                av_price_obj.sum =0
                            else:
                                #av_price_obj.av_price=0
                                #av_price_obj.sum_price=0
                                document.posted = False
                                document.save()
                                # av_price_obj.save()
                                messages.error(request, "Отрицательный остаток в таблице Av_price. Документ не проведен.")
                                return redirect("change_delivery_unposted", document.id)
                            av_price_obj.save()
                        else:
                            av_price_obj = AvPrice.objects.create(
                                name=names[i],
                                imei=imeis[i],
                                current_remainder=int(quantities[i]),
                                sum=int(quantities[i]) * int(prices[i]),
                                av_price=int(prices[i]),
                            )
                    #=============End of Av_price Module=================
                        # checking docs before remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                            # creating remainder_history
                            rho = RemainderHistory.objects.create(
                                document=document,
                                rho_type=document.title,
                                created=dateTime,
                                shop=shop,
                                category=product.category,
                                supplier=supplier,
                                imei=imeis[i],
                                name=names[i],
                                pre_remainder=rho_latest_before.current_remainder,
                                incoming_quantity=int(quantities[i]),
                                outgoing_quantity=0,
                                current_remainder=rho_latest_before.current_remainder + int(quantities[i]),
                                av_price=av_price_obj.av_price,
                                wholesale_price=int(prices[i]),
                                sub_total=int(int(quantities[i]) * int(prices[i])),
                            )
                        else:
                            rho = RemainderHistory.objects.create(
                                document=document,
                                rho_type=document.title,
                                created=dateTime,
                                shop=shop,
                                category=product.category,
                                supplier=supplier,
                                imei=imeis[i],
                                name=names[i],
                                pre_remainder=0,
                                incoming_quantity=int(quantities[i]),
                                outgoing_quantity=0,
                                current_remainder=int(quantities[i]),
                                av_price=av_price_obj.av_price,
                                wholesale_price=int(prices[i]),
                                sub_total=int(int(quantities[i]) * int(prices[i]))
                            )
                        document_sum+=rho.sub_total
     
                        # checking docs after remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created)
                            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder = obj.current_remainder
                    document.sum = document_sum
                    document.save()
                    registers = Register.objects.filter(document=document)
                    for register in registers:
                        register.delete()
                    return redirect("log")
                # saving uposted document
                else:
                    for i in range(n):
                        product = Product.objects.get(imei=imeis[i])
                        if Register.objects.filter(document=document, deleted=True).exists():
                            registers = Register.objects.filter(document=document, deleted=True)
                            for register in registers:
                                register.delete()
                        else:
                            if Register.objects.filter(document=document).exists():
                                register = Register.objects.get(document=document, product=product) 
                                register.price = prices[i]
                                register.quantity = quantities[i]
                                register.sub_total = sub_totals[i]
                                register.document = document
                                register.new = False
                                register.save()
                                document_sum += int(register.sub_total)
                    document.sum = document_sum
                    document.created=dateTime
                    document.shop_receiver=shop
                    document.supplier=supplier
                    document.save()
                    return redirect("log")
        else:
            context = {
                "registers": registers,
                "shops": shops,
                "suppliers": suppliers,
                "document": document,
                "categories": categories,
                "document_datetime": document_datetime
            }
            return render(request, "documents/change_delivery_unposted.html", context)
    auth.logout(request)
    return redirect("login")

def unpost_delivery(request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        document = Document.objects.get(id=document_id)
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        shop = document.shop_receiver
        supplier = document.supplier
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # checking rhos before
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
                remainder=rho_latest_before.current_remainder
            else:
                remainder=0
            #checking rhos after
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
                sequence_rhos_after = RemainderHistory.objects.filter( shop=rho.shop, imei=rho.imei, created__gt=rho.created).order_by('created')
                for obj in sequence_rhos_after:
                    obj.pre_remainder = remainder
                    obj.current_remainder = (
                        remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    obj.save()
                    remainder = obj.current_remainder
            register=Register.objects.create(
                document=document,
                product=product,
                quantity=rho.incoming_quantity,
                price=rho.wholesale_price,
                sub_total=rho.sub_total
            )
        #=============Av_price_module==================================
            av_price_obj = AvPrice.objects.get(imei=rho.imei)
            av_price_obj.current_remainder -= rho.incoming_quantity
            av_price_obj.sum -= int(rho.incoming_quantity) * int(rho.wholesale_price)
            if av_price_obj.current_remainder > 0:
                av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
            else:
                av_price_obj.av_price=0
            av_price_obj.save()
            rho.delete()
        document.posted=False
        document.save()
        return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")

def enter_new_sku (request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories=ProductCategory.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        ean = request.POST["EAN"]
        if '/' in ean:
            imei=imei.replace('/', '_')
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)
        ean_length=len(ean)
        if ean_length>13:
            messages.error(
                request,
                "EAN не может содержать больше 13 цифр",
            )
        if SKU.objects.filter(ean=ean).exists():
            messages.error(
                request,
                "SKU с данным EAN уже есть в БД.",
            )
            return redirect("delivery", identifier.id)
        else:
            sku = SKU.objects.create(name=name, ean=ean, category=category)
            return redirect("delivery", identifier.id)
    else:

        return redirect("delivery", identifier.id)
#=======================================================================
def sku_new(request):
    if request.user.is_authenticated:
        categories=ProductCategory.objects.all()
        context = {
            "categories": categories,
        }
        return render(request, "documents/sku_new.html", context)
    else:
        return redirect("login")
    
def sku_new_create(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            name = request.POST["name"]
            ean = request.POST["EAN"]
            if '/' in ean:
                ean=ean.replace('/', '_')
            category = request.POST["category"]
            category = ProductCategory.objects.get(id=category)
            ean_length=len(ean)
            if ean_length>13:
                messages.error(request,
                    "EAN не может содержать больше 13 цифр"
                )
            if SKU.objects.filter(ean=ean).exists():
                messages.error(request,
                    "SKU с данным EAN уже есть в БД."
                )
                return redirect("sku_new")
            else:
                sku = SKU.objects.create(name=name, ean=ean, category=category)
                # context = {
                #     "sku": sku,
                # }
                #return render(request, "documents/sku_imei_link.html", context)
                return redirect('sku_imei_link', sku.id)
        else:
            return redirect("log")
    return redirect("login")

def sku_imei_link(request, sku):
    if request.user.is_authenticated:
        sku=SKU.objects.get(id=sku)
        if request.method == "POST":
            pass
        else:
            context = {
                        "sku": sku,
                    }
            return render(request, "documents/sku_imei_link.html", context)
    else:
        return redirect("login")
# =====================================================================================
def identifier_transfer(request):
    identifier = Identifier.objects.create()
    return redirect("transfer", identifier.id)

def transfer(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all().exclude(active=False)
        shop_default = Shop.objects.get(name="ООС")
        if Register.objects.filter(identifier=identifier).exists():
            registers = Register.objects.filter(identifier=identifier).order_by('-created')
            numbers = registers.count()
            for register, i in zip(registers, range(numbers)):
                register.number = i + 1
                register.save()
            context = {
                "identifier": identifier,
                "shops": shops,
                "registers": registers,
                "shop_default": shop_default,
            }
            return render(request, "documents/transfer.html", context)
        else:
            context = {
                "identifier": identifier,
                "shops": shops,
                "shop_default": shop_default,
            }
            return render(request, "documents/transfer.html", context)
    else:
        return redirect("login")

def check_transfer(request, identifier_id):
    tdelta=datetime.timedelta(hours=3)
    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
    dateTime=dT_utcnow+tdelta
    #shops = Shop.objects.all().exclude(active=False)
    identifier = Identifier.objects.get(id=identifier_id)
    #if "check_imei" in request.GET:
    #shop = request.GET["shop"]
    if request.method == "POST":
        registers=Register.objects.filter(identifier=identifier)
        check_imei = request.POST["check_imei"]
        quantity = request.POST["quantity_hidden_to_post"]
        if '/' in check_imei:
            check_imei=check_imei.replace('/', '_')
        if AvPrice.objects.filter(imei=check_imei).exists():
            avPrice=AvPrice.objects.get(imei=check_imei)
        else:
            messages.error(request,"AvPrice не существует для данного наименования.",)
            return redirect("transfer", identifier.id)
        if Product.objects.filter(imei=check_imei).exists():
            product=Product.objects.get(imei=check_imei)
            if registers.filter(imei=check_imei).exists():
                final_qnty= int(quantity) + 1
                register=registers.get(imei=check_imei)
                register.updated=dateTime
                register.quantity=final_qnty
                register.save()
                #messages.error(request,"Вы уже ввели данное наименование. Запишите нужно кол-во в списке ниже",)
                #return redirect("transfer", identifier.id)
            else:
                if product.category.name == 'Сим_карты':   
                    if AvPrice.objects.filter(imei=product.imei).exists():
                        av_price=AvPrice.objects.get(imei=product.imei)
                        register = Register.objects.create(
                            product=product,
                            identifier=identifier,
                            quantity=1,
                            price=av_price.av_price,
                            sub_total=av_price.av_price
                        )
                    else:
                        messages.error(request,"Поступление для данного наименования не было создано. Соответственно av_price отсутствует",)
                        return redirect("transfer", identifier.id)
                else:
                    register = Register.objects.create(
                        product=product,
                        imei=check_imei,
                        name=product.name,
                        identifier=identifier,
                        quantity=1,
                        av_price=avPrice,
                    )

            return redirect ("transfer", identifier.id)
        else:
            messages.error(request, "Данное наименование отсутствует в базе данных")
            return redirect("transfer", identifier.id)
    else:
        return redirect("transfer", identifier.id)

def change_register(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        if request.method == "POST":
            imei = request.POST["imei"]
            price = request.POST["price"]
            quantity = request.POST["quantity"]
            sub_total = request.POST["sub_total"]
            register=Register.objects.get(document=document, imei=imei)
            register.quantity=quantity
            register.price=price
            register.price=sub_total
            register.save()
            return redirect("change_transfer_unposted", document.id)
    else:
        return redirect ('login')

def check_transfer_unposted(request, document_id):
    tdelta=datetime.timedelta(hours=3)
    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
    dateTime=dT_utcnow+tdelta
    users = Group.objects.get(name='sales').user_set.all()
    group = Group.objects.get(name='admin').user_set.all()
    shops = Shop.objects.all().exclude(active=False)
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    for register in registers:
        if register.deleted == True:
            register.delete()
    shop_sender = document.shop_sender
    # if "imei_check" in request.GET:
    if request.method=="POST":
        check_imei = request.POST["check_imei"]
        quantity = request.POST["quantity_hidden_to_post"]
        if '/' in check_imei:
            check_imei=check_imei.replace('/', '_')
        # shop = request.GET["shop"]
        # shop = Shop.objects.get(id=shop)
        if AvPrice.objects.filter(imei=check_imei).exists():
            avPrice=AvPrice.objects.get(imei=check_imei)
        else:
            messages.error(request,"Ошибка. AvPrice не существует для данного наименования.",)
            return redirect("change_transfer_unposted", document.id)
        if Product.objects.filter(imei=check_imei).exists():
            product = Product.objects.get(imei=check_imei)
            if registers.filter(imei=check_imei).exists():
                final_qnty=int(quantity)+1
                if RemainderHistory.objects.filter(imei=check_imei, shop=shop_sender).exists():
                    rho=RemainderHistory.objects.filter(imei=check_imei, shop=shop_sender).latest('created')
                    if rho.current_remainder >= final_qnty:
                        register=registers.get(imei=check_imei)
                        register.updated=dateTime
                        register.quantity=final_qnty
                        register.save()
                        #messages.error(request,"Вы уже ввели данное наименование. Запишите нужно кол-во в списке ниже",)
                        return redirect("change_transfer_unposted", document.id)
                    messages.error(request,"Ошибка. Необходимое кол-во отсутствует на данном складе.",)
                    return redirect("change_transfer_unposted", document.id)
                messages.error(request,"Ошибка. Данное наименование отсутствует на данном складе",)
                return redirect("change_transfer_unposted", document.id)
            else:
                if RemainderHistory.objects.filter(imei=check_imei, shop=shop_sender).exists():
                    rho=RemainderHistory.objects.filter(imei=check_imei, shop=shop_sender).latest('created')
                    if rho.current_remainder >0:
                        if product.category.name == 'Сим_карты':   
                            if AvPrice.objects.filter(imei=product.imei).exists():
                                av_price=AvPrice.objects.get(imei=product.imei)
                                register = Register.objects.create(
                                    product=product,
                                    document=document,
                                    quantity=1,
                                    price=av_price.av_price,
                                    sub_total=av_price.av_price
                                )
                            else:
                                messages.error(request,"Ошибка. Поступление для данного наименования не было создано. Соответственно av_price отсутствует",)
                                return redirect("change_transfer_unposted", document.id)
                        else:
                            register = Register.objects.create(
                                product=product,
                                imei=check_imei,
                                name=product.name,
                                document=document,
                                quantity=1,
                                new=True,
                                av_price=avPrice,
                            )
                            
                            if rho.retail_price:
                                register.price=rho.retail_price
                            else:
                                register.price=0
                            register.sub_total = int(quantity) * int(register.price)
                            register.save()
                            return redirect("change_transfer_unposted", document.id)
                    messages.error(request,"Ошибка. Необходимое кол-во отсутствует на данном складе.",)
                    return redirect("change_transfer_unposted", document.id)
                messages.error(request,"Ошибка. Данное наименование отсутствует на данном складе",)
                return redirect("change_transfer_unposted", document.id)
        else:
            messages.error(request, "Ошибка. Данное наименование отсутствует в базе данных")
            return redirect("change_transfer_unposted", document.id)
    # else:
    #     messages.error(request, "Вы не ввели IMEI")
    #     return redirect("change_transfer_unposted", document.id)

def delete_line_transfer(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.filter(identifier=identifier_id, product=product)
    item.delete()
    return redirect("transfer", identifier.id)

def delete_line_unposted_transfer(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    register = Register.objects.get(document=document, product=product)
    register.delete()
    return redirect("change_transfer_unposted", document.id)

def transfer_input(request, identifier_id):
    if request.user.is_authenticated:
        users = Group.objects.get(name='sales').user_set.all()
        group = Group.objects.get(name='admin').user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        doc_type = DocumentType.objects.get(name="Перемещение ТМЦ")
        shop_sender_to_ozon = Shop.objects.get(name='ООС')
        ozon_shop = Shop.objects.get(name='Озон')
        numbers = registers.count()
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            prices = request.POST.getlist("price", None)
            quantities = request.POST.getlist("quantity", None)
            if request.user in users: 
                shop_sender = Shop.objects.get(name='ООС')
                shop_receiver=request.session['session_shop']
                shop_receiver=Shop.objects.get(id=shop_receiver)
            else:
                shop_sender=request.POST['shop_sender']
                shop_sender=Shop.objects.get(id=shop_sender)
                shop_receiver = request.POST["shop_receiver"]
                shop_receiver=Shop.objects.get(id=shop_receiver)
           #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            if shop_sender == shop_receiver:
                messages.error(request,"Документ не проведен.Выберите фирму получателя отличную от отправителя")
                return redirect("transfer", identifier.id)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            # posting the document
            if post_check == True:
            #checking availability of items to transfer
                n = len(names)
                for i in range(n):
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender, created__lt=dateTime).exists():
                        remainder_history= RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender, created__lt=dateTime).latest('created')
                        if remainder_history.current_remainder < int(quantities[i]):
                            #check_point.append(False)
                            string=f'Документ не проведеден. Количество товара с IMEI {imeis[i]} недостаточно.'
                            messages.error(request,  string)
                            return redirect("transfer", identifier.id)
                    else:
                        string=f'Документ не проведеден. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("transfer", identifier.id)
                if imeis:
                    #creating document
                    document = Document.objects.create(
                        created=dateTime,
                        title=doc_type,
                        user=request.user,
                        posted=True,
                        shop_sender=shop_sender,
                        shop_receiver=shop_receiver,
                    )
                    document_sum = 0
                    for i in range(n):
                        product=Product.objects.get(imei=imeis[i])
                        if AvPrice.objects.filter(imei=imeis[i]).exists():
                            av_price=AvPrice.objects.get(imei=imeis[i])
                            av_price=av_price.av_price
                        else:
                            av_price=0
                        document_sum += int(prices[i]) * int(quantities[i])
                        # checking shop_sender
                        rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i],shop=shop_sender,created__lt=dateTime).latest('created')
                        rho = RemainderHistory.objects.create(
                            created=dateTime,
                            user=request.user,
                            document=document,
                            rho_type=document.title,
                            shop=shop_sender,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            av_price=av_price,
                            retail_price=prices[i],
                            pre_remainder=rho_latest_before.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity=quantities[i],
                            current_remainder=rho_latest_before.current_remainder- int(quantities[i]),
                            sub_total=int(prices[i]) * int(quantities[i]),
                            status=False
                        )
                        # checking docs after remainder_history for shop_sender
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender,created__gt=rho.created).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i],shop=shop_sender,created__gt=rho.created).order_by('created')
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder = obj.current_remainder

                            #remainder for updating ozon marketplace quantity    
                            mp_quantity=remainder
                        else:
                            mp_quantity=rho.current_remainder
                        #updating quantity at ozon marketplace
                        if product.for_mp_sale is True and shop_sender == shop_sender_to_ozon and shop_receiver != ozon_shop:
                            headers = {
                                "Client-Id": "867100",
                                "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                            }
                            task = {
                                "stocks": [
                                    {
                                        #"offer_id": str(product.id),
                                        "offer_id": str(product.EAN),
                                        "product_id": str(product.ozon_id),
                                        "stock": str(mp_quantity),
                                        "warehouse_id": 1020001938106000
                                    }
                                ]
                            }
                            response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task, headers=headers)
                            json=response.json()
                            status_code=response.status_code
                            time.sleep(0.5)
                            #print(status_code)
                            #print(json)


                        # checking shop_receiver
                        rho = RemainderHistory.objects.create(
                            created=dateTime,
                            document=document,
                            user=request.user,
                            rho_type=document.title,
                            shop=shop_receiver,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            incoming_quantity=quantities[i],
                            outgoing_quantity=0,
                            status=True,
                            sub_total=int(prices[i])*int(quantities[i]),
                            av_price=av_price
                        )
                        #checking docs before for shop_receiver
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__lt=rho.created).exists():
                            rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__lt=rho.created).latest('created')
                            rho.pre_remainder=rho_latest_before.current_remainder
                        else:
                            rho.pre_remainder=0
                        rho.current_remainder=rho.pre_remainder+int(quantities[i])
                        rho.save()
                        # checking docs after remainder_history for shop_receiver
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__gt=rho.created).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i],shop=shop_receiver,created__gt=rho.created).order_by('created')
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder = obj.current_remainder
                    document.sum = document_sum
                    document.save()
                    for register in registers:
                        register.delete()
                    identifier.delete()
                    if request.user in users:
                        return redirect ('sale_interface')
                    else:
                        return redirect("log")
                else:
                    messages.error(request, "Вы не ввели ни одного наименования.")
                    return redirect("transfer", identifier.id)
            else:
                document = Document.objects.create(
                    created=dateTime,
                    title=doc_type,
                    user=request.user,
                    posted=False,
                    shop_receiver=shop_receiver,
                    shop_sender=shop_sender,
                )
                document_sum = 0
                n = len(names)
                for i in range(n):
                    product=Product.objects.get(imei=imeis[i])
                    document_sum += int(prices[i]) * int(quantities[i])
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.document = document
                    register.new = False
                    register.identifier = None
                    register.save()
                identifier.delete()
                document.sum = document_sum
                document.save()
                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")                
    else:
        auth.logout(request)
        return redirect("login")

def change_transfer_posted(request, document_id):
    users=Group.objects.get(name="sales").user_set.all()
    document = Document.objects.get(id=document_id)
    shop_sender=document.shop_sender
    shop_receiver=document.shop_receiver
    rhos=RemainderHistory.objects.filter(document=document).exclude(shop=shop_receiver).order_by('created')
    #dateTimee=document.created
    document_datetime=document.created
    document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
    numbers = rhos.count()
    for rho, i in zip(rhos, range(numbers)):
        rho.number = i + 1
        rho.save()
 
    context = {
        'rhos': rhos,
        'dateTime': document_datetime,
        "document": document,
        'shop_receiver': shop_receiver,
        'shop_sender': shop_sender,
    }
    return render(request, "documents/change_transfer_posted.html", context)

def change_transfer_unposted(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("-created")
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        shop_receiver=document.shop_receiver
        shop_sender=document.shop_sender
        shops = Shop.objects.all().exclude(active=False)
        shop_sender_to_ozon = Shop.objects.get(name='ООС')
        ozon_shop = Shop.objects.get(name='Озон')
        doc_type = DocumentType.objects.get(name="Перемещение ТМЦ")
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            prices = request.POST.getlist("price", None)
            quantities = request.POST.getlist("quantity", None)
            shop_sender = request.POST["shop_sender"]
            shop_receiver = request.POST["shop_receiver"]
            shop_sender = Shop.objects.get(id=shop_sender)
            shop_receiver = Shop.objects.get(id=shop_receiver)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            if shop_sender == shop_receiver:
                messages.error(request,"Документ не проведен. Выберите фирму получателя отличную от отправителя",)
                return redirect("change_transfer_unposted", document.id)
            else:
                if not imeis:
                    messages.error(request, "Вы не ввели ни одного наименования.")
                    return redirect("change_transfer_unposted", document.id)
                else:
                    try:
                        if request.POST["post_check"]:
                            post_check = True
                    except KeyError:
                        post_check = False
                #checking availability
                if post_check == True:
                    n = len(names)
                    for i in range(n):
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender,created__lt=dateTime).exists():
                            rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender, created__lt=dateTime).latest('created')
                            if rho_latest_before.current_remainder < int(quantities[i]):
                                string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                                messages.error(request,  string)
                                return redirect("change_transfer_unposted", document.id)
                        else:
                            string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                            messages.error(request,  string)
                            return redirect("change_transfer_unposted", document.id)
                    # posting transfer document
                    document.posted = True
                    document.shop_receiver=shop_receiver
                    document.shop_sender=shop_sender
                    document.created=dateTime
                    document.save()
                    document_sum = 0
                    for i in range(n):
                        product=Product.objects.get(imei=imeis[i])
                        if AvPrice.objects.filter(imei=imeis[i]).exists():
                            av_price=AvPrice.objects.get(imei=imeis[i])
                            av_price=av_price.av_price
                        else:
                            av_price=0
                        document_sum += int(prices[i]) * int(quantities[i])
                        # creating new rho
                        rho = RemainderHistory.objects.create(
                            created=dateTime,
                            document=document,
                            user=document.user,
                            rho_type=document.title,
                            shop=shop_sender,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            av_price=av_price,
                            incoming_quantity=0,
                            outgoing_quantity=quantities[i],
                            sub_total=int(prices[i]) * int(quantities[i])
                        )
                        #checking docs before for shop_sender
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_sender, created__lt=dateTime).exists():
                            rho_latest_before = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__lt=dateTime).latest('created')
                            rho.pre_remainder=rho_latest_before.current_remainder
                        else:
                            rho.pre_remainder=0
                        rho.current_remainder=rho.pre_remainder-int(quantities[i])
                        rho.save()
                        # checking docs after remainder_history for shop_sender
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender, created__gt=dateTime).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__gt=dateTime)
                            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder =obj.current_remainder
                        #remainder for updating ozon marketplace quantity    
                            mp_quantity=remainder
                        else:
                            mp_quantity=rho.current_remainder
                        #updating quantity at ozon marketplace
                        if product.for_mp_sale is True and shop_sender == shop_sender_to_ozon and shop_receiver != ozon_shop:
                            headers = {
                                "Client-Id": "867100",
                                "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                            }
                            task = {
                                "stocks": [
                                    {
                                        #"offer_id": str(product.id),
                                        "offer_id": str(product.EAN),
                                        "product_id": str(product.ozon_id),
                                        "stock": str(mp_quantity),
                                        "warehouse_id": 1020001938106000
                                    }
                                ]
                            }
                            response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task, headers=headers)
                            time.sleep(0.5)
                            json=response.json()
                            status_code=response.status_code
                            #print(status_code)
                            #print(json)

                        # creating rho for shop_receiver
                        rho = RemainderHistory.objects.create(
                            created=dateTime,
                            user=document.user,
                            document=document,
                            rho_type=document.title,
                            shop=shop_receiver,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            av_price=av_price,
                            incoming_quantity=quantities[i],
                            outgoing_quantity=0,
                            status=True,
                            sub_total=int(prices[i])*int(quantities[i])
                        )
                        #checking docs before for shop_sender
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_receiver, created__lt=dateTime).exists():
                            rho_latest_before = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__lt=dateTime).latest('created')
                            rho.pre_remainder=rho_latest_before.current_remainder
                        else:
                            rho.pre_remainder=0
                        rho.current_remainder=rho.pre_remainder+int(quantities[i])
                        rho.save()
                        # checking docs after remainder_history for shop_receiver
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_receiver, created__gt=dateTime).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__gt=dateTime)
                            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder =obj.current_remainder
                    document.sum = document_sum
                    document.save()
                    registers = Register.objects.filter(document=document)
                    for register in registers:
                        register.delete()
                    return redirect("log")
                # saving unposted document
                else:
                    n = len(names)
                    document_sum = 0
                    for i in range(n):
                        document_sum += int(prices[i]) * int(quantities[i])
                        product = Product.objects.get(imei=imeis[i])
                        register = Register.objects.get(document=document, product=product)
                        register.price = prices[i]
                        register.quantity = quantities[i]
                        register.sub_total = int(prices[i]) * int(quantities[i])
                        register.new=False
                        register.save()
                    document.sum = document_sum
                    document.created=dateTime
                    document.shop_sender=shop_sender
                    document.shop_receiver=shop_receiver
                    document.save()
                    return redirect("log")

        else:
            context = {
                "registers": registers,
                "shops": shops,
                "document": document,
                "dateTime": dateTime,
                'shop_receiver': shop_receiver,
                'shop_sender': shop_sender,
            }
            return render(request, "documents/change_transfer_unposted.html", context)
    else:
        auth.logout(request)
        return redirect ('login')

def unpost_transfer(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    for rho in rhos:
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
            rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
            remainder=rho_latest_before.current_remainder
        else:
            remainder=0
           
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created)
            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder
                obj.current_remainder = (
                    remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder = obj.current_remainder
        if rho.status==True:
            product=Product.objects.get(imei=rho.imei)
            register=Register.objects.create(
                document=document,
                price=rho.retail_price,
                quantity=rho.incoming_quantity,
                sub_total= rho.incoming_quantity * rho.retail_price,
                product=product
            )
        rho.delete()
    document.posted = False
    document.save()
    return redirect("log")

def transfer_auto (request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        shops = Shop.objects.all().exclude(active=False)
        doc_type = DocumentType.objects.get(name="Перемещение ТМЦ")
        if request.method == "POST":
            file = request.FILES["file_name"]
            shop_sender = request.POST["shop_sender"]
            shop_sender=Shop.objects.get(id=shop_sender)
            shop_receiver = request.POST["shop_receiver"]
            shop_receiver=Shop.objects.get(id=shop_receiver)
            if shop_sender == shop_receiver:
                messages.error(request,"Документ не проведен.Выберите фирму получателя отличную от отправителя")
                return redirect("transfer_auto")
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
            df1 = pandas.read_excel(file)
            cycle = len(df1)#returns number of rows
            #checking availabiltiy of items to avoid saving only a portion of document
            for i in range(cycle):
                row = df1.iloc[i]#reads rows of excel file one by one
                imei=row.Imei
                # if '/' in row.Imei:
                #     imei=row.Imei
                #     imei=imei.replace('/', '_')
                if RemainderHistory.objects.filter(imei=imei, shop=shop_sender, created__lt=dateTime).exists():
                    remainder_history= RemainderHistory.objects.filter(imei=imei, shop=shop_sender, created__lt=dateTime).latest('created')
                    if remainder_history.current_remainder < int(row.Quantity):
                        #check_point.append(False)
                        string=f'Документ не проведеден. Количество товара {row.Title} с данным IMEI {imei} недостаточно для перемещения.'
                        messages.error(request,  string)
                        return redirect("transfer_auto")
                else:
                    string=f'Документ не проведеден. Товар {row.Title} с IMEI {imei} отсутствует на балансе фирмы.'
                    messages.error(request,  string)
                    return redirect("transfer_auto")
            document = Document.objects.create(
                created=dateTime,
                title=doc_type,
                user=request.user,
                posted=True,
                shop_sender=shop_sender,
                shop_receiver=shop_receiver,
            )
            document_sum = 0
            for i in range(cycle):
                row = df1.iloc[i]#reads rows of excel file one by one
                imei=row.Imei
                product=Product.objects.get(imei=imei)
                if AvPrice.objects.filter(imei=imei).exists():
                    av_price=AvPrice.objects.get(imei=imei)
                else:
                    av_price=AvPrice.objects.create(
                        imei=imei,
                        name=row.Title,
                        current_remainder=row.Quantity,
                        av_price=row.Retail_price,
                        sum=int(row.Quantity)*int(row.Retail_price)
                    )
                document_sum+=int(row.Quantity) * int(row.Retail_price)
                # checking shop_sender
                #additional check in case quantities in excel file are 0
                if RemainderHistory.objects.filter(imei=imei,shop=shop_sender,created__lt=document.created).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=imei,shop=shop_sender,created__lt=document.created).latest('created')
                    pre_remainder=rho_latest_before.current_remainder
                else:
                    pre_remainder=0
                rho = RemainderHistory.objects.create (
                    created=document.created,
                    user=request.user,
                    document=document,
                    rho_type=document.title,
                    shop=shop_sender,
                    category=product.category,
                    imei=imei,
                    name=product.name,
                    av_price=av_price.av_price,
                    retail_price=row.Retail_price,
                    pre_remainder=pre_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=int(row.Quantity),
                    current_remainder=rho_latest_before.current_remainder- int(row.Quantity),
                    sub_total=int(row.Retail_price) * int(row.Quantity),
                    status=False,
                    )
                # checking docs after remainder_history for shop_sender
                if RemainderHistory.objects.filter(imei=imei, shop=shop_sender, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imei,shop=shop_sender,created__gt=rho.created).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder
                #checking docs before for shop_receiver
                #additional check in case quantities in excel file are 0
                if RemainderHistory.objects.filter(imei=imei, shop=shop_receiver, created__lt=document.created).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=imei, shop=shop_receiver, created__lt=document.created).latest('created')
                    pre_remainder=rho_latest_before.current_remainder
                else:
                    pre_remainder=0
                rho = RemainderHistory.objects.create(
                    created=document.created,
                    document=document,
                    user=request.user,
                    rho_type=document.title,
                    shop=shop_receiver,
                    category=product.category,
                    imei=row.Imei,
                    name=product.name,
                    retail_price=row.Retail_price,
                    pre_remainder=pre_remainder,
                    current_remainder=pre_remainder+int(row.Quantity),
                    incoming_quantity=int(row.Quantity),
                    outgoing_quantity=0,
                    status=True,
                    sub_total=int(row.Quantity)*int(row.Retail_price)
                )
                # checking docs after remainder_history for shop_receiver
                if RemainderHistory.objects.filter(imei=imei, shop=shop_receiver, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imei,shop=shop_receiver,created__gt=rho.created).order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                        )
                        obj.save()
                        remainder = obj.current_remainder
            document.sum = document_sum
            document.save()
            return redirect('log')
        else:
            context = {
                'shops': shops,
                }
            return render(request, "documents/transfer_auto.html", context)
    else:
        auth.logout(request)
        return redirect("login")
# =======================================================================================
def identifier_recognition(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("recognition", identifier.id)
    else:
        return redirect("login")

def check_recognition(request, identifier_id):
    #users=Group.objects.get(name="admin").user_set.all()
    if request.user.is_authenticated:
        categories = ProductCategory.objects.all()
        identifier = Identifier.objects.get(id=identifier_id)
        # if 'imei' in request.GET:
        if request.method == "POST":
            imei = request.POST["check_imei"]
            if '/' in imei:
                imei=imei.replace('/', '_')
            # shop = request.POST["shop"]
            # shop=Shop.objects.get(id=shop)
            if Product.objects.filter(imei=imei).exists():
                product = Product.objects.get(imei=imei)
                if Register.objects.filter(identifier=identifier, product=product).exists():
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.quantity += 1
                    register.sub_total=register.quantity*register.price
                    register.save()
                    return redirect("recognition", identifier.id)
                else:
                    register = Register.objects.create(
                        identifier=identifier,
                        product=product,
                        price=0,
                        quantity=1,
                        sub_total=0,
                    )
                    return redirect("recognition", identifier.id)    
            else:
                messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
                return redirect("recognition", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def enter_new_product_recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)
        if Product.objects.filter(imei=imei).exists():
            messages.error(
                request,
                "Наименование в базу данных не введено, так как IMEI не является уникальным",
            )
            return redirect("recognition", identifier.id)
        else:
            product = Product.objects.create(name=name, imei=imei, category=category)
            return redirect("recognition", identifier.id)
    else:
        return redirect("recognition", identifier.id)

def check_recognition_unposted (request, document_id):
    users=Group.objects.get(name="admin").user_set.all()
    if request.user in users:
        document = Document.objects.get(id=document_id)
        registers = Register.objects.filter(document=document)
        if request.method == "POST":
            imei = request.POST["imei"]
            if '/' in imei:
                imei=imei.replace('/', '_')
            shop=document.shop_receiver
            #shop=Shop.objects.get(id=shop)
            if Product.objects.filter(imei=imei).exists():
                product = Product.objects.get(imei=imei)
                if Register.objects.filter(document=document, product=product).exists():
                    register.quantity += 1
                    register.sub_total=register.price*register.quantity
                    register.save()
                else:
                    register = Register.objects.create(
                        document=document, 
                        product=product,
                        quantity=1,
                    )
                    register.sub_total=register.quantity*register.price
                    register.save()         
            return redirect("change_recognition_unposted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_recognition_unposted", document.id)       
    else:
        auth.logout(request)
        return redirect("login")

def recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    sim_category=ProductCategory.objects.get(name="Сим_карты")
    service_category=ProductCategory.objects.get(name='Услуги')
    wink_category=ProductCategory.objects.get(name='Подписки')
    insurance_category=ProductCategory.objects.get(name='Страховки')
    shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier).order_by("created")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "shops": shops,
        "registers": registers,
        "sim_category": sim_category,
        'wink_category': wink_category,
        "service_category": service_category,
        "insurance_category": insurance_category,
    }
    return render(request, "documents/recognition.html", context)

def delete_line_recognition(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("recognition", identifier.id)

def delete_line_recognition_unposted (request, imei, document_id):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.delete()
    return redirect("change_recognition_unposted", document.id)

def clear_recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("recognition", identifier.id)

def recognition_input(request, identifier_id):
    if request.user.is_authenticated:
        users=Group.objects.get(name="admin").user_set.all()
        group=Group.objects.get(name="sales").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        doc_type = DocumentType.objects.get(name="Оприходование ТМЦ")
        if request.method == "POST":
            if request.user in users:
                shop = request.POST["shop"]
                shop = Shop.objects.get(id=shop)
                #==============Time Module=========================================
                dateTime=request.POST.get('dateTime', False)
                if dateTime:
                    # converting dateTime in str format (2021-07-08T01:05) to django format ()
                    dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                    #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                    current_dt=datetime.datetime.now()
                    mics=current_dt.microsecond
                    tdelta_1=datetime.timedelta(microseconds=mics)
                    secs=current_dt.second
                    tdelta_2=datetime.timedelta(seconds=secs)
                    tdelta_3=tdelta_1+tdelta_2
                    dateTime=dateTime+tdelta_3
                else:
                    tdelta=datetime.timedelta(hours=3)
                    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                    dateTime=dT_utcnow+tdelta
                    #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                    #==================End of time module================================
            else:
                session_shop=request.session['session_shop']
                shop=Shop.objects.get(id=session_shop)
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("recognition", identifier.id)
            n = len(names)
            document_sum = 0
            if post_check == True:
                document = Document.objects.create(
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    shop_receiver=shop,
                )
                for i in range(n):
                  #================Av_Price_Module===================================
                  # При оприходовании на оптовый склад мы ставим оптовые цены, тем самым не сильно изменяя av_price. При оприходовании на розничный склад мы ставим розничные цены, которые значительно изменяют av_price при условии, что они отличаются от оптовых цен. (Интернет номера, КЭО). Соответстенно товар не желательно оприходовать на розничный склад.
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj=AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        if av_price_obj.current_remainder > 0:
                            av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                        else:
                            av_price_obj.av_price = int(prices[i])
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price= int(prices[i])
                    )       
                    # checking docs before remainder_history
                    product=Product.objects.get(imei=imeis[i])
                    rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        rho_type=doc_type,
                        shop=shop,
                        category=product.category,
                        imei=imeis[i],
                        av_price=av_price_obj.av_price,
                        name=names[i],
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        sub_total=int(quantities[i])*int(prices[i]),
                    )
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                        rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                        rho.pre_remainder=rho_latest_before.current_remainder
                        rho.current_remainder=rho_latest_before.current_remainder + int(quantities[i])
                    else:
                        rho.pre_remainder=0
                        rho.current_remainder=int(quantities[i])
                    if shop.retail==True:
                        rho.retail_price=int(prices[i])
                    else:
                        rho.wholesale_price=int(prices[i])
                    rho.save()
                    document_sum+=rho.sub_total 
                   
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                        remainder=rho.current_remainder
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).order_by('created')
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder
                                + obj.incoming_quantity
                                - obj.outgoing_quantity
                            )
                            obj.save()
                            remainder = obj.current_remainder
                for register in registers:
                    register.delete()
                identifier.delete()
                document.sum=document_sum
                document.save()
                if request.user in group:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")
            else:
                document = Document.objects.create(
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=False,
                    shop_receiver=shop
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
                document.sum = document_sum
                document.save()
                identifier.delete()
                if request.user in group:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")    
    else:
        auth.logout(request)
        return redirect("login")

def change_recognition_posted(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        shop=document.shop_receiver
        if document.base_doc:
            base_document=Document.objects.get(id=document.base_doc)
        else:
            base_document="Not Existing"
        if RemainderHistory.objects.filter(document=document).exists():
            rhos = RemainderHistory.objects.filter(document=document).order_by("name")
            dateTime=document.created
            dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
            numbers = rhos.count()
            for rho, i in zip(rhos, range(numbers)):
                rho.number = i + 1
                rho.save()
            context = {
                "rhos": rhos,
                "document": document,
                'base_document': base_document,
                'shop': shop,
                "dateTime": dateTime,
            }
            return render(request, "documents/change_recognition_posted.html", context)
        else:
            messages.error(request, "В ходе инвентаризации не было излишков и оприходований")
            return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")

def change_recognition_unposted(request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:  
        document = Document.objects.get(id=document_id)
        shop=document.shop_receiver
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
        shops = Shop.objects.all()
        categories = ProductCategory.objects.all()
        doc_type = DocumentType.objects.get(name="Оприходование ТМЦ")
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method=='POST':
            shop = request.POST["shop"]
            dateTime = request.POST["dateTime"]
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            shop = Shop.objects.get(id=shop)
            # category=ProductCategory.objects.get(id=category)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_recognition_unposted", document.id)
            else:
                #posting the document
                n = len(names)
                document_sum = 0
                if post_check == True:
                    document.created=dateTime
                    document.shop_receiver=shop
                    document.posted=True
                    document.save()
                    
                    for i in range(n):
                    #===============Av_price_module=========================
                        av_price_obj=AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder+=int(quantities[i])
                        av_price_obj.sum+=int(quantities[i])*int(prices[i])
                        if av_price_obj.current_remainder > 0:
                            av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                        else:
                            av_price_obj.av_price = int(prices[i])
                        av_price_obj.save()
                    #==========End Of Av_price_module====================
                        product = Product.objects.get(imei=imeis[i])
                        # creating remainder_history object
                        rho = RemainderHistory.objects.create(
                            document=document,
                            created=dateTime,
                            rho_type=doc_type,
                            shop=shop,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            av_price=av_price_obj.av_price,
                            incoming_quantity=quantities[i],
                            outgoing_quantity=0,
                            sub_total=int(quantities[i])*int(prices[i]),
                        )
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                            rho.pre_remainder=rho_latest_before.current_remainder
                            rho.current_remainder=rho_latest_before.current_remainder + int(quantities[i])
                        else:
                            rho.pre_remainder=0
                            rho.current_remainder=int(quantities[i])
                        if shop.retail==True:
                            rho.retail_price=int(prices[i])
                        else:
                            rho.wholesale_price=int(prices[i])
                        rho.save()
                        document_sum+=rho.sub_total
                        # checking docs after remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                            remainder=rho.current_remainder
                            sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).order_by('created')
                            for obj in sequence_rhos_after:
                                obj.pre_remainder = remainder
                                obj.current_remainder = (
                                    remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder = obj.current_remainder

                    document.sum=document_sum
                    registers = Register.objects.filter(document=document)
                    for register in registers:
                        register.delete()
                else:
                    for i in range(n):
                        product = Product.objects.get(imei=imeis[i])
                        register = Register.objects.get(document=document, product=product)
                        register.price = prices[i]
                        register.quantity = quantities[i]
                        register.sub_total = sub_totals[i]
                        register.sub_total = int(prices[i]) * int(quantities[i])
                        register.save()
                        document_sum+=int(register.sub_total)
                document.sum = document_sum
                document.created=dateTime
                document.shop_receiver=shop
                document.save()
                return redirect("log")
        else:
            context = {
                "registers": registers,
                "shops": shops,
                'shop': shop,
                'dateTime': dateTime,
                "document": document,
                "categories": categories,
            }
            return render(request, "documents/change_recognition_unposted.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def unpost_recognition(request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:   
        document = Document.objects.get(id=document_id)
        shop=document.shop_receiver
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # checking rhos before
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
                remainder=rho_latest_before.current_remainder
            else:
                remainder=0
            #checking rhos after
            if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
                sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).order_by('created')
                for obj in sequence_rhos_after:
                    obj.pre_remainder = remainder
                    obj.current_remainder = (
                        remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    obj.save()
                    remainder = obj.current_remainder
        #===========Av_price_module====================================
            av_price_obj = AvPrice.objects.get(imei=rho.imei)
            av_price_obj.current_remainder -= rho.incoming_quantity
            shop=Shop.objects.get(id=rho.shop.id)
            if shop.retail == True:
                av_price_obj.sum-= rho.retail_price * rho.incoming_quantity
            else:
                av_price_obj.sum-= rho.wholesale_price * rho.incoming_quantity
            if av_price_obj.current_remainder > 0:
                av_price_obj.av_price=av_price_obj.sum/av_price_obj.current_remainder
            else:
                av_price_obj.av_price=0
            av_price_obj.save()
        
            register=Register.objects.create(
                document=document,
                product=product,
                quantity=rho.incoming_quantity,
                sub_total=rho.sub_total
            )
            if shop.retail == True:
                register.price = rho.retail_price
            else:
                register.price=rho.av_price
            register.save()
            rho.delete()
        doc_sum=0
        registers=Register.objects.filter(document=document)
        for register in registers:
            doc_sum+=register.sub_total
        document.posted = False
        document.sum=doc_sum
        document.save()
        return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def delete_recognition(request, document_id):
    document = Document.objects.get(id=document_id)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder -= rho.incoming_quantity
        av_price.sum -= rho.incoming_quantity * rho.av_price
        av_price.av_price = av_price.sum / av_price.current_remainder
        av_price.save()

        if RemainderHistory.objects.filter(
            shop=rho.shop, imei=rho.imei, created__lt=rho.created
        ).exists():
            sequence_rhos_before = RemainderHistory.objects.filter(
                shop=rho.shop, imei=rho.imei, created__lt=rho.created
            )
            rho_latest_before = sequence_rhos_before.latest("created")
            remainder_current = RemainderCurrent.objects.get(
                shop=rho.shop, imei=rho.imei
            )
            remainder_current.current_remainder = rho_latest_before.current_remainder
            # remainder_current.total_av_price=rho_latest_before.sub_total
            # remainder_current.av_price=rho_latest_before.av_price
            remainder_current.save()
        else:
            remainder_current = RemainderCurrent.objects.get(
                shop=rho.shop, imei=rho.imei
            )
            remainder_current.current_remainder = 0
            # remainder_current.total_av_price=0
            # remainder_current.av_price=0
            remainder_current.save()

        if RemainderHistory.objects.filter(
            shop=rho.shop, imei=rho.imei, created__gt=rho.created
        ).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(
                shop=rho.shop, imei=rho.imei, created__gt=rho.created
            )
            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder_current.current_remainder
                obj.current_remainder = (
                    remainder_current.current_remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder_current.current_remainder = obj.current_remainder
                remainder_current.save()

        rho.delete()
    for recognition in recognitions:
        recognition.delete()
    document.delete()
    return redirect("log")
#===================================================================================================
def signing_off_sim_auto(request):
    doc_type = DocumentType.objects.get(name="Списание ТМЦ")
    doc_type_transfer = DocumentType.objects.get(name="Перемещение ТМЦ")
    #this is done to exclude transfer_sender rhos
    # "False" for Transfer(send) "True" for Transfer(receive)
    rhos=RemainderHistory.objects.exclude(rho_type=doc_type_transfer, status=False)
    if request.method == "POST":
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
        file = request.FILES["file_name"]
        # print(file)
        # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        document = Document.objects.create(
            created=dateTime,
            user=request.user, 
            title=doc_type,
            posted=True
        )
        document_sum = 0
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            # checking docs before remainder_history
            if rhos.filter(imei=row.Imei, created__lt=document.created).exists():
                rho_latest_before = rhos.filter(imei=row.Imei, created__lt=document.created).latest('created')
                if rho_latest_before.current_remainder >0:
                    # creating remainder_history
                    rho = RemainderHistory.objects.create(
                        user=request.user,
                        document=document,
                        rho_type=document.title,
                        created=document.created,
                        shop=rho_latest_before.shop,
                        category=rho_latest_before.category,
                        supplier=rho_latest_before.supplier,
                        #product_id=product,
                        imei=row.Imei,
                        name=rho_latest_before.name,
                        pre_remainder=rho_latest_before.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=row.Quantity,
                        current_remainder=rho_latest_before.current_remainder - int(row.Quantity),
                        wholesale_price=int(row.Price),
                        sub_total=int(row.Price) * int(row.Quantity),
                    )
                    document_sum += int(rho.sub_total)
    #============Av_price_module====================
                    if AvPrice.objects.filter(imei=row.Imei).exists():
                        av_price_obj = AvPrice.objects.get(imei=row.Imei)
                        av_price_obj.current_remainder -= int(row.Quantity)
                        av_price_obj.sum -= int(row.Quantity) * int(row.Price)
                    #     if av_price_obj.current_remainder > 0:
                    #         av_price_obj.av_price = int(av_price_obj.sum) / int(av_price_obj.current_remainder)
                    #     else:
                    #         av_price_obj.av_price=int(row.Price)
                    #     av_price_obj.save()
                    # else:
                    #     av_price_obj = AvPrice.objects.create(
                    #         name=product.name,
                    #         imei=product.imei,
                    #         current_remainder=int(row.Quantity),
                    #         sum=int(row.Quantity) * int(row.Price),
                    #         av_price=int(row.Price),
                    #     )
                    #rho.av_price=av_price_obj.av_price
                    rho.save()
            sim_signing_off_record=SimSigningOffRecord.objects.create(
                user=request.user,
                document=document,
                doc_type=doc_type,
                created=document.created,
                name=row.Title,
                imei=row.Imei,
            )
            # checking docs after remainder_history
            # if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__gt=rho.created).exists():
            #     sequence_rhos_after = RemainderHistory.objects.filter(imei=product.imei, shop=shop, created__gt=rho.created).order_by('created')
            #     pre_remainder=rho.current_remainder
            #     for obj in sequence_rhos_after:
            #         obj.pre_remainder = pre_remainder
            #         obj.current_remainder = (
            #             pre_remainder
            #             + obj.incoming_quantity
            #             - obj.outgoing_quantity
            #         )
            #         obj.save()
            #         pre_remainder = obj.current_remainder
        document.sum = document_sum
        document.save()
        return redirect("log")
    else:
        # context = {
        #     "shops": shops,
        #     'shop_default': shop_default,
        #     "suppliers": suppliers, 
        #     "categories": categories,
        #     }
        return render(request, "documents/signing_off_sim_auto.html")

def identifier_signing_off(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("signing_off", identifier.id)
    else:
        return redirect("login")

def check_signing_off(request, identifier_id):
    users=Group.objects.get(name="admin").user_set.all()
    if request.user in users:
        identifier = Identifier.objects.get(id=identifier_id)
        # if 'imei' in request.GET:
        if request.method == "POST":
            imei = request.POST["imei"]
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            if Product.objects.filter(imei=imei).exists():
                product = Product.objects.get(imei=imei)
                if RemainderHistory.objects.filter(shop=shop, imei=imei).exists():
                    rho_latest=RemainderHistory.objects.filter(shop=shop, imei=imei).latest('created')
                    if rho_latest.current_remainder < 0:
                        messages.error(request, "Данное наименование отсутствует на балансе данной торговой точки.")
                        return redirect("signing_off", identifier.id)
                if Register.objects.filter(identifier=identifier, product=product).exists():
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.quantity += 1
                    register.sub_total=register.price*register.quantity
                    register.save()
                    return redirect("signing_off", identifier.id)
                else:
                    register = Register.objects.create(
                        identifier=identifier,
                        product=product,
                        quantity=1,
                    )
                    if shop.retail == True:
                        register.price=rho_latest.retail_price
                    else:
                        register.price=rho_latest.wholesale_price
                    register.sub_total=register.price*register.quantity
                    register.save()
                return redirect("signing_off", identifier.id)   
            else:
                messages.error(request, "Данное наименование отсутствует в БД.")
                return redirect("signing_off", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def check_signing_off_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    shop=document.shop_sender
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if RemainderCurrent.objects.filter(shop=shop, imei=imei).exists():
                remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imei)
                if Register.objects.filter(document=document, product=product, deleted=True).exists():
                    register = Register.objects.get(document=document, product=product, deleted=True)
                    register.deleted = False
                    register.save()
                elif Register.objects.filter(document=document, product=product).exists():
                    messages.error(request, "Вы уже ввели данное наименование.")
                    return redirect("change_signing_off_unposted", document.id)
                else:
                    if shop.retail==True:
                        register = Register.objects.create(
                            document=document, 
                            product=product,
                            price=remainder_current.retail_price,
                            sub_total=remainder_current.retail_price,
                            new=True
                        )
                        if register.price==0:
                            messages.error(request, "Розничная цена для данного наименования отсутствует. Введите ее.")
                            return redirect ('change_signing_off_unposted', document_id)
                        else:
                            messages.error(request, "В поле цена введена розничная цена для данного наименования.")
                            return redirect ('change_signing_off_unposted', document_id)
                    else:
                        if AvPrice.objects.filter(imei=imei).exists():
                            av_price_obj = AvPrice.objects.get(imei=imei)
                            register = Register.objects.create(
                                document=document,
                                product=product,
                                price=av_price_obj.av_price,
                                quantity=1,
                                sub_total=av_price_obj.av_price,
                                new=True
                            )
                            messages.error(request, "В поле цена введена усредненная закупочная цена для данного наименования.")
                            return redirect ('change_signing_off_unposted', document_id)
                        else:
                            messages.error(request, "Усредненная закупочная цена для данного наименования отсутствует. Введите ее.")
                            return redirect ('change_signing_off_unposted', document_id) 
                return redirect ('change_signing_off_unposted', document_id)
            else:
                messages.error(request, "Данное наименование отсутствует на остатках данной фирмы.")
                return redirect ('change_signing_off_unposted', document_id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect ('change_signing_off_unposted', document_id)

def signing_off(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    session_shop=request.session['session_shop']
    shop=Shop.objects.get(id=session_shop)
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()

    context = {
        "identifier": identifier,
        "shop": shop,
        "registers": registers,
    }
    return render(request, "documents/signing_off.html", context)

def delete_line_signing_off(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("signing_off", identifier.id)

def delete_line_unposted_signing_off (request, imei, document_id):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.delete()
    return redirect("change_signing_off_unposted", document.id)

def clear_signing_off(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("signing_off", identifier.id)

def signing_off_input(request, identifier_id):
    users=Group.objects.get(name="admin").user_set.all()
    if request.user in users:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        doc_type = DocumentType.objects.get(name="Списание ТМЦ")
        if request.method == "POST":
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices=request.POST.getlist('price', None)
            sub_totals=request.POST.getlist('sub_total', None)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("signing_off", identifier.id)
            if post_check == True:
                #checking availability of the item at the shop
                n = len(names)
                #checking availability
                for i in range(n):
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                        rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                        if rho_latest_before.current_remainder < int(quantities[i]):
                            string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                            messages.error(request,  string)
                            return redirect("signing_off", identifier.id)
                    else:
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("signing_off", identifier.id)
                #creating new document
                document = Document.objects.create(
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    shop_sender=shop
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product=Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history. There is no need in 'If check' since it's done during availability check
                    rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    #creating new rho
                    rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=document.title,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=rho_latest_before.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=rho_latest_before.current_remainder
                        - int(quantities[i]),
                        sub_total=int(quantities[i]) * int(prices[i]),
                    )
                    if shop.retail==True:
                        rho.retail_price=prices[i]
                    else:
                        rho.av_price=prices[i]
                    rho.save()
                    document_sum+=rho.sub_total
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
                        remainder=rho.current_remainder
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created)
                        sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder
                                + int(obj.incoming_quantity)
                                - int(obj.outgoing_quantity)
                            )
                            obj.save()
                            remainder = obj.current_remainder
                    #calculating av_price for the remainder
                    AvPrice.objects.filter(imei=imeis[i])
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()

                document.sum = document_sum
                document.save()
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")

            else:
                document = Document.objects.create(
                    shop_sender=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=False
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
                document.sum = document_sum
                document.save()
                identifier.delete()
                return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def delete_signing_off(request, document_id):
    document = Document.objects.get(id=document_id)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder += rho.incoming_quantity
        av_price.sum += rho.incoming_quantity * av_price.av_price
        # av_price.av_price=av_price.sum/av_price.current_remainder
        av_price.save()
        if RemainderHistory.objects.filter(
            shop=rho.shop, imei=rho.imei, created__lt=rho.created
        ).exists():
            sequence_rhos_before = RemainderHistory.objects.filter(
                shop=rho.shop, imei=rho.imei, created__lt=rho.created
            )
            rho_latest_before = sequence_rhos_before.latest("created")
            remainder_current = RemainderCurrent.objects.get(
                shop=rho.shop, imei=rho.imei
            )
            remainder_current.current_remainder = rho_latest_before.current_remainder
            # remainder_current.total_av_price=rho_latest_before.sub_total
            # remainder_current.av_price=rho_latest_before.av_price
            remainder_current.save()
        else:
            remainder_current = RemainderCurrent.objects.get(
                shop=rho.shop, imei=rho.imei
            )
            remainder_current.current_remainder = 0
            # remainder_current.total_av_price=0
            # remainder_current.av_price=0
            remainder_current.save()
        if RemainderHistory.objects.filter(
            shop=rho.shop, imei=rho.imei, created__gt=rho.created
        ).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(
                shop=rho.shop, imei=rho.imei, created__gt=rho.created
            )
            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder_current.current_remainder
                obj.current_remainder = (
                    remainder_current.current_remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder_current.current_remainder = obj.current_remainder
                remainder_current.save()
    rho.delete()
    for signoff in signoffs:
        signoff.delete()
    document.delete()
    return redirect("log")

def change_signing_off_posted (request, document_id):
    document = Document.objects.get(id=document_id)
    #doc_type=DocumentType.objects.get(name='Списание ТМЦ')
    if document.base_doc:
        base_document=Document.objects.get(id=document.base_doc)
    else:
        base_document="Not Existing"
    if RemainderHistory.objects.filter(document=document).exists():
        rhos = RemainderHistory.objects.filter(document=document).order_by("name")
        shop = document.shop_sender
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()

        context = {
            "rhos": rhos,
            "document": document,
            'base_document': base_document,
            'shop': shop,
            "dateTime": dateTime,
        }
        return render(request, "documents/change_signing_off_posted.html", context)
    else:
        messages.error(request, "В ходе инвентаризации недостач и списаний выявлено не было")
        return redirect ('log')
       
def change_signing_off_unposted (request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        document = Document.objects.get(id=document_id)
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
        shops = Shop.objects.all()
        shop=document.shop_sender
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        categories = ProductCategory.objects.all()
        doc_type = DocumentType.objects.get(name="Списание ТМЦ")
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method=='POST':
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            sub_totals = request.POST.getlist("sub_total", None)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request,  'Вы не ввели ни одного наименования')
                return redirect("change_signing_off_unposted", document.id)
            if post_check == True:
                n = len(names)
                for i in range(n):
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop,created__lt=dateTime).exists():
                        rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                        if rho_latest_before.current_remainder < int(quantities[i]):
                            string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                            messages.error(request,  string)
                            return redirect("change_signing_off_unposted", document.id)
                    else:
                        string=f'Документ не проведен. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
                        messages.error(request,  string)
                        return redirect("change_signing_off_unposted", document.id)

                # end of availability check
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history
                    rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                    # creating remainder_history
                    rho = RemainderHistory.objects.create(
                        document=document,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=rho_latest_before.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=rho_latest_before.current_remainder - int(quantities[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    if shop.retail==True:
                        rho.retail_price=prices[i]
                    else:
                        rho.av_price=prices[i]
                    rho.save()
                    document_sum += rho.sub_total
                    #checking rhos after           
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
                        remainder=rho.current_remainder
                        sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder
                                + obj.incoming_quantity
                                - obj.outgoing_quantity
                            )
                            obj.save()
                            remainder= obj.current_remainder
                    #calculating av_price for the remainder
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()
                document.posted = True
                document.sum=document_sum
                document.created=dateTime
                document.shop_sender=shop
                document.save()
                registers = Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
                return redirect ('log')    
            else:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(document=document, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
                document.sum = document_sum
                document.created=dateTime
                document.shop_sender=shop
                document.save()
            return redirect("log")
        
        else:
            context = {
                "registers": registers,
                "document": document,
                "shops": shops,
                "shop": shop,
                'dateTime': dateTime,
            }
            return render(request, "documents/change_signing_off_unposted.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def unpost_signing_off (request, document_id):
    document = Document.objects.get(id=document_id)
    shop=document.shop_sender
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    for rho in rhos:
        product = Product.objects.get(imei=rho.imei)
        # deleting existing rhos
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
            rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
            remainder=rho_latest_before.current_remainder
        else:
            remainder=0
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created)
            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder
                obj.current_remainder = (
                    remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder = obj.current_remainder
        av_price_obj = AvPrice.objects.get(imei=rho.imei)
        av_price_obj.current_remainder += rho.outgoing_quantity        
        av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
        av_price_obj.save()
        #creating registers
        register=Register.objects.create(
            document=document,
            product=product,
            quantity=rho.outgoing_quantity,
        )
        if shop.retail==True:
            register.price=rho.retail_price
        else:
            register.price=rho.av_price
        register.sub_total=register.price*register.quantity
        register.save()
        rho.delete()
    document.posted = False
    document.save()
    return redirect("log")
# ================================================================================================

def identifier_return(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("return_doc", identifier.id)
    else:
        return redirect("login")

def check_return(request, identifier_id):
    if request.user.is_authenticated:
        # shops = Shop.objects.all()
        users=Group.objects.get(name="sales").user_set.all()
        # categories = ProductCategory.objects.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        # if 'imei' in request.GET:
        if request.method == "POST":
            imei = request.POST["imei"]
            if '/' in imei:
                imei=imei.replace('/', '_')
            # if request.user in users:
            #     shop=request.session['session_shop']
            #     shop=Shop.objects.get(id=shop)
            #     dateTime=datetime.datetime.now()
            if Product.objects.filter(imei=imei).exists():
                product = Product.objects.get(imei=imei)
                if Register.objects.filter(identifier=identifier, product=product).exists():
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.quantity += 1
                    register.save()
                    return redirect("return_doc", identifier.id)
                else:
                    register = Register.objects.create(
                        identifier=identifier,
                        product=product,
                        quantity=1,
                    )
                return redirect("return_doc", identifier.id)
            else:
                messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
                return redirect("return_doc", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def check_return_unposted(request, document_id):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        document = Document.objects.get(id=document_id)
        registers = Register.objects.filter(document=document)
        shop=document.shop_receiver
        # if 'imei' in request.GET:
        if request.method == "POST":
            imei = request.POST["imei"]
            if '/' in imei:
                imei=imei.replace('/', '_')
            if Product.objects.filter(imei=imei).exists():
                product = Product.objects.get(imei=imei)
                if Register.objects.filter(document=document, product=product).exists():
                    messages.error(request, "Вы уже ввели данное наименование.")
                    return redirect("change_return_unposted", document.id)
                else:
                    # if shop.retail==True:
                    register = Register.objects.create(
                        document=document, 
                        product=product,
                        # price=remainder_current.retail_price,
                        # sub_total=remainder_current.retail_price,
                    )     
                return redirect("change_return_unposted", document.id)
            else:
                messages.error(request, "Данное наименование отсутствует в БД.")
                return redirect("change_return_unposted", document.id)
    auth.logout(request)
    return redirect("login")

def return_doc(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all()
        registers = Register.objects.filter(identifier=identifier)
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        context = {
            "identifier": identifier,
            "shops": shops,
            "registers": registers,
        }
        return render(request, "documents/return_doc.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def delete_line_return(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("return_doc", identifier.id)

def delete_line_unposted_return (request, imei, document_id):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    register = Register.objects.get(document=document, product=product)
    register.delete()
    return redirect("change_return_unposted", document.id)

def clear_return(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("return_doc", identifier.id)

def return_input(request, identifier_id):
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        doc_type = DocumentType.objects.get(name="Возврат ТМЦ")
        base_doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            if request.user in users:
                session_shop=request.session['session_shop']
                shop = Shop.objects.get(id=session_shop)
                dateTime = datetime.datetime.now()
            else:
                shop=request.POST['shop']
                shop=Shop.objects.get(id=shop)
           #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if not imeis:
                messages.error(request,"Вы не ввели ни одного наименования",)
                return redirect("return_doc", identifier.id)
            #checking if return is based on sale for this shop
            n = len(names)
            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, rho_type=base_doc_type, created__lt=dateTime,).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime, rho_type=base_doc_type).latest('created')
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} никогда не продавался с баланса данной фирмы.'
                    messages.error(request,  string)
                    return redirect("return_doc", identifier.id)

            # posting the document
            if post_check == True:
                
                #==First Section of Cash Register Module (Checking if the shift if open less than 12 hours. Otherwise it won't print)===========
                if shop.cash_register==False:
                    #checking if shift is open for more than 12 hours
                    if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                        print ('Смена открыта более 12 часов')
                        messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                        return redirect ('sale_interface')
                #=============End of First Section of Cash Register Module========================================
                document = Document.objects.create(
                    shop_receiver=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=True
                )
                n = len(names)
                document_sum = 0
                jsonData=[]#list for json structure for cash register
                for i in range(n): 
                    product=Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                        rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                        pre_remainder=rho_latest_before.current_remainder
                    else:
                        pre_remainder=0
                    #creating rho
                    rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=pre_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        #av_price=av_price,
                        current_remainder=pre_remainder + int(quantities[i]),
                        retail_price=prices[i],
                        sub_total= int(quantities[i]) * int(prices[i]),
                    )
                    document_sum+=rho.sub_total
                    #calculating av_price for the remainder
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        sale_rho_latest = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, rho_type=base_doc_type).latest('created')
                        av_price_obj=AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        #av_price_obj.av_price = int(sale_rho_latest.av_price)
                        av_price_obj.sum += int(quantities[i]) * int(sale_rho_latest.av_price)
                        av_price_obj.save()
                        if av_price_obj.current_remainder > 0:
                            av_price_obj.av_price=av_price_obj.sum / av_price_obj.current_remainder
                        else:
                            av_price_obj.av_price = int(sale_rho_latest.ave_price)
                        av_price_obj.save()
                    else:
                        av_price_obj=AvPrice.objects.create (
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            av_price=int(prices[i]),
                            sum=int(quantities[i])*int(prices[i])
                        )
                    av_price_obj.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
                        remainder=rho.current_remainder
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created)
                        sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder
                            obj.current_remainder = (
                                remainder
                                + obj.incoming_quantity
                                - obj.outgoing_quantity
                            )
                            obj.save()
                            remainder = obj.current_remainder
                    document.sum = document_sum
                    document.save()
                    # operations with cash
                    if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                        cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                        cash_remainder=cho_latest_before.current_remainder
                    else:
                        cash_remainder=0 
                    cho = Cash.objects.create(
                        shop=shop,
                        created=dateTime,
                        cho_type=doc_type,
                        document=document,
                        user=request.user,
                        pre_remainder=cash_remainder,
                        cash_out=document_sum,
                        cash_in=0,
                        current_remainder=cash_remainder - document_sum,
                    )
                    if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                        sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created).order_by('created')
                        cash_remainder=cho.current_remainder
                        for obj in sequence_chos_after:
                            obj.pre_remainder = cash_remainder
                            obj.current_remainder = (cash_remainder+ obj.cash_in - obj.cash_out)
                            obj.save()
                            cash_remainder = obj.current_remainder
                    # end of operations with cash
                    #===============creating dictionaries to insert in json structure for cash register 
                    retail_price=round(float(rho.retail_price), 2)#converts integer number to float number with two digits after divider
                    sub_total=round(float(rho.sub_total), 2)#converts integer number to float number with two digits after divider  
                    quantity=round(float(rho.incoming_quantity), 3)#converts integer number to float number with three digits after divider
                    json_dict={
                        "type": "position",
                        "name": rho.name,
                        "price": retail_price,
                        "quantity": quantity,
                        "amount": sub_total,
                        "tax": {
                            "type": "none"
                        }
                        }
                    json_type = {
                        "type": "text"
                        }
                    jsonData.append(json_dict)
                    jsonData.append(json_type)
                #==================end of dictionnaries to insert to json structure for cash register
                #================Cash Register Module / Sell ===================
                if shop.cash_register==False:
                    sum_to_pay_json=round(float(document.sum), 2)#total sum to pay to be inserted in json structure for cash register
                    #time.sleep(1)
                    auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                    uuid_number=uuid.uuid4()#creatring a unique identification number
                    task = {
                    "uuid": str(uuid_number),
                    "request": [   
                    {
                    "type": "sellReturn",
                    "items": jsonData,

                        "payments":[{
                                "type": "cash",
                                "sum": sum_to_pay_json
                            }]
                    }]}
            
                    try:
                        response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                        # status_code=response.status_code
                        # print(status_code)
                        # text=response.text
                        # print(text)
                        # url=response.url
                        # json=response.json()
                        if shop.shift_status == True:
                            shop.shift_status = False
                            shop.save()
                    except:
                        messages.error(request, "Документ не проведен. Сообщите администратору.")
                        return redirect ('sale_interface')
                #=================End of Cash Register Module==============


                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect ('log')
            
            #saving registers without posting
            else:
                document = Document.objects.create(
                    shop_receiver=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=False
                )
                n = len(names)
                sum = 0
                for i in range(n):
                    sum += int(prices[i]) * int(quantities[i])
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(identifier=identifier, product=product)
                    register.price = prices[i]
                    register.shop = shop
                    register.quantity = quantities[i]
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.document = document
                    register.identifier = None
                    register.save()
                identifier.delete()
                document.sum = sum
                document.save()
                users=Group.objects.get(name="sales").user_set.all()
                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")
    else:
        return redirect ('login')

def change_return_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    users=Group.objects.get(name="sales").user_set.all()
    group=Group.objects.get(name="admin").user_set.all()
    shop=document.shop_receiver
    document_datetime=document.created
    document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
    registers = (Register.objects.filter(document=document).exclude(deleted=True).order_by("created"))
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Возврат ТМЦ")
    base_doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        sub_totals = request.POST.getlist("sub_total", None)
        #=============DateTime change unposted module=====================
        dateTime = request.POST["dateTime"]
        # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
        dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
        current_dt=datetime.datetime.now()
        mics=current_dt.microsecond
        tdelta_1=datetime.timedelta(microseconds=mics)
        secs=current_dt.second
        tdelta_2=datetime.timedelta(seconds=secs)
        tdelta_3=tdelta_1+tdelta_2
        dateTime=dateTime+tdelta_3
        #===========End of DateTime change unposted module
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        if not imeis:
            messages.error(request,"Вы не ввели ни одного наименования",)
            return redirect("change_return_unposted", document.id)
        # posting the document
        if post_check == True:
            #checking if return is based on sale for this shop
            n = len(names)
            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime, rho_type=base_doc_type).exists():
                    rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime, rho_type=base_doc_type).latest('created')
                else:
                    string=f'Документ не проведен. Товар с IMEI {imeis[i]} никогда не продавался с баланса данной фирмы.'
                    messages.error(request,  string)
                    return redirect("change_return_unposted", document.id)  
            n = len(names)
            document_sum = 0
            for i in range(n):
                product=Product.objects.get(imei=imeis[i])
                # checking docs before remainder_history
                rho_latest_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                # creating remainder_history
                rho = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    rho_type=doc_type,
                    category=product.category,
                    imei=imeis[i],
                    name=names[i],
                    retail_price=prices[i],
                    pre_remainder=rho_latest_before.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=rho_latest_before.current_remainder
                    + int(quantities[i]),
                    sub_total= int(quantities[i]) * int(prices[i]),
                )
                document_sum+=rho.sub_total  
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                    created__gt=dateTime).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
                    sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                    for obj in sequence_rhos_after:
                        obj.pre_remainder = remainder
                        obj.current_remainder = (
                            remainder
                            + obj.incoming_quantity
                            - obj.outgoing_quantity
                            )
                        obj.save()
                        remainder = obj.current_remainder
                av_price = AvPrice.objects.get(imei=imeis[i])
                av_price.current_remainder += int(quantities[i])
                av_price.sum += int(quantities[i]) * av_price.av_price
                av_price.save()
            document.sum = document_sum
            document.created=dateTime
            document.shop_receiver=shop
            document.posted=True
            document.save()
            # operations with cash
            if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                cash_remainder = cho_latest_before.current_remainder
            else:
                cash_remainder = 0
            cho = Cash.objects.create(
                shop=shop,
                cho_type=doc_type,
                created=dateTime,
                document=document,
                user=request.user,
                pre_remainder=cash_remainder,
                cash_out=document_sum,
                cash_in=0,
                current_remainder=cash_remainder - document_sum,
            )
     
            #changing cash objects after
            if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (cash_remainder + obj.cash_in - obj.cash_out)
                    obj.save()
                    cash_remainder = obj.current_remainder
            # end of operations with cash
            registers=Register.objects.filter(document=document)
            for register in registers:
                register.delete()
            return redirect ('log')
        else:
            n = len(names)
            document_sum = 0
            for i in range(n):
                product = Product.objects.get(imei=imeis[i])
                register = Register.objects.get(document=document, product=product)
                register.price = prices[i]
                register.quantity = quantities[i]
                register.sub_total = sub_totals[i]
                register.document = document
                register.save()
                document_sum += int(register.sub_total)
            document.sum = document_sum
            document.created=dateTime
            document.shop_receiver=shop
            document.save()
            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect("log")
    else:
        context = {
            "registers": registers,
            "shops": shops,
            'shop': shop,
            "document": document,
            'document_datetime': document_datetime
        }
        return render(request, "documents/change_return_unposted.html", context)

def change_return_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    shop=document.shop_receiver
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    #categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop_current = document.shop_receiver
    rhos=RemainderHistory.objects.filter(document=document)
    numbers = rhos.count()
    for rho, i in zip(rhos, range(numbers)):
        rho.number = i + 1
        rho.save()
   
    context = {
        "document": document,
        'rhos': rhos,
        "shops": shops,
        'dateTime': dateTime,
        'shop': shop
    }
    return render(request, "documents/change_return_posted.html", context)

def unpost_return(request, document_id):
    document = Document.objects.get(id=document_id)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        product=Product.objects.get(imei=rho.imei)
        #checking rhos before
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
            rho_latest_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).latest('created')
            pre_remainder=rho_latest_before.current_remainder
        else:
            pre_remainder=0
        #checking rhos after
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).order_by('created')
            remainder=pre_remainder
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder
                obj.current_remainder = (
                    remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder = obj.current_remainder
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder -= rho.incoming_quantity
        av_price.sum -= rho.incoming_quantity * av_price.av_price
        av_price.save()
        register=Register.objects.create(
            document=document,
            product=product,
            quantity=rho.incoming_quantity,
            price=rho.retail_price,
            sub_total=rho.sub_total
        )
        rho.delete()
    document.posted = False
    document.save()

    #deleting cash operations
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        cho_latest_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created).latest('created')
        pre_cash_remainder = cho_latest_before.current_remainder
    else:
        pre_cash_remainder = 0
    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        sequence_chos_after = Cash.objects.filter(shop=cho.shop, created__gt=cho.created).order_by('created')
        cash_remainder=pre_cash_remainder
        for obj in sequence_chos_after:
            obj.pre_remainder = cash_remainder
            obj.current_remainder = (
                cash_remainder + obj.cash_in - obj.cash_out
            )
            obj.save()
            cash_remainder= obj.current_remainder
    cho.delete()
    return redirect("log")
#==============================================
def identifier_supplier_return(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("return_doc", identifier.id)
    else:
        return redirect("login")

def supplier_return_sim_auto(request):
    doc_type = DocumentType.objects.get(name="Возврат ТМЦ поставщику")
    doc_type_transfer = DocumentType.objects.get(name="Перемещение ТМЦ")
    #this is done to exclude transfer_sender rhos
    # "False" for Transfer(send) "True" for Transfer(receive)
    rhos=RemainderHistory.objects.exclude(rho_type=doc_type_transfer, status=False)
    if request.method == "POST":
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
        file = request.FILES["file_name"]
        # print(file)
        # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        document = Document.objects.create(
            created=dateTime,
            user=request.user, 
            title=doc_type,
            posted=True
        )
        document_sum = 0
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            # checking docs before remainder_history
            if rhos.filter(imei=row.Imei, created__lt=document.created).exists():
                rho_latest_before = rhos.filter(imei=row.Imei, created__lt=document.created).latest('created')
                if rho_latest_before.current_remainder >0:
                    # creating remainder_history
                    rho = RemainderHistory.objects.create(
                        user=request.user,
                        document=document,
                        rho_type=document.title,
                        created=document.created,
                        shop=rho_latest_before.shop,
                        category=rho_latest_before.category,
                        supplier=rho_latest_before.supplier,
                        #product_id=product,
                        imei=row.Imei,
                        name=rho_latest_before.name,
                        pre_remainder=rho_latest_before.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=row.Quantity,
                        current_remainder=rho_latest_before.current_remainder - int(row.Quantity),
                        wholesale_price=int(row.Price),
                        sub_total=int(row.Price) * int(row.Quantity),
                    )
                    document_sum += int(rho.sub_total)
    #============Av_price_module====================
                    if AvPrice.objects.filter(imei=row.Imei).exists():
                        av_price_obj = AvPrice.objects.get(imei=row.Imei)
                        av_price_obj.current_remainder -= int(row.Quantity)
                        av_price_obj.sum -= int(row.Quantity) * int(row.Price)
                    #     if av_price_obj.current_remainder > 0:
                    #         av_price_obj.av_price = int(av_price_obj.sum) / int(av_price_obj.current_remainder)
                    #     else:
                    #         av_price_obj.av_price=int(row.Price)
                    #     av_price_obj.save()
                    # else:
                    #     av_price_obj = AvPrice.objects.create(
                    #         name=product.name,
                    #         imei=product.imei,
                    #         current_remainder=int(row.Quantity),
                    #         sum=int(row.Quantity) * int(row.Price),
                    #         av_price=int(row.Price),
                    #     )
                    #rho.av_price=av_price_obj.av_price
                    rho.save()
            # checking docs after remainder_history
            # if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__gt=rho.created).exists():
            #     sequence_rhos_after = RemainderHistory.objects.filter(imei=product.imei, shop=shop, created__gt=rho.created).order_by('created')
            #     pre_remainder=rho.current_remainder
            #     for obj in sequence_rhos_after:
            #         obj.pre_remainder = pre_remainder
            #         obj.current_remainder = (
            #             pre_remainder
            #             + obj.incoming_quantity
            #             - obj.outgoing_quantity
            #         )
            #         obj.save()
            # pre_remainder = obj.current_remainder
            
            sim_supplier_return=SimSupplierReturnRecord.objects.create(
                user=request.user,
                document=document,
                doc_type=doc_type,
                created=document.created,
                name=row.Title,
                imei=row.Imei,
            )
                            
        document.sum = document_sum
        document.save()
        return redirect("log")
    else:
        # context = {
        #     "shops": shops,
        #     'shop_default': shop_default,
        #     "suppliers": suppliers, 
        #     "categories": categories,
        #     }
        return render(request, "documents/supplier_return_sim_auto.html")

def supplier_return(request):
    pass

#==========================================================================================
# для изменения цены в документе Sale от предыдущих дат нет необходимости делать переоценку задней датой.
# Админ может просто сделать документ непроведенным и поменять стоимость.
# Проблема может возникнуть, если в документе ПРОДАЖА будет проставлена нестандартная цена, а следующий
# документ ПРОДАЖА берет эту нестандратную цену. Нужно сделать так, чтобы цена в документ ПРОДАЖА
# (check_sale) проставлялась только из документов Оприходование, Перемещение, Переоценка, Ввод остатков

# def identifier_revaluation_multi_shop(request):
#     if request.user.is_authenticated:
#         identifier = Identifier.objects.create()
#         return redirect("revaluation_document_multi_shop", identifier.id)
#     else:
#         return redirect("login")


def revaluation_document_multi_shop (request):
    identifier = Identifier.objects.create()
    if request.method == "POST":
        #post_checks = request.POST.getlist("checked", None)
        items = request.POST.getlist("check_box", None)
        #shops = request.POST.getlist("shop", None)
        for item in items:
            item=item.split('_')
            imei=str(item[0])
            shop=str(item[1])
            product=Product.objects.get(imei=imei)
            shop=Shop.objects.get(name=shop)
            register = Register.objects.create(
                identifier=identifier,
                name=product.name,
                imei=product.imei,
                shop=shop,
            )
        registers=Register.objects.filter(identifier=identifier)
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        context = {
            'registers': registers,
            'identifier': identifier,
        }
        return render (request, 'documents/revaluation_multi_shop.html', context)
    # else:
    #     registers=Register.objects.filter(identifier=identifier)
    #     context = {
    #         'registers': registers,
    #         'identifier': identifier,
    #     }
    #     return render (request, 'documents/revaluation_multi_shop.html', context)

def revaluation_input_multi_shop(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
    registers=Register.objects.filter(identifier=identifier)
    if request.method == "POST":
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        shops = request.POST.getlist("shop", None)
        prices_new = request.POST.getlist("price_new", None)
        #==============Time Module=========================================
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
            #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
            #==================End of time module================================
        if not imeis:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("log")
        n = len(names)
        for i in range(n):
            shop=Shop.objects.get(name=shops[i])
            document = Document.objects.create(
                shop_receiver=shop, 
                title=doc_type, 
                user=request.user, 
                created=dateTime,
                posted=True,
            )
            product=Product.objects.get(imei=imeis[i])
            if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                rho_latest = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                if rho_latest.current_remainder > 0:
                    pre_remainder=rho_latest.current_remainder
                else:
                    if RemainderHistory.objects.filter(document=document).exists():
                        rhos=RemainderHistory.objects.filter(document=document)
                        for rho in rhos:
                            rho.delete()
                    document.delete()
                    string=f'Документ не проведен. Кол-во товара с {imeis[i]} на складе равно 0'
                    messages.error(request, string)
                    return redirect("log")
            else:
                if RemainderHistory.objects.filter(document=document).exists():
                    rhos=RemainderHistory.objects.filter(document=document)
                    for rho in rhos:
                        rho.delete()
                document.delete()
                string=f'Документ не проведен. Товар с {imeis[i]} отсутствует наданном складе'
                messages.error(request, string)
                return redirect("log")
            # creating remainder_history
            rho = RemainderHistory.objects.create(
                document=document,
                rho_type=document.title,
                created=dateTime,
                shop=shop,
                category=product.category,
                imei=imeis[i],
                name=names[i],
                pre_remainder=pre_remainder,
                incoming_quantity=0,
                outgoing_quantity=0,
                retail_price=prices_new[i],
                current_remainder=pre_remainder,
                sub_total= int(pre_remainder)*int(prices_new[i]),
            )
            #sum+=rho.sub_total
            #document.sum=sum
            document.sum=rho.sub_total
            document.save()
        for register in registers:
            register.delete()
        identifier.delete()
        return redirect("log")


# def identifier_revaluation_multi_shop(request):
#     if request.user.is_authenticated:
#         identifier = Identifier.objects.create()
#         return redirect("revaluation", identifier.id)
#     else:
#         return redirect("login")

def revaluation_document (request):
    identifier = Identifier.objects.create()
    if request.method == "POST":
        items = request.POST.getlist("checked", None)
        shop=request.POST ['shop']
        shop=Shop.objects.get(id=shop)
        print(shop)
        n = len(items)
        for i in range(n): 
            product=Product.objects.get(imei=items[i])
            register = Register.objects.create(
                identifier=identifier,
                name=product.name,
                imei=product.imei,
                shop=shop,
            )
        registers=Register.objects.filter(identifier=identifier)
        numbers = registers.count()
        print(numbers)
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()

        context = {
            'registers': registers,
            'identifier': identifier,
            'shop': shop,
        }
        return render (request, 'documents/revaluation.html', context)

def revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    shop=registers[0].shop

    context = {
        "registers": registers,
        'identifier': identifier,
        'shop': shop,
    }
    return render(request, "documents/revaluation.html", context)

def revaluation_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        shop=Shop.objects.get(id=shop)
        if shop.retail == False:
            messages.success(request, "Вы не можете делать переоценку на оптовом складе.")
            return redirect("revaluation", identifier.id)
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        prices_new = request.POST.getlist("price_new", None)
        #==============Time Module=========================================
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
            #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
            #==================End of time module================================
        if not imeis:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("revaluation", identifier.id)
        document = Document.objects.create(
            shop_receiver=shop, 
            title=doc_type, 
            user=request.user, 
            created=dateTime,
            posted=True,
        )
        sum=0
        n = len(names)
        for i in range(n):
            product=Product.objects.get(imei=imeis[i])
            #============check quantity module===================================
            if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                rho_latest = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).latest('created')
                if rho_latest.current_remainder > 0:
                    pre_remainder=rho_latest.current_remainder
                else:
                    if RemainderHistory.objects.filter(document=document).exists():
                        rhos=RemainderHistory.objects.filter(document=document)
                        for rho in rhos:
                            rho.delete()
                    document.delete()
                    string=f'Документ не проведен. Кол-во товара с {imeis[i]} на складе равно 0'
                    messages.error(request, string)
                    return redirect("revaluation", identifier.id)
            else:
                if RemainderHistory.objects.filter(document=document).exists():
                    rhos=RemainderHistory.objects.filter(document=document)
                    for rho in rhos:
                        rho.delete()
                document.delete()
                string=f'Документ не проведен. Товар с {imeis[i]} отсутствует наданном складе'
                messages.error(request, string)
                return redirect("revaluation", identifier.id)
            # creating remainder_history
            rho = RemainderHistory.objects.create(
                document=document,
                rho_type=document.title,
                created=dateTime,
                shop=shop,
                category=product.category,
                imei=imeis[i],
                name=names[i],
                pre_remainder=pre_remainder,
                incoming_quantity=0,
                outgoing_quantity=0,
                retail_price=prices_new[i],
                current_remainder=pre_remainder,
                sub_total= int(pre_remainder)*int(prices_new[i]),
            )
            sum+=rho.sub_total
        for register in registers:
            register.delete()
        identifier.delete()
        document.sum=sum
        document.save()
        return redirect("log")

def change_revaluation_posted (request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        shop=document.shop_receiver
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        context = {
            "rhos": rhos,
            "document": document,
            'dateTime': dateTime,
            'shop': shop,
        }
        return render(request, "documents/change_revaluation_posted.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def revaluation_auto (request):
    if request.user.is_authenticated:
        shops=Shop.objects.all()
        categories = ProductCategory.objects.all()

        context = {
            "shops": shops,
            "categories": categories,
            }
        return render(request, "documents/revaluation_auto.html", context)
    else:
        return redirect ('login')

def delete_line_revaluation(request, imei, identifier_id, shop_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    shop=Shop.objects.get(id=shop_id)
    items = Register.objects.filter(identifier=identifier, product=product, shop=shop)
    for item in items:
        item.delete()
    return redirect("revaluation", identifier.id)

def clear_revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("revaluation", identifier.id)

def unpost_revaluation (request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        rhos = RemainderHistory.objects.filter(document=document)
        for rho in rhos:
            product=Product.objects.get(imei=rho.imei)
            register=Register.objects.create(
                document=document,
                product=product,
                quantity=rho.current_remainder,
                price=rho.retail_price,
                sub_total=rho.sub_total
            )
            rho.delete()
        document.posted=False
        document.save()
        return redirect ('log')
    else:
        return redirect ('login')

def change_revaluation_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers=Register.objects.filter(document=document)
    shop=document.shop_receiver
    context = {
        'document': document,
        'registers': registers,
        'shop': shop
    }
    return render (request, 'documents/change_revaluation_unposted.html', context)

def delete_line_revaluation_unposted (request, imei, document_id):
    pass



# def check_revaluation(request, identifier_id):
#    identifier = Identifier.objects.get(id=identifier_id)
#    if request.method == "POST":
#        imei = request.POST["imei"]
#        product=Product.objects.get(imei=imei)
#        if Register.objects.filter(identifier=identifier, product=product).exists():
#                messages.error(request, "Вы уже ввели данное наименование")
#                return redirect("revaluation", identifier.id)
#        else:
#            register = Register.objects.create(
#                identifier=identifier,
#                name=product.name,
#                imei=product.imei,
#            )
#            return redirect("revaluation", identifier.id)

#def check_revaluating_unposted (request, document_id):
#    pass

# def update_retail_price(request):
#     group = Group.objects.get(name="admin").user_set.all()
#     doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
#     dateTime = datetime.datetime.now()
#     if request.user in group:
#         if request.method == "POST":
#             imei = request.POST["imei"]
#             retail_price = request.POST["retail_price"]
#             shop = request.POST["shop"]
#             shop = Shop.objects.get(name=shop)

#             category = request.POST["category"]
#             category = ProductCategory.objects.get(name=category)

#             product = Product.objects.get(imei=imei)
#             document = Document.objects.create(
#                 created=dateTime,
#                 title=doc_type,
#                 user=request.user,
#                 posted=True,
#             )
#             rho_latest_before = RemainderHistory.objects.filter(
#                 shop=shop, imei=imei, created__lt=dateTime
#             ).latest("created")
#             rho = RemainderHistory.objects.create(
#                 document=document,
#                 created=document.created,
#                 rho_type=doc_type,
#                 user=request.user,
#                 shop=shop,
#                 product_id=product,
#                 category=product.category,
#                 imei=imei,
#                 name=product.name,
#                 retail_price=retail_price,
#                 pre_remainder=rho_latest_before.pre_remainder,
#                 incoming_quantity=0,
#                 outgoing_quantity=0,
#                 current_remainder=rho_latest_before.current_remainder,
#             )
#             return redirect("remainder_report_output", shop.id, category.id, dateTime)
#     else:
#         auth.logout(request)
#         return redirect("login")

# =========================================Cash_off salary ===========================================

def cash_off_salary(request):
    if request.user.is_authenticated:
        users_sales=Group.objects.get(name='sales').user_set.all()
        users = User.objects.filter(is_active=True).order_by('last_name')
        expense = Expense.objects.get(name="Зарплата")
        doc_type = DocumentType.objects.get(name="РКО (зарплата)")
        shops = Shop.objects.all()
        expenses = Expense.objects.all().exclude(name="Зарплата")
        if request.method == "POST":
            # identifier = Identifier.objects.create()
            if request.user in users_sales:
                session_shop=request.session['session_shop']
                shop=Shop.objects.get(id=session_shop)
            else:
                shop=request.POST['shop']
                shop=Shop.objects.get(id=shop)
            cash_receiver = request.POST["cash_receiver"]
            cash_receiver=User.objects.get(id=cash_receiver)
            sum = request.POST["sum"]
            sum = int(sum)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if post_check == True:
                # operations with cash
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                    if cash_remainder < sum:
                        messages.error(request,"В кассе недостаточно денежных средств")
                        return redirect("cash_off_salary" )
                else:
                    messages.error(request,"В кассе недостаточно денежных средств")
                    return redirect("cash_off_salary")
              
                document = Document.objects.create(
                    shop_sender=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                cho = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    cash_receiver=cash_receiver,
                    cash_off_reason=expense,
                    pre_remainder=cash_remainder,
                    cash_out=sum,
                    current_remainder=cash_remainder - sum,
                )
                if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created
                    ).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder + obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder=obj.current_remainder
                # end of operations with cash
                document.sum = sum
                document.save()
                # identifier.delete()
                if request.user in users_sales:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")
            else:
                document = Document.objects.create(
                    shop_sender=shop,
                    title=doc_type, 
                    user=request.user,
                    created=dateTime, 
                    posted=False
                )
                register = Register.objects.create(
                    document=document,
                    shop=shop,
                    sub_total=sum,
                    expense=expense,
                    cash_receiver=cash_receiver
                )
                document.sum=sum
                document.save()
                return redirect("log")
        else:
            context = {
                "shops": shops,
                'users': users
            }
            return render(request, "documents/cash_off_salary.html", context)
    else:
        auth.logout(request)
        return redirect ('login')

def change_cash_off_salary_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    document_dateTime=document.created 
    document_dateTime=document_dateTime.strftime('%Y-%m-%dT%H:%M')
    
    cho = Cash.objects.get(document=document)
    doc_type = DocumentType.objects.get(name="РКО (зарплата)")
   
    context = {
        "document": document, 
        "cho": cho, 
        'document_dateTime': document_dateTime,
        }
    return render(request, "documents/change_cash_off_salary_posted.html", context)

def change_cash_off_salary_unposted (request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        dateTime=document.created 
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        system_users=Group.objects.get(name='sales').user_set.all()
        shops = Shop.objects.all()
        shop=document.shop_sender
        expense = Expense.objects.get(name="Зарплата")
        register = Register.objects.get(document=document)
        users = User.objects.filter(is_active=True).order_by('last_name')
        if request.method == "POST":
            doc_type = DocumentType.objects.get(name="РКО (зарплата)")
            shop = request.POST["shop"]
            cash_receiver = request.POST["cash_receiver"]
            cash_receiver=User.objects.get(id=cash_receiver)
            shop = Shop.objects.get(id=shop)
            sum = request.POST["sum"]
            sum = int(sum)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
                # posting transfer document
            if post_check == True:
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                    if cash_remainder < sum:
                        messages.error(request,"В кассе недостаточно денежных средств")
                        return redirect("change_cash_off_salary_unposted", document.id)
                else:
                    messages.error(request,"В кассе недостаточно денежных средств",)
                    return redirect("change_cash_off_salary_unposted", document.id)
                    
                cho = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    cash_receiver=cash_receiver,
                    cash_off_reason=expense,
                    pre_remainder=cash_remainder,
                    cash_out=sum,
                    current_remainder=cash_remainder - sum,
                )
                if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                    cash_remainder=cho.current_remainder
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
                        obj.save()
                        cash_remainder = obj.current_remainder
                # end of operations with cash
                document.sum = sum
                document.shop_sender=shop
                document.created=dateTime
                document.posted=True
                document.save()
                register.delete()
                return redirect("log")
            else:
                register.sub_total=sum
                register.shop=shop
                register.cash_receiver=cash_receiver
                register.save()
                document.sum=sum
                document.shop_sender=shop
                document.created=dateTime
                document.save()
                return redirect("log")
        else:
            context = {
                "document": document,
                'dateTime': dateTime,
                "register": register,
                "shops": shops,
                'users': users,
            }
            return render(request, "documents/change_cash_off_salary_unposted.html", context)
    else:
        auth.logout(request)
        return redirect ('login')

def unpost_cash_off_salary (request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        users_sales=Group.objects.get(name="sales").user_set.all()
        document=Document.objects.get(id=document_id)
        shops = Shop.objects.all()
        cho = Cash.objects.get(document=document)
        register=Register.objects.create(
            shop=cho.shop,
            document=document,
            sub_total=document.sum,
            expense=cho.cash_off_reason,
            cash_receiver=cho.cash_receiver
        )
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            cho_latest_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created).latest('created')
            cash_remainder_before = cho_latest_before.current_remainder
        else:
            cash_remainder_before =0
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            cash_remainder=cash_remainder_before
            sequence_chos_after = Cash.objects.filter(shop=cho.shop, created__gt=cho.created).order_by('created')
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder
                obj.current_remainder = cash_remainder+ obj.cash_in - obj.cash_out
                obj.save()
                cash_remainder = obj.current_remainder
        cho.delete()
        document.posted=False
        document.save()
        return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")
  
#=====================================Cash_off expenses================================================
def cash_off_expenses(request):
    if request.user.is_authenticated:
        users=Group.objects.get(name='sales').user_set.all()
        shops = Shop.objects.all()
        expenses = Expense.objects.all().exclude(name="Зарплата")
        if request.method == "POST":
            if request.user in users:
                session_shop=request.session['session_shop']
                shop=Shop.objects.get(id=session_shop)
            else:
                shop=request.POST['shop']
                shop=Shop.objects.get(id=shop)
            doc_type = DocumentType.objects.get(name="РКО (хоз.расходы)")
            expense = request.POST["expense"]
            expense = Expense.objects.get(id=expense)
            sum = request.POST["sum"]
            sum = int(sum)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                    post_check = False
            if post_check == True:
                # operations with cash
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                    if cash_remainder < sum:
                        messages.error(request,"В кассе недостаточно денежных средств")
                        return redirect("cash_off_expenses")
                else:
                    messages.error(request,"В кассе недостаточно денежных средств",)
                    return redirect("cash_off_expenses")
                document = Document.objects.create(
                    shop_sender=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    sum=sum
                )
                cho = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    cash_off_reason=expense,
                    pre_remainder=cash_remainder,
                    cash_out=sum,
                    current_remainder=cash_remainder - sum,
                )
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder
                            + obj.cash_in 
                            - obj.cash_out
                        )
                        obj.save()
                        cash_remainder = obj.current_remainder
                    # end of operations with cash
                    document.sum = sum
                    document.save()
                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")        
            else:
                document = Document.objects.create(
                    shop_sender=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=False,
                    sum=sum
                )
                register = Register.objects.create(
                    document=document,
                    sub_total=sum,
                    expense=expense,
                )   
                return redirect("log")
        else:
            context = {
                "shops": shops, 
                "expenses": expenses
            }
            return render(request, "documents/cash_off_expenses.html", context)

    return redirect ('login')

def change_cash_off_expenses_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    expenses = Expense.objects.all().exclude(name="Зарплата")
    cho = Cash.objects.get(document=document)
    
    context = {
        "document": document, 
        "cho": cho,  
        "expenses": expenses,
        'dateTime': dateTime
        }
    return render(request, "documents/change_cash_off_expenses_posted.html", context)

def change_cash_off_expenses_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    users=Group.objects.get(name='sales').user_set.all()
    shops = Shop.objects.all()
    expenses = Expense.objects.all().exclude(name="Зарплата")
    register = Register.objects.get(document=document)
    if request.method == "POST":
        doc_type = DocumentType.objects.get(name="РКО (хоз.расходы)")
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        expense = request.POST ["expense"]
        expense = Expense.objects.get(id=expense)
        sum = request.POST["sum"]
        sum = int(sum)
        #=============DateTime change unposted module=====================
        dateTime = request.POST["dateTime"]
        # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
        dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
        current_dt=datetime.datetime.now()
        mics=current_dt.microsecond
        tdelta_1=datetime.timedelta(microseconds=mics)
        secs=current_dt.second
        tdelta_2=datetime.timedelta(seconds=secs)
        tdelta_3=tdelta_1+tdelta_2
        dateTime=dateTime+tdelta_3
        #===========End of DateTime change unposted module  
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
            # posting transfer document
        if post_check == True:
            # operations with cash
            if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                cash_remainder = cho_latest_before.current_remainder
                if cash_remainder < sum:
                    messages.error(request,"В кассе недостаточно денежных средств")
                    return redirect("cash_off_expenses")
            else:
                messages.error(request,"В кассе недостаточно денежных средств",)
                return redirect("cash_off_expenses")
            cho = Cash.objects.create(
                shop=shop,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                cash_off_reason=expense,
                pre_remainder=cash_remainder,
                cash_out=sum,
                current_remainder=cash_remainder - sum,
            )
            if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
                    obj.save()
                    cash_remainder = obj.current_remainder
            # end of operations with cash
            document.sum = sum
            document.created=dateTime
            document.shop_sender=shop
            document.posted=True
            document.save()
            register.delete()
            return redirect("log")
        else:
            register.sub_total=sum
            register.expense=expense
            register.save()
            document.sum=sum
            document.shop_sender=shop
            document.created=dateTime
            document.save()
            return redirect("log")
    else:
        context = {
            "document": document,
            'dateTime': dateTime,
            "register": register,
            "shops": shops,
            "expenses": expenses
        }
        return render(request, "documents/change_cash_off_expenses_unposted.html", context)

def unpost_cash_off_expenses (request, document_id):
    users=Group.objects.get(name="sales").user_set.all()
    document=Document.objects.get(id=document_id)
    shops = Shop.objects.all()
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        cho_latest_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created).latest('created')
        cash_remainder_before = cho_latest_before.current_remainder
    else:
        cash_remainder_before=0
    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        sequence_chos_after = Cash.objects.filter(shop=cho.shop, created__gt=cho.created).order_by('created')
        cash_remainder=cash_remainder_before
        for obj in sequence_chos_after:
            obj.pre_remainder = cash_remainder
            obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
            obj.save()
            cash_remainder = obj.current_remainder
    register=Register.objects.create(
        document=document,
        sub_total=cho.cash_out,
        expense=cho.cash_off_reason
    )
    cho.delete()
    document.posted=False
    document.save()
    return redirect ('log')

#===============================================================================================
def cash_receipt(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:   
        vouchers = Voucher.objects.all()
        contributors=Contributor.objects.all()
        shops = Shop.objects.all()
        users=Group.objects.get(name='sales').user_set.all()
        if request.method == "POST":
            doc_type = DocumentType.objects.get(name="ПКО")
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            voucher = request.POST["voucher"]
            voucher = Voucher.objects.get(id=voucher)
            contributor = request.POST["contributor"]
            contributor = Contributor.objects.get(id=contributor)
            sum = request.POST["sum"]
            sum = int(sum)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            # posting cash receipt document
            if post_check == True:
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                else:
                    cash_remainder=0
                document = Document.objects.create(
                    title=doc_type, 
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                cho = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    cash_contributor=contributor,
                    cash_in_reason=voucher,
                    pre_remainder=cash_remainder,
                    cash_in=sum,
                    current_remainder=cash_remainder + sum,
                )
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
                        obj.save()
                        cash_remainder = obj.current_remainder
                # end of operations with cash
                document.sum = sum
                document.save()
                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")
            else:
                document = Document.objects.create(
                    shop_receiver=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=False
                )
                register = Register.objects.create(
                    document=document,
                    sub_total=sum,
                    voucher=voucher,
                    contributor=contributor
                )
                document.sum=sum
                document.save()
                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")

        context = {
            "vouchers": vouchers,
            "contributors": contributors,
            "shops": shops,
        }
        return render(request, "documents/cash_receipt.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def change_cash_receipt_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    cho = Cash.objects.get(document=document)
    context = {
        "document": document,
        "cho": cho,
        'dateTime': dateTime
    }
    return render(request, "documents/change_cash_receipt_posted.html", context)

def change_cash_receipt_unposted (request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group: 
        document = Document.objects.get(id=document_id)
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        vouchers = Voucher.objects.all()
        contributors=Contributor.objects.all()
        shops = Shop.objects.all()
        register = Register.objects.get(document=document)
        if request.method == "POST":
            doc_type = DocumentType.objects.get(name="ПКО")
            shop = request.POST["shop"]
            shop = Shop.objects.get(id=shop)
            voucher = request.POST["voucher"]
            voucher = Voucher.objects.get(id=voucher)
            contributor = request.POST["contributor"]
            contributor = Contributor.objects.get(id=contributor)
            sum = request.POST["sum"]
            sum = int(sum)
            #=============DateTime change unposted module=====================
            dateTime = request.POST["dateTime"]
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
            #===========End of DateTime change unposted module
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
                # posting transfer document
            if post_check == True:
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                else:
                    cash_remainder=0
                cho = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    cash_contributor=contributor,
                    cash_in_reason=voucher,
                    pre_remainder=cash_remainder,
                    cash_in=sum,
                    current_remainder=cash_remainder + sum,
                )
                if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
                        obj.save()
                        cash_remainder = obj.current_remainder
                # end of operations with cash
                document.sum = sum
                document.created=dateTime
                document.shop_receiver=shop
                register.voucher=voucher
                register.contributor=contributor
                document.posted=True
                document.save()
                register.delete()
                return redirect("log")
            else:
                register.sub_total=sum
                register.voucher=voucher
                register.contributor=contributor
                register.save()
                document.sum = sum
                document.created=dateTime
                document.shop_receiver=shop
                document.save()
                return redirect("log")
        else:
            context = {
                "document": document,
                "register": register,
                "shops": shops,
                "vouchers": vouchers,
                "contributors": contributors,
                'dateTime': dateTime,
            }
            return render(request, "documents/change_cash_receipt_unposted.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def unpost_cash_receipt (request, document_id):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group: 
        document=Document.objects.get(id=document_id)
        cho = Cash.objects.get(document=document)
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            cho_latest_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created).latest('created')
            cash_remainder_before=cho_latest_before.current_remainder
        else:
            cash_remainder_before=0
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            sequence_chos_after = Cash.objects.filter(shop=cho.shop, created__gt=cho.created).order_by('created')
            cash_remainder=cash_remainder_before
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder
                obj.current_remainder = cash_remainder + obj.cash_in - obj.cash_out
                obj.save()
                cash_remainder = obj.current_remainder
        register=Register.objects.create(
            document=document,
            sub_total=document.sum,
            voucher=cho.cash_in_reason,
            contributor=cho.cash_contributor
        )
        cho.delete()
        document.posted=False
        document.save()
        return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")
    
#==========================================================================================================
def cash_movement(request):
    if request.user.is_authenticated:
        shops = Shop.objects.all()
        users=Group.objects.get(name='sales').user_set.all()
        doc_type = DocumentType.objects.get(name="Перемещение денег")
        if request.method == "POST":
            if request.user in users:
                session_shop=request.session['session_shop']
                shop_cash_sender=Shop.objects.get(id=session_shop)
                shop_cash_receiver=Shop.objects.get(name='ООС')
            else:
                shop_cash_sender = request.POST["shop_cash_sender"]
                shop_cash_sender = Shop.objects.get(id=shop_cash_sender)
                shop_cash_receiver = request.POST["shop_сash_receiver"]
                shop_cash_receiver = Shop.objects.get(id=shop_cash_receiver)
            sum = request.POST["sum"]
            sum = int(sum)
            #==============Time Module=========================================
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
                #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
                #==================End of time module================================
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                    post_check = False
            if post_check == True:
                # SHOP SENDER OPERATIONS
                # checking if cash remainder is enough to send the the sum indicated
                if Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                    if cash_remainder < sum:
                        messages.error(request,"В кассе недостаточно денежных средств")
                        return redirect("cash_off_expenses")
                else:
                    messages.error(request,"В кассе недостаточно денежных средств",)
                    return redirect("cash_movement")
                document = Document.objects.create(
                    title=doc_type,
                    shop_sender=shop_cash_sender,
                    shop_receiver=shop_cash_receiver,
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    sum=sum,
                )
                cho = Cash.objects.create(
                    shop=shop_cash_sender,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    pre_remainder=cash_remainder,
                    cash_out=sum,
                    current_remainder=cash_remainder - sum,
                    sender=True
                )
                if Cash.objects.filter(shop=shop_cash_sender, created__gt=cho.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop_cash_sender, created__gt=cho.created).order_by('created')
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder
                            + obj.cash_in 
                            - obj.cash_out
                            )
                        obj.save()
                        cash_remainder = obj.current_remainder

                #=============================Smsc API=======================
                #В сообщении нужно обязательно указать отправителя, иначе спам фильтр не пропустит его.
                phone='79519125000'
                message=f'ООО Ритейл. РКО {sum} руб. {shop_cash_sender}; {dateTime}; {request.user.last_name}'
                #base_url="https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={}&mes=OOO Ритейл. Ваш телефон готов."
                base_url="https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={}&mes={}"
                url=base_url.format(phone, message)
                api_request=requests.get(url)

                # SHOP RECEIVER OPERATIONS
                if Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).exists():
                    cho_latest_before = Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).latest('created')
                    cash_remainder = cho_latest_before.current_remainder
                else:
                    cash_remainder=0
                cho = Cash.objects.create(
                    shop=shop_cash_receiver,
                    created=dateTime,
                    document=document,
                    cho_type=doc_type,
                    user=request.user,
                    pre_remainder=cash_remainder,
                    cash_in=sum,
                    current_remainder=cash_remainder + sum,
                )
                if Cash.objects.filter(shop=shop_cash_receiver, created__gt=cho.created).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop_cash_receiver, created__gt=cho.created).order_by('created')
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    cash_remainder=cho.current_remainder
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder
                        obj.current_remainder = (
                            cash_remainder + obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder = obj.current_remainder
                document.sum = sum
                document.save()

                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")
            else:
                document = Document.objects.create(
                    title=doc_type,
                    shop_sender=shop_cash_sender,
                    shop_receiver=shop_cash_receiver,
                    user=request.user, 
                    created=dateTime,
                    posted=False,
                    sum=sum
                )

                if request.user in users:
                    return redirect ('sale_interface')
                else:
                    return redirect("log")

        else:
            context = {"shops": shops}
            return render(request, "documents/cash_movement.html", context)
    auth.logout(request)
    return redirect ('login')

def change_cash_movement_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    doc_type = DocumentType.objects.get(name="Перемещение денег")
    chos = Cash.objects.filter(document=document)
    context = {
        "document": document,
        'dateTime': dateTime,
    }
    return render(request, "documents/change_cash_movement_posted.html", context)

def change_cash_movement_unposted (request, document_id):
    users=Group.objects.get(name='sales').user_set.all()
    document = Document.objects.get(id=document_id)
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    doc_type = DocumentType.objects.get(name="Перемещение денег")
    shops = Shop.objects.all()
    if request.method == "POST":
        shop_cash_sender = request.POST["shop_cash_sender"]
        shop_cash_sender = Shop.objects.get(id=shop_cash_sender)
        shop_cash_receiver = request.POST["shop_cash_receiver"]
        shop_cash_receiver = Shop.objects.get(id=shop_cash_receiver)
        sum = request.POST["sum"]
        sum = int(sum)
        #=============DateTime change unposted module=====================
        dateTime = request.POST["dateTime"]
        # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00) 
        dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
        current_dt=datetime.datetime.now()
        mics=current_dt.microsecond
        tdelta_1=datetime.timedelta(microseconds=mics)
        secs=current_dt.second
        tdelta_2=datetime.timedelta(seconds=secs)
        tdelta_3=tdelta_1+tdelta_2
        dateTime=dateTime+tdelta_3
        #===========End of DateTime change unposted module
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
            # posting transfer document
        if post_check == True:
            #checking chos for shop_sender
            if Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).exists():
                cho_latest_before = Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).latest('created')
                pre_remainder = cho_latest_before.current_remainder
                if pre_remainder < sum:
                    messages.error(request,"В кассе недостаточно денежных средств",)
                    return redirect("change_cash_movement_unposted")
            else:
                messages.error(request,"В кассе недостаточно денежных средств",)
                return redirect("change_cash_movement_unposted")
            cho = Cash.objects.create(
                shop=shop_cash_sender,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                pre_remainder=pre_remainder,
                cash_out=sum,
                current_remainder=pre_remainder - sum,
                sender=True
            )
            if Cash.objects.filter(shop=shop_cash_sender, created__gt=cho.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop_cash_sender, created__gt=cho.created).order_by('created')
                pre_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = pre_remainder
                    obj.current_remainder = (
                        pre_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    pre_remainder = obj.current_remainder
            # SHOP RECEIVER OPERATIONS
            if Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).exists():
                cho_latest_before = Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).latest('created')
                cash_remainder = cho_latest_before.current_remainder
            else:
                cash_remainder=0
            cho = Cash.objects.create(
                shop=shop_cash_receiver,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                pre_remainder=cash_remainder,
                cash_in=sum,
                current_remainder=cash_remainder + sum,
            )
            if Cash.objects.filter(shop=shop_cash_receiver, created__gt=cho.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop_cash_receiver, created__gt=cho.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
            document.posted=True
            document.created=dateTime
            document.shop_sender=shop_cash_sender     
            document.shop_receiver=shop_cash_receiver    
            document.sum = sum
            document.save()
            if request.user in users:
                return redirect ('sale_interface')
            else:
                return redirect("log")
        else:
            document.shop_receiver=shop_cash_sender
            document.shop_receiver=shop_cash_receiver
            document.created=dateTime
            document.sum=sum
            document.save()
            return redirect("log")
    else:
        context = {
            'document': document,
            'shops': shops,
            'dateTime': dateTime,
        }
        return render (request, 'documents/change_cash_movement_unposted.html', context)

def unpost_cash_movement (request, document_id):
    users=Group.objects.get(name="sales").user_set.all()
    document=Document.objects.get(id=document_id)
    chos = Cash.objects.filter(document=document)
    for cho in chos:
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            cho_latest_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created).latest('created')
            cash_remainder=cho_latest_before.current_remainder
        else:
            cash_remainder=0
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            sequence_chos_after=Cash.objects.filter(shop=cho.shop, created__gt=cho.created).order_by('created')
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder
                obj.current_remainder = (
                    cash_remainder
                    + obj.cash_in
                    - obj.cash_out
                )
                obj.save()
                cash_remainder = obj.current_remainder
        cho.delete()
    document.posted=False
    document.save() 
    return redirect ('log')

# ========================================End of cash_off operations ============================
def identifier_inventory(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("inventory", identifier.id)
    else:
        return redirect("login")

def inventory(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)
       #==============Time Module=========================================
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
            #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
            #==================End of time module================================

        products=Product.objects.filter(category=category)
        for obj in products:
            if RemainderHistory.objects.filter(imei=obj.imei, shop=shop, created__lt=dateTime).exists():
                sequence_rhos_before = RemainderHistory.objects.filter(imei=obj.imei, shop=shop, created__lt=dateTime)
                remainder_history = sequence_rhos_before.latest("created")
                if remainder_history.current_remainder>0:
                    register=Register.objects.create(
                        identifier=identifier,
                        shop=shop,
                        name=remainder_history.name,
                        imei=remainder_history.imei,
                        quantity=remainder_history.current_remainder,
                        price=remainder_history.retail_price,
                        real_quantity=0,
                        reevaluation_price=remainder_history.retail_price,
                    )
      
        return redirect("inventory_list", identifier.id)

    else:
        context = {
            "shops": shops,
            "categories": categories,
            "identifier": identifier,
            }
        return render(request, "documents/inventory.html", context)

def inventory_list (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
   
    registers=Register.objects.filter(identifier=identifier).order_by("name")
    last_updated=registers.latest('updated')
    counter=1
    for i in registers:
        i.number=counter
        counter=counter + 1
        i.save()
    context = {
        'last_updated': last_updated,
        'registers': registers,
        'identifier': identifier,
        'categories': categories,
    }
    return render (request, 'documents/inventory_list.html', context)

def check_inventory (request, identifier_id):
    tdelta=datetime.timedelta(hours=3)
    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
    dateTime=dT_utcnow+tdelta
    identifier=Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    shop=registers.first().shop
    if request.method == "POST":
        check_imei = request.POST["check_imei"]
        real_qnty = request.POST["real_qnty_hidden_to_post"]
        if '/' in check_imei:
            check_imei=check_imei.replace('/', '_')
        # imeis_hidden = request.POST.getlist("imei_hidden", None)
        # real_qnts_hidden = request.POST.getlist("real_qnt_hidden", None)
        # reevaluation_prices_hidden=request.POST.getlist("reevaluation_price_hidden", None)
        if registers.filter(imei=check_imei).exists():
            final_qnty= int(real_qnty) + 1
            register=registers.get(imei=check_imei)
            register.updated=dateTime
            register.real_quantity=final_qnty
            register.save()
        else:
            if Product.objects.filter(imei=check_imei).exists():
                product=Product.objects.get(imei=check_imei)
                register = Register.objects.create(
                    identifier=identifier,
                    updated=dateTime,
                    shop=shop,
                    imei=product.imei, 
                    name=product.name,
                    quantity=0,
                    real_quantity=1,
                    #new=True
                )
              
            else:
                messages.error(request, "Данное наименование отсутствует в БД. Введите его, а затем повторите операцию.")
        return redirect ('inventory_list', identifier.id)
        
def check_inventory_unposted (request, document_id):
    tdelta=datetime.timedelta(hours=3)
    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
    dateTime=dT_utcnow+tdelta
    document=Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    shop=registers.first().shop
    if request.method == "POST":
        check_imei = request.POST["check_imei"]
        real_qnty = request.POST["real_qnty_hidden_to_post"]
        if '/' in check_imei:
            check_imei=check_imei.replace('/', '_')
        # imeis_hidden = request.POST.getlist("imei_hidden", None)
        # real_qnts_hidden = request.POST.getlist("real_qnt_hidden", None)
        # reevaluation_prices_hidden=request.POST.getlist("reevaluation_price_hidden", None)
        if registers.filter(imei=check_imei).exists():
            final_qnty= int(real_qnty) + 1
            register=registers.get(imei=check_imei)
            register.updated=dateTime
            register.real_quantity=final_qnty
            register.save()
        elif Product.objects.filter(imei=check_imei).exists():
            product=Product.objects.get(imei=check_imei)
            register = Register.objects.create(
                document=document,
                updated=dateTime,
                shop=shop,
                imei=product.imei, 
                name=product.name,
                quantity=0,
                real_quantity=1,
                #new=True
            )
                    
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его, а затем повторите операцию.")
            return redirect("change_inventory_unposted", document.id)
        return redirect("change_inventory_unposted", document.id)

def enter_new_product_inventory(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)

        if Product.objects.filter(imei=imei).exists():
            messages.error(request,"Наименование в базу данных не введено, так как IMEI не является уникальным")
            return redirect("inventory_list", identifier.id)
        else:
            product = Product.objects.create(
                name=name,
                imei=imei,
                category=category,
            )
            return redirect("inventory_list", identifier.id)  

def enter_new_product_inventory_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)

        if Product.objects.filter(imei=imei).exists():
            messages.error(request,"Наименование в базу данных не введено, так как IMEI не является уникальным")
            return redirect("change_inventory_unposted", document.id)
        else:
            product = Product.objects.create(
                name=name,
                imei=imei,
                category=category,
            )
            return redirect("change_inventory_unposted", document.id)   

def inventory_input (request, identifier_id):
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        doc_type=DocumentType.objects.get(name='Инвентаризация ТМЦ')
        doc_type_1=DocumentType.objects.get(name='Списание ТМЦ')
        doc_type_2=DocumentType.objects.get(name='Оприходование ТМЦ')
        registers=Register.objects.filter(identifier=identifier).order_by("name")
        shop = registers.first().shop
        #dateTime = registers.first().created
        tdelta=datetime.timedelta(hours=3)
        dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
        dateTime=dT_utcnow+tdelta
        #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
        #==================End of time module================================
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            real_qnts = request.POST.getlist("real_qnt", None)
            prices=request.POST.getlist('price', None)
            reevaluation_prices=request.POST.getlist('reevaluation_price', None)
            # if dateTime:
            #     # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            #     dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            # else:
            #     dateTime = datetime.now()
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            if post_check == True:
                #creates inventory document
                document = Document.objects.create(
                    title=doc_type,
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                #creates sign off document
                document_sign_off = Document.objects.create(
                    title=doc_type_1, 
                    base_doc=document.id,
                    shop_sender=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                #creates recognition document
                document_recognition = Document.objects.create(
                    title=doc_type_2, 
                    base_doc=document.id,
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                document_sum=0
                document_sum_1=0
                document_sum_2=0
                n=len(names)
                for i in range(n):
                    product=Product.objects.get(imei=imeis[i])
                    if quantities[i]>real_qnts[i]:
                        # checking docs before remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                            remainder_history = sequence_rhos_before.latest("created")
                            remainder_current = remainder_history.current_remainder
                        else:
                            remainder_current=0
                        new_rho = RemainderHistory.objects.create(
                            document=document_sign_off,
                            created=dateTime,
                            shop=shop,
                            rho_type=doc_type_1,
                            inventory_doc=document_sign_off,
                            #rho_type=document.title,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            pre_remainder=remainder_current,
                            incoming_quantity=0,
                            outgoing_quantity=int(quantities[i])-int(real_qnts[i]),
                            current_remainder=real_qnts[i],
                            retail_price=reevaluation_prices[i],
                            #wholesale_price=int(prices[i]),
                            #sub_total= int(quantities[i]) * int(prices[i]),
                            sub_total=(int(quantities[i])-int(real_qnts[i])) * int(reevaluation_prices[i]),
                        )
                        document_sum_1+=new_rho.sub_total 
                       
                        #remainder_current.total_av_price=remainder_current.current_remainder*remainder_current.av_price
                        #document_sum=remainder_history.sub_total
                    elif quantities[i]<real_qnts[i]:
                        # checking docs before remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                            remainder_history = sequence_rhos_before.latest("created")
                            remainder_current = remainder_history.current_remainder
                            retail_price=remainder_history.retail_price
                        else:
                            remainder_current=0
                        new_rho = RemainderHistory.objects.create(
                            document=document_recognition,
                            created=dateTime,
                            shop=shop,
                            rho_type=doc_type_2,
                            inventory_doc=document_recognition,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            pre_remainder=remainder_current,
                            incoming_quantity=int(real_qnts[i])-int(quantities[i]),
                            outgoing_quantity=0,
                            current_remainder=real_qnts[i],
                            retail_price=reevaluation_prices[i],
                            #wholesale_price=int(prices[i]),
                            #sub_total= int(quantities[i]) * int(prices[i]),
                            sub_total=(int(real_qnts[i])-int(quantities[i])) * int(reevaluation_prices[i]),
                        )
                        document_sum_2+=new_rho.sub_total 

                    inventory_item=InventoryList.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        imei=imeis[i],
                        name=names[i],
                        quantity=quantities[i],
                        real_quantity=real_qnts[i],
                        price=prices[i],
                        reevaluation_price=reevaluation_prices[i],
                        sub_total=int(real_qnts[i])*int(reevaluation_prices[i])
                    )
                    document_sum+=inventory_item.sub_total 
                    
                document_sign_off.sum=document_sum_1
                document_sign_off.save()
                document_recognition.sum=document_sum_2
                document_recognition.save()
                document.sum=document_sum
                document.save()
                for register in registers:
                    register.delete()
                identifier.delete()           
                return redirect ('log')
            else:
                #creates inventory document
                document = Document.objects.create(
                    title=doc_type,
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=False
                )
                document_sum=0
                n = len(names)
                #document_sum = 0
                for i in range(n):
                    register = Register.objects.get(identifier=identifier, imei=imeis[i])
                    register.document=document
                    register.shop=shop
                    register.new=False
                    register.name=names[i]
                    register.imei=imeis[i]
                    register.quantity=quantities[i]
                    register.real_quantity=real_qnts[i]
                    register.price=prices[i]
                    register.reevaluation_price=reevaluation_prices[i]
                    register.sub_total=int(real_qnts[i])*int(reevaluation_prices[i])
                    register.save()
                    document_sum+=register.sub_total
                document.sum=document_sum
                document.save()
                #we can't delete identifier at this moment since register still has links to it
                #identifier.delete()
                return redirect ('log')
    else:
        auth.logout(request)
        return redirect ('login')
        
def change_inventory_unposted(request, document_id):
    if request.user.is_authenticated:
        tdelta=datetime.timedelta(hours=3)
        dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
        dateTime=dT_utcnow+tdelta
        #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
        #==================End of time module================================
        categories=ProductCategory.objects.all()
        document = Document.objects.get(id=document_id)
        doc_type_1=DocumentType.objects.get(name='Списание ТМЦ')
        doc_type_2=DocumentType.objects.get(name='Оприходование ТМЦ')
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("name")
        last_updated=registers.latest('updated')
        #shop = registers.first().shop
        shop = document.shop_receiver
        identifier=registers.first().identifier
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
        if request.method == "POST":
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            real_qnts = request.POST.getlist("real_qnt", None)
            prices = request.POST.getlist("price", None)
            reevaluation_prices=request.POST.getlist("reevaluation_price", None)
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            # posting the document
            if post_check == True:
                document_sum=0
                document_sum_1=0
                document_sum_2=0
                document.posted=True
                document.created=dateTime
                document.save()
                #creates sign off document
                document_sign_off = Document.objects.create(
                    title=doc_type_1, 
                    base_doc=document.id,
                    shop_sender=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                #creates recognition document
                document_recognition = Document.objects.create(
                    title=doc_type_2, 
                    base_doc=document.id,
                    shop_receiver=shop,
                    user=request.user, 
                    created=dateTime,
                    posted=True
                )
                n = len(names)
                for i in range(n):
                    product=Product.objects.get(imei=imeis[i])
                    if quantities[i]>real_qnts[i]:
                        # checking docs before remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                            remainder_history = sequence_rhos_before.latest("created")
                            remainder_current = remainder_history.current_remainder
                        else:
                            remainder_current=0
                        new_rho = RemainderHistory.objects.create(
                            document=document_sign_off,
                            created=dateTime,
                            shop=shop,
                            rho_type=doc_type_1,
                            inventory_doc=document_sign_off,
                            #rho_type=document.title,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            pre_remainder=remainder_current,
                            incoming_quantity=0,
                            outgoing_quantity=int(quantities[i])-int(real_qnts[i]),
                            current_remainder=real_qnts[i],
                            retail_price=reevaluation_prices[i],
                            #wholesale_price=int(prices[i]),
                            #sub_total= int(quantities[i]) * int(prices[i]),
                            sub_total=(int(quantities[i])-int(real_qnts[i])) * int(reevaluation_prices[i]),
                        )
                        document_sum_1+=new_rho.sub_total 
                        
                        #remainder_current.total_av_price=remainder_current.current_remainder*remainder_current.av_price
                        #document_sum=remainder_history.sub_total
                    elif quantities[i]<real_qnts[i]:
                        # checking docs before remainder_history
                        if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                            sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                            remainder_history = sequence_rhos_before.latest("created")
                            remainder_current = remainder_history.current_remainder
                            retail_price=remainder_history.retail_price
                        else:
                            remainder_current=0
                        new_rho = RemainderHistory.objects.create(
                            document=document_recognition,
                            created=dateTime,
                            shop=shop,
                            rho_type=doc_type_2,
                            inventory_doc=document_recognition,
                            category=product.category,
                            imei=imeis[i],
                            name=names[i],
                            pre_remainder=remainder_current,
                            incoming_quantity=int(real_qnts[i])-int(quantities[i]),
                            outgoing_quantity=0,
                            current_remainder=real_qnts[i],
                            retail_price=reevaluation_prices[i],
                            #wholesale_price=int(prices[i]),
                            #sub_total= int(quantities[i]) * int(prices[i]),
                            sub_total=(int(real_qnts[i])-int(quantities[i])) * int(reevaluation_prices[i]),
                        )
                        document_sum_2+=new_rho.sub_total 
            
                    inventory_item=InventoryList.objects.create(
                        document=document,
                        created=dateTime,
                        shop=document.shop_receiver,
                        imei=imeis[i],
                        name=names[i],
                        quantity=quantities[i],
                        real_quantity=real_qnts[i],
                        price=prices[i],
                        reevaluation_price=reevaluation_prices[i],
                        sub_total=int(real_qnts[i])*int(reevaluation_prices[i])
                    )
                    document_sum+=inventory_item.sub_total

                document_sign_off.sum=document_sum_1
                document_sign_off.save()
                document_recognition.sum=document_sum_2
                document_recognition.save()
                document.sum=document_sum
                document.save()

                for register in registers:
                    register.delete()
                identifier.delete()           
                return redirect ('log')
            # else:
                #     messages.error(request, "Вы не ввели ни одного наименования.")
                #     return redirect("change_inventory_unposted", document.id)
            else:
                if imeis:
                    n = len(names)
                    document_sum = 0
                    for i in range(n):
                        register=Register.objects.get(document=document, imei=imeis[i])
                        #register.document=document
                        #register.shop=shop
                        register.name=names[i]
                        register.imei=imeis[i]
                        register.quantity=quantities[i]
                        register.real_quantity=real_qnts[i]
                        register.price=prices[i]
                        register.reevaluation_price=reevaluation_prices[i]
                        register.sub_total=int(real_qnts[i])*int(reevaluation_prices[i])
                        #register.new=False
                        register.save()
                        document_sum+=register.sub_total
                        #register.new = False
                        #document_sum += int(register.sub_total)
                        if Register.objects.filter(document=document, deleted=True).exists():
                            registers=Register.objects.filter(document=document, deleted=True)
                            for register in registers:
                                register.delete()
                    document.sum=document_sum
                    document.save()
                    return redirect("log")
                else:
                    messages.error(request, "Вы не ввели ни одного наименования.")
                    return redirect("change_inventory_unposted", document.id)
        else:
            context = {
                "last_updated": last_updated,
                "registers": registers,
                "shop": shop,
                "document": document,
                'categories': categories,
            }
            return render(request, "documents/change_inventory_unposted.html", context)
    else:
        auth.logout(request)
        return redirect ('login')

def change_inventory_posted(request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        inventory_list=InventoryList.objects.filter(document=document)
        shop=inventory_list.first().shop
        numbers = inventory_list.count()
        for item, i in zip(inventory_list, range(numbers)):
            item.number = i + 1
            item.save()
        context = {
            'inventory_list': inventory_list,
            'document': document,
            'shop': shop,
            'numbers': numbers,
        }
        return render (request, 'documents/change_inventory_posted.html', context)
    else:
        auth.logout(request)
        return redirect ('login')

def unpost_inventory(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document)
    for rho in rhos:
        #av_price = AvPrice.objects.get(imei=rho.imei)
        #av_price.current_remainder -= rho.incoming_quantity
        #av_price.sum -= rho.incoming_quantity * av_price.av_price
        # av_price.av_price=av_price.sum/av_price.current_remainder
        #av_price.save()
        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created).exists():
            sequence_rhos_before = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__lt=rho.created)
            rho_latest_before = sequence_rhos_before.latest("created")
            remainder_current = RemainderCurrent.objects.get(shop=rho.shop, imei=rho.imei)
            remainder_current.current_remainder = rho_latest_before.current_remainder
            # remainder_current.total_av_price=rho_latest_before.sub_total
            # remainder_current.av_price=rho_latest_before.av_price
            remainder_current.save()
        else:
            remainder_current = RemainderCurrent.objects.get(shop=rho.shop, imei=rho.imei)
            remainder_current.current_remainder = 0
            # remainder_current.total_av_price=0
            # remainder_current.av_price=0
            remainder_current.save()

        if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
            sequence_rhos_after = RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, created__gt=rho.created)
            sequence_rhos_after = sequence_rhos_after.all().order_by("created")
            for obj in sequence_rhos_after:
                obj.pre_remainder = remainder_current.current_remainder
                obj.current_remainder = (
                    remainder_current.current_remainder
                    + obj.incoming_quantity
                    - obj.outgoing_quantity
                )
                obj.save()
                remainder_current.current_remainder = obj.current_remainder
                remainder_current.save()
        rho.delete()
    docs=Document.objects.filter(base_doc=document.id)
    for doc in docs:
        doc.delete()
    document.posted = False
    document.save()
    return redirect("log")

#===========================================================================
class GeneratePDF(View):
    # def get(self, request, *args, **kwargs):
    def get(self, request, document_id):
        document=Document.objects.get(id=document_id)
        registers=Register.objects.filter(document=document)
        
        data = {
            'registers': registers
        }
        if request.user.is_authenticated:
            if Group.objects.filter(name='entities').exists():
                group=Group.objects.get(name='entities').user_set.all()
                if request.user in group:
                    pdf = render_to_pdf('pdf_invoice_entity.html', data)
                    return HttpResponse(pdf, content_type='application/pdf')
                else:
                    pdf = render_to_pdf('pdf_invoice.html', data)
                    return HttpResponse(pdf, content_type='application/pdf')
            else:
                pdf = render_to_pdf('pdf_invoice.html', data)
                return HttpResponse(pdf, content_type='application/pdf')
        else:
            pdf = render_to_pdf('pdf_invoice.html', data)
            return HttpResponse(pdf, content_type='application/pdf')

class DownloadPDF(View):
    # def get(self, request, *args, **kwargs):
    def get(self, request, document_id):
        document=Document.objects.get(id=document_id)
        rhos=RemainderHistory.objects.filter(document=document, status = True)
        total_sum=0
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
            total_sum+=rho.sub_total
        rhos=RemainderHistory.objects.filter(document=document, status = True) 
        # invoice = OrderItem.objects.filter(order=pk)
        # order = Order.objects.get(id=pk)
        # new_total = 0.00
        # counter = 0
        # for item in invoice:
        #     line_total = float(item.price)*item.quantity
        #     new_total += line_total
        #     counter += item.quantity
        data = {
            'rhos': rhos,
            'document': document,
            'total_sum': total_sum,
        }
        pdf = render_to_pdf('pdf_transfer.html', data)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Transfer_%s.pdf" % (document_id)
        content = "attachment; filename='%s'" % (filename)
        response['Content-Disposition'] = content
        return response


def trade_in(request, identifier_id):
    if request.user.is_athenticated:
        if request.method == "POST":
           #  = request.POST["shop"]


            pass

    else:
        return redirect ('login')

# def email(request):
#     send_mail(
#         'Hello from DjangoDev',
#         'Here goes email text',
#         '79200711112@yandex.ru',
#         ['Sergei_Vinokurov@rambler.ru'],
#         fail_silently=False
#     )

#     return render(request, 'email/email.html')

def teko_pay (request):
    if request.user.is_authenticated:
        teko_payments=Teko_pay.objects.all()
        shops=Shop.objects.all()
        users_sales=Group.objects.get(name="sales").user_set.all()
        users_admin=Group.objects.get(name="admin").user_set.all()
        if request.method == "POST":
            dateTime=request.POST.get('dateTime', False)
            if dateTime:
                # converting dateTime in str format (2021-07-08T01:05) to django format ()
                dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
                current_dt=datetime.datetime.now()
                mics=current_dt.microsecond
                tdelta_1=datetime.timedelta(microseconds=mics)
                secs=current_dt.second
                tdelta_2=datetime.timedelta(seconds=secs)
                tdelta_3=tdelta_1+tdelta_2
                dateTime=dateTime+tdelta_3
            else:
                tdelta=datetime.timedelta(hours=3)
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                dateTime=dT_utcnow+tdelta
            if request.user in users_sales:
                session_shop=request.session['session_shop']
                shop=Shop.objects.get(id=session_shop)
                phone_number=request.POST.get('phone_number', False)
            else:
                shop=request.POST['shop']
                shop=Shop.objects.get(id=shop)
            sum = request.POST["sum"]
            sum = int(sum)

            if shop.cash_register == False:#if shop is equipped with erms cash register
                dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
                #dateTime=dT_utcnow+tdelta
                # print(shop.shift_status_updated)
                # print(dT_utcnow)
                # a = dT_utcnow - shop.shift_status_updated
                # print(a)
                if shop.shift_status == False and (dT_utcnow - shop.shift_status_updated).total_seconds()/3600 > 12: #if shift is open for more than 12 hours
                    print ('Смена открыта более 12 часов')
                    messages.error(request, "Смена окрыта более 12 часов. Сначала закройте смену.")
                    return redirect ('sale_interface')
                
                #teko_cash=float(cho.cash_in)#converts integer number to float number
                teko_cash=round(float(sum), 2)#converts integer number to float number
                phone_number='Платеж на ' + phone_number
                #retail_price=retail_price+'.00'#adds two zeros to the string
                #print('Смена открыта менее 12 часов')

                auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                uuid_number=uuid.uuid4()#creatring a unique identification number

                task = {
                    "uuid": str(uuid_number),
                    "request": [{
            

                    "type": "sell",
                    "items": [ 
                        {
                        "type": "position",
                        "name": phone_number,
                        "price": teko_cash,
                        "quantity": 1.0,
                        "amount": teko_cash,
                        "tax": {
                            "type": "vat0"
                        }
                        },
                    ],

                    "payments":[{
                            "type": "cash",
                            "sum": teko_cash
                        }]
                }]}
                try:
                    response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)
                
                    #status_code=response.status_code
                    # print(status_code)
                    # text=response.text
                    # print(text)
                    # url=response.url
                    # json=response.json()
                    if shop.shift_status == True:
                        shop.shift_status = False
                        shop.save()
                except:
                    messages.error(request, "Платеж не проведен. Сообщите администратору.")
                    return redirect ('sale_interface')
                #=================End of Cash Register Module==============
                
            doc_type = DocumentType.objects.get(name="Платежи Теко")
            document = Document.objects.create(
                created=dateTime,
                shop_sender=shop,
                title=doc_type,
                user=request.user,
                posted=True,
                sum=sum,
            )
            if Cash.objects.filter(shop=shop, created__lt=document.created).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=document.created).latest('created')
                cash_remainder = cho_latest_before.current_remainder
            else:
                cash_remainder = 0

            cho = Cash.objects.create(
                shop=shop,
                cho_type=doc_type,
                created=document.created,
                document=document,
                user=request.user,
                pre_remainder=cash_remainder,
                cash_in=sum,
                current_remainder=cash_remainder + sum,
            )

            if Cash.objects.filter(shop=shop, created__gt=document.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created).order_by('created')
                cash_remainder=cho.current_remainder
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
        
            if request.user in users_sales:
                return redirect ('sale_interface')
            else:
                return redirect ('log') 
        else:
            if request.user in users_sales:
                session_shop=request.session['session_shop']
                session_shop=Shop.objects.get(id=session_shop)
                context = {
                    "teko_payments": teko_payments,
                    "shops": shops,
                    "session_shop": session_shop,
                }
                return render(request, 'documents/teko_pay.html', context)

            else:
                context = {
                    "teko_payments": teko_payments,
                    "shops": shops,
                }
                return render(request, 'documents/teko_pay.html', context)
    else:
        auth.logout(request)
        return redirect("login")
    
def change_teko_pay_posted (request, document_id):
    if request.user.is_authenticated:
        document = Document.objects.get(id=document_id)
        cho=Cash.objects.get(document=document)
        shop=cho.shop
        document_datetime=document.created
        document_datetime=document_datetime.strftime('%Y-%m-%dT%H:%M')
        if request.method == "POST":
            #checking chos before
            if Cash.objects.filter(shop=shop, created__lt=cho.created).exists():
                cho_latest_before = Cash.objects.filter(shop=shop, created__lt=cho.created).latest('created')  
                cash_remainder=cho_latest_before.current_remainder
            else:
                cash_remainder = 0 
            #checking chos after
            if Cash.objects.filter(shop=shop, created__gt=cho.created).exists():
                cash_remainder=cash_remainder
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created).order_by('created')
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder
                    obj.current_remainder = (
                        cash_remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder = obj.current_remainder
            cho.delete()
            document.delete()
            return redirect ('log')
        else:
            context = {
                'cho': cho,
                'document': document,
                'document_datetime':document_datetime,
                }
            return render(request, 'documents/change_teko_pay_posted.html', context)

    else:
        return redirect ('login')

#======================Marketplaces==========================================
def ozon_product_create(request):
    if request.user.is_authenticated:
        #categories = ProductCategory.objects.all()
        category = ProductCategory.objects.get(name='Аксы')
        if request.method == "POST":
            file = request.FILES["file_name"]
            # print(file)
            # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            n=0
            #В названии обязательно должно быть слово Чехол или стекло
            for i in range(cycle):
                n += 1
                row = df1.iloc[i]#reads each row of the df1 one by one
                imei=row.Imei
                if '/' in str(imei):
                    imei=imei.replace('/', '_')
                if Product.objects.filter(imei=imei).exists():
                    product=Product.objects.get(imei=imei)
                    if product.for_mp_sale is False:
                        product.for_mp_sale = True
                    if product.EAN is None and product.category == category:
                        product.EAN = product.imei
                    product.save() 
                else:
                    product = Product.objects.create(
                        name=row.Title,
                        imei=imei, 
                        category=category,
                        for_mp_sale=True,              
                    )
                    if product.category == category:
                        product.EAN=imei
                        product.save()
                #==========Ozon import module==========================
                #Озон воспринимает товар как уже существующий, если у него совпадают обязательные аттрибуты.
                #Достаточно изменить один их них, чтобы Озон создал новый товар

                #если значение aттрибута 'dictionary_value_id' больше нуля, нужно открывать данный аттрибут через
                #https://api-seller.ozon.ru/v1/description-category/attribute/values и смотреть идентификационный номер
                #и текстовое значение нужные нам. И их указыать в соответствующем аттрибуте

                #Сначала мы создаём новый товар на площадке Ozon посредством метода: 
                #response=requests.post('https://api-seller.ozon.ru/v3/product/import', json=task, headers=headers)
                #В процессе содания нового товара Ozon присваивает ему уникальный Ozon_id, но не изменяет кол-во товара на стоке Ozon
                #Изменение в кол-во товара на стоке Оzon вносятся позднее при проведении Автоматического поступления

                #Далее получаем ozon_id посредством метода:
                #response=requests.post('https://api-seller.ozon.ru/v2/product/list', json=task_2, headers=headers)
                #и сохраняем в модели Product

                #Ozon_id и offer_id нужны для дальнейшего редактирования количества товара на стоке озон посредством метода:
                #response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task_3, headers=headers)
                #offer_id это номер товара уникальный в erms. 
                #В качестве offer_id для аксов мы используем imei. Можно использовать EAN товара. Это удобно в случае с аксами,
                #но при работе со смартфонами EAN не всегда известен. IMEI использовать не получится, так как один SKU может иметь разные IMEI.

                #я пытался создать товар и задать ему количество в одной функции, но Озону нужно время для того, чтобы проверить,
                #что я создал у него на площадке, и он возвращает нужныйм нам ozon_id только через какое-то время, а не сразу
                #поэтому я разделил эти две функции. Сначала мы создаем товар (def ozon_product_create), а затем уже задаем нужное
                #количество (def delivery_auto)

                #checking if product already has Ozon_id & does not have to be created again
                if product.ozon_id is None:
                    headers = {
                        "Client-Id": "867100",
                        "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                    }
                    if 'Чехол' in row.Title:
                        key_word_var_1 =str(row.Model)
                        key_word_var_2 =str(row.Model_short)
                        key_word_var_3 =str(row.Brand)
                        key_word=  f"""чехол на; чехол с экраном; чехол на {key_word_var_3}; чехол для {key_word_var_3}; чехол; чехол-книжка; 
    чехол книжка; чехол для смартфона; {key_word_var_1}; {key_word_var_2}; чехол с магнитом; чехол с картой; 
    чехол на смартфон; чехол на телефон {key_word_var_3}; чехол для телефона {key_word_var_3}; чехол телефон {key_word_var_3}; магнитный чехол; чехол {key_word_var_3}; 
    противоударный чехол; кармашек для карт на чехол; чехол с отделением для карты; для телефона чехол; чехол защитный; 
    книжка чехол для телефона; чехол на телефона; чехол с магнитом на телефон"""
                        description_string = f"""Ищете идеальный аксессуар для вашего смартфона? Защитный чехол для {key_word_var_1} – это именно то, что вам нужно! Этот противоударный чехол обеспечивает надежную защиту от падений и ударов, сохраняя ваш телефон в идеальном состоянии. Изготовленный из качественных материалов, он гарантирует долговечность и стильный внешний вид.

    Чехол идеально подходит для активных пользователей, которые ценят безопасность своих устройств. Благодаря продуманному дизайну, он обеспечивает полный доступ ко всем портам и кнопкам, позволяя легко подключать зарядные устройства, наушники и другие аксессуары. Внутренний слой имеет специальное покрытие, которое защищает ваш смартфон от царапин и загрязнений.

    Этот аксессуар не только защитит ваш телефон, но и добавит ему стильный акцент. Чехол доступен в нескольких цветах, что позволяет выбрать вариант, который лучше всего подходит вашему стилю. Он идеально сочетается с другими гаджетами, такими как планшеты, ноутбуки и даже автомобильные устройства.

    Не забывайте, что правильная защита вашего устройства – это не только вопрос стиля, но и функциональности. Чехол для Samsung Galaxy A15 поддерживает работу с беспроводными зарядными устройствами, что делает его еще более удобным в использовании. Вы можете спокойно заряжать свой смартфон, не снимая защиту.

    Если вы ищете универсальный чехол, который подойдет не только для Samsung, но и для других брендов, таких как Xiaomi, Realme и Huawei, этот продукт станет отличным выбором. Он совместим с различными устройствами, включая игровые консоли и аксессуары для видеонаблюдения.

    Не упустите возможность защитить ваш смартфон с помощью качественного чехла. Заказывайте сейчас и наслаждайтесь безопасностью и стилем в одном флаконе! Этот защитный аксессуар станет вашим надежным спутником в повседневной жизни, будь то на работе, дома или в поездках. Убедитесь, что ваш телефон всегда под надежной защитой, выбирая только лучшее!"""
                        if 'белый' in row.Title:
                            colour='белый'
                            colour_id = '51571'
                        elif 'черный' in row.Title:
                            colour='черный'
                            colour_id = '61574'
                        elif 'коричневый' in row.Title:
                            colour='коричневый'
                            colour_id = '61575'
                        elif 'розовый' in row.Title:
                            colour='розовый'
                            colour_id = '61580'
                        elif 'светло-фиолетовый' in row.Title:
                            colour='фиолетовый'
                            colour_id = '61586'
                        elif 'темно-синий' in row.Title:
                            colour='темно-синий'
                            colour_id = '61592'
                        elif 'синий' in row.Title:
                            colour='синий'
                            colour_id = '61581'
                        elif 'темно-зеленый' in row.Title:
                            colour='темно-зеленый'
                            colour_id = '61602'
                        elif 'серебряный' in row.Title:
                            colour='серебристый'
                            colour_id = '61610'
                        elif 'золотой' in row.Title:
                            colour='золотой'
                            colour_id = '61582'
                        elif 'бордовый' in row.Title:
                            colour='бордовый'
                            colour_id = '61590'
                        
                        if 'Honor' in row.Title:
                            brand_name='Honor'
                            brand_id='39679'
                        elif 'Tecno' in row.Title:
                            brand_name='Tecno'
                            brand_id='928650554'
                        elif 'Realme' in row.Title:
                            brand_name='realme'
                            brand_id='970588994'
                        elif 'Samsung' in row.Title:
                            brand_name='Samsung'
                            brand_id='39605'
                        # elif 'Redmi' in row.Title:
                        #     brand_name='Redmi'
                        #     brand_id='39605'
                        elif 'Xiaomi' in row.Title:
                            brand_name='Xiaomi'
                            brand_id='39638'
                        elif 'Poco' in row.Title:
                            brand_name='Poco'
                            brand_id='971006054'
                        elif 'iPhone' in row.Title:
                            brand_name='Apple'
                            brand_id='39477'

                        task = {
                            "items": [
                                {
                                    "attributes": [
                                        #is required: true
                                        #Brand
                                        {
                                            "complex_id": 0,
                                            "id": 85,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    "value": "Нет бренда"
                                                }
                                            ]
                                        },
                                        #is required: true
                                        #Тип
                                        #Выберите наиболее подходящий тип товара. По типам товары распределяются по категориям на сайте Ozon. 
                                        #Если тип указан неправильно, товар попадет в неверную категорию. Чтобы правильно указать тип, 
                                        #найдите на сайте Ozon товары, похожие на ваш, и посмотрите, какой тип у них указан.",

                                        {
                                            "complex_id": 0,
                                            "id": 8229,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 97011,
                                                    "value": "Чехол для смартфона"
                                                }
                                            ]
                                        },
                                        #is required: True
                                        #"Название модели (для объединения в одну карточку)",
                                        #"Укажите название модели товара. Не указывайте в этом поле тип и бренд."
                                        #Чтобы объединить две карточки, для каждой передайте 9048 в массиве attributes. 
                                        #Все атрибуты в этих карточках, кроме размера или цвета, должны совпадать.
                                        {
                                            "complex_id": 0,
                                            "id": 9048,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    "value": str(row.Model)
                                                }
                                            ]
                                        },
                                        #is required: True
                                        #Product colour
                                        {
                                            "complex_id": 0,
                                            "id": 10096,
                                            "values": [
                                                {
                                                    "dictionary_value_id": colour_id,
                                                    "value": colour
                                                }
                                            ]
                                        },
                                        #is required: false
                                        #Название
                                        #Название пишется по принципу:\nТип + Бренд + Модель (серия + пояснение) + Артикул производителя + , (запятая) + Атрибут\n
                                        # Название не пишется большими буквами (не используем caps lock).\n
                                        # Перед атрибутом ставится запятая. Если атрибутов несколько, они так же разделяются запятыми.\n
                                        # Если какой-то составной части названия нет - пропускаем её.\n
                                        # Атрибутом может быть: цвет, вес, объём, количество штук в упаковке и т.д.\n
                                        # Цвет пишется с маленькой буквы, в мужском роде, единственном числе.\n
                                        # Слово цвет в названии не пишем.\nТочка в конце не ставится.\n
                                        # Никаких знаков препинания, кроме запятой, не используем.\n
                                        # Кавычки используем только для названий на русском языке.\n
                                        # Примеры корректных названий:\n
                                        # Смартфон Apple iPhone XS MT572RU/A, space black \n
                                        # Кеды Dr. Martens Киноклассика, бело-черные, размер 43\n
                                        # Стиральный порошок Ariel Магия белого с мерной ложкой, 15 кг\n
                                        # Соус Heinz Xtreme Tabasco суперострый, 10 мл\n
                                        # Игрушка для животных Четыре лапы \"Бегающая мышка\" БММ, белый",
                                        {
                                            "complex_id": 0,
                                            "id": 4180,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    "value": str(row.Title)
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #Маркетинговый текст
                                        {
                                            "complex_id": 0,
                                            "id": 4191,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    #"value": "Стильный чехол защитит ваш телефон от сколов и царапин."
                                                    "value": description_string
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #Партномер. Каталожный номер изделия или детали. Получаем этот номер от поставщика
                                        {
                                            "complex_id": 0,
                                            "id": 4381,
                                            "values": [
                                                {
                                                    "value": str(row.Part_Number)
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #product weight in g
                                        {
                                            "complex_id": 0,
                                            "id": 4383,
                                            "values": [
                                                {
                                                    "value": "100"
                                                }
                                            ]
                                        },
                                        #is requried: False
                                        #guarantee period
                                        #{
                                        #    "complex_id": 0,
                                        #    "id": 4385,
                                        #    "values": [
                                        #        {
                                        #            "value": "12"
                                        #        }
                                        #   ]
                                        #},
                                        #is requred: False
                                        #Country of manufacture
                                        {
                                            "complex_id": 0,
                                            "id": 4389,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    "value": "Китай"
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #Вид чехла
                                        {
                                            "complex_id": 0,
                                            "id": 5938,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 22053,
                                                    "value": "Книжка"
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #Технические особенности
                                        {
                                            "complex_id": 0,
                                            "id": 5941,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 26235,
                                                    "value": "Трансформация в подставку"
                                                }
                                            ]
                                        },
                                        #is required: False
                                        #Внешние размеры, мм. Записывается только число.
                                        # {
                                        #     "complex_id": 0,
                                        #     "id": 5942,
                                        #     "values": [
                                        #         {
                                        #             "dictionary_value_id": 0,
                                        #             "value": "200"
                                        #         }
                                        #     ]
                                        # },
                                        #is required: False
                                        #Material
                                        {
                                            "complex_id": 0,
                                            "id": 21615,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 971206481,
                                                    "value": "Искусственная кожа, силикон, текстиль"
                                                }
                                            ]
                                        },
                                        #is required : false
                                        #key words
                                        {
                                            "complex_id": 0,
                                            "id": 22336,
                                            "values": [
                                                {
                                                    "dictionary_value_id": 0,
                                                    "value": key_word
                                                }
                                            ]
                                        },
                                        #is required : false
                                        #подходит для
                                        #для поисковых запросов
                                        {
                                            "complex_id": 0,
                                            "id": 22898,
                                            "values": [
                                                {
                                                    "dictionary_value_id": brand_id,
                                                    "value": brand_name
                                                }
                                            ]
                                        },
                                    ],
                                    "barcode": str(row.Imei),
                                    "description_category_id": 17028650,
                                    "color_image": "",
                                    "complex_attributes": [],
                                    "currency_code": "RUB",
                                    "depth":200,
                                    "dimension_unit": "mm",
                                    "height": 20,
                                    "images": [str(row.Primary_Image), str(row.Image_1), str(row.Image_2), str(row.Image_3), str(row.Image_4), str(row.Image_5), str(row.Image_6), str(row.Image_7)],
                                    "images360": [],
                                    "name": str(row.Title),
                                    "offer_id": str(product.EAN),
                                    "old_price": str(row.MP_RRP),
                                    "pdf_list": [],
                                    "price": str(row.MP_RRP),
                                    "primary_image":"" ,
                                    "vat": "0",
                                    "weight": 100,
                                    "weight_unit": "g",
                                    "width": 100
                                }
                            ]
                        }
                    elif 'Стекло' in row.Title:
                        key_word_var =str(row.Model)
                        key_word=  f'Стекло, защитное стекло, {key_word_var}.'
                        task = {
                        "items": [
                            {
                                "attributes": [
                                    #is required: true
                                    #Brand
                                    {
                                        "complex_id": 0,
                                        "id": 85,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": "Нет бренда"
                                            }
                                        ]
                                    },
                                    #is required: true
                                    #Тип
                                    #Выберите наиболее подходящий тип товара. По типам товары распределяются по категориям на сайте Ozon. 
                                    #Если тип указан неправильно, товар попадет в неверную категорию. Чтобы правильно указать тип, 
                                    #найдите на сайте Ozon товары, похожие на ваш, и посмотрите, какой тип у них указан.",

                                    {
                                        "complex_id": 0,
                                        "id": 8229,
                                        "values": [
                                            {
                                                "dictionary_value_id": 91523,
                                                "value": "Защитное стекло"
                                            }
                                        ]
                                    },
                                    #is required: True
                                    #"Название модели (для объединения в одну карточку)",
                                    #"Укажите название модели товара. Не указывайте в этом поле тип и бренд."
                                    #Чтобы объединить две карточки, для каждой передайте 9048 в массиве attributes. 
                                    #Все атрибуты в этих карточках, кроме размера или цвета, должны совпадать.
                                    {
                                        "complex_id": 0,
                                        "id": 9048,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": str(row.Model)
                                            }
                                        ]
                                    },
                                    
                                    #is required: false
                                    #Название
                                    #Название пишется по принципу:\nТип + Бренд + Модель (серия + пояснение) + Артикул производителя + , (запятая) + Атрибут\n
                                    # Название не пишется большими буквами (не используем caps lock).\n
                                    # Перед атрибутом ставится запятая. Если атрибутов несколько, они так же разделяются запятыми.\n
                                    # Если какой-то составной части названия нет - пропускаем её.\n
                                    # Атрибутом может быть: цвет, вес, объём, количество штук в упаковке и т.д.\n
                                    # Цвет пишется с маленькой буквы, в мужском роде, единственном числе.\n
                                    # Слово цвет в названии не пишем.\nТочка в конце не ставится.\n
                                    # Никаких знаков препинания, кроме запятой, не используем.\n
                                    # Кавычки используем только для названий на русском языке.\n
                                    # Примеры корректных названий:\n
                                    # Смартфон Apple iPhone XS MT572RU/A, space black \n
                                    # Кеды Dr. Martens Киноклассика, бело-черные, размер 43\n
                                    # Стиральный порошок Ariel Магия белого с мерной ложкой, 15 кг\n
                                    # Соус Heinz Xtreme Tabasco суперострый, 10 мл\n
                                    # Игрушка для животных Четыре лапы \"Бегающая мышка\" БММ, белый",
                                    {
                                        "complex_id": 0,
                                        "id": 4180,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": str(row.Title)
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #Маркетинговый текст
                                    {
                                        "complex_id": 0,
                                        "id": 4191,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": "Защитное стекло защитит экран вашего телефона от сколов и царапин, возникающих в процессе нормальной экспуатации телефона и при падениях."
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #Партномер. Каталожный номер изделия или детали. Получаем этот номер от поставщика
                                    {
                                        "complex_id": 0,
                                        "id": 4381,
                                        "values": [
                                            {
                                                "value": str(row.Part_Number)
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #product weight in g
                                    {
                                        "complex_id": 0,
                                        "id": 4383,
                                        "values": [
                                            {
                                                "value": "18"
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #что входит в комплект
                                    {
                                        "complex_id": 0,
                                        "id": 4384,
                                        "values": [
                                            {
                                                "value": "Салфетка"
                                            }
                                        ]
                                    },
                                    #is requried: False
                                    #guarantee period
                                    #{
                                    #    "complex_id": 0,
                                    #    "id": 4385,
                                    #    "values": [
                                    #        {
                                    #            "value": "12"
                                    #        }
                                    #   ]
                                    #},
                                    #is requred: False
                                    #Country of manufacture
                                    {
                                        "complex_id": 0,
                                        "id": 4389,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": "Китай"
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #Применение
                                    {
                                        "complex_id": 0,
                                        "id": 5221,
                                        "values": [
                                            {
                                                "dictionary_value_id": 21995,
                                                "value": "На экран"
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #Толщина стекла, мм
                                    {
                                        "complex_id": 0,
                                        "id": 6134,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": "0.3"
                                            }
                                        ]
                                    },
                                    #is required: False
                                    #Количество в упаковке
                                    {
                                        "complex_id": 0,
                                        "id": 8513,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": "1"
                                            }
                                        ]
                                    },
                                    #is required : false
                                    #key words
                                    {
                                        "complex_id": 0,
                                        "id": 22336,
                                        "values": [
                                            {
                                                "dictionary_value_id": 0,
                                                "value": key_word
                                            }
                                        ]
                                    },
                                    #is requied: false
                                    #Покрытие
                                    {
                                        "complex_id": 0,
                                        "id": 11046,
                                        "values": [
                                            {
                                                "dictionary_value_id": 970788906,
                                                "value": "Глянцевое"
                                            }
                                        ]
                                    },
                                    #is requied: false
                                    #Прозрачность покрытия
                                    {
                                        "complex_id": 0,
                                        "id": 11047,
                                        "values": [
                                            {
                                                "dictionary_value_id": 970788960,
                                                "value": "Суперпрозрачное"
                                            }
                                        ]
                                    },
                                    #is requied: false
                                    #Дополнительные свойства покрытия
                                    {
                                        "complex_id": 0,
                                        "id": 11048,
                                        "values": [
                                            {
                                                "dictionary_value_id": 970788950,
                                                "value": "Олеофобное покрытие"
                                            }
                                        ]
                                    },
                                    #is requied: false
                                    #вид стекла
                                    {
                                        "complex_id": 0,
                                        "id": 11049,
                                        "values": [
                                            {
                                                "dictionary_value_id": 970788953,
                                                "value": "3D"
                                            }
                                        ]
                                    },
                                    #is requied: false
                                    #Твердость стекла
                                    {
                                        "complex_id": 0,
                                        "id": 11050,
                                        "values": [
                                            {
                                                "dictionary_value_id": 970788957,
                                                "value": "9H"
                                            }
                                        ]
                                    }
                                    #is requied: false
                                    #Подходит для
                                    # {
                                    #     "complex_id": 0,
                                    #     "id": 22898,
                                    #     "values": [
                                    #         {
                                    #             "dictionary_value_id": ,
                                    #             "value": ""
                                    #         }
                                    #     ]
                                    # }
                                ],
                                
                                "barcode": str(row.Imei),
                                "description_category_id": 17028628,
                                "color_image": "",
                                "complex_attributes": [],
                                "currency_code": "RUB",
                                "depth":200,
                                "dimension_unit": "mm",
                                "height": 5,
                                "images": [],
                                "images360": [],
                                "name": str(row.Title),
                                "offer_id": str(product.EAN),
                                "old_price": str(row.MP_RRP),
                                "pdf_list": [],
                                "price": str(row.MP_RRP),
                                "primary_image": str(row.Primary_Image),
                                "vat": "0",
                                "weight": 18,
                                "weight_unit": "g",
                                "width": 100
                            }
                        ]
                        }
                    #uploading new or updating existing product
                    response=requests.post('https://api-seller.ozon.ru/v3/product/import', json=task, headers=headers)  
                    status_code=response.status_code
                    json=response.json()
                    # print('=========Request Status & Task ID==========================')
                    # print('Наименование ' + str(n))
                    # print(status_code)
                    # if status_code == 200:
                    #     print('Товар в БД Озон создан')
                    # else:
                    #     string=f'. Товар {product.id} в БД Озон не создан.'
                    #     print(string)
                    #messages.error(request,  string)
                    #print(json)
                    #a=json['result']
                    task_id=json['result']['task_id']
                    print('Task_id: ' + str(task_id))
                    # в качестве ответа данный метод возвращает task_id. Мы можем использовать task id 
                    #в методе response=requests.post('https://api-seller.ozon.ru/v1/product/import/info', json=task_1, headers=headers)
                    #для того, чтобы узнать статус загрузки наименования. Если всё ок, то данный метод должен возвратить ozon_id,
                    #но обычно озону нужно время, чтобы отмодерировать новое наименование, поэтому, если сделать запрос сразу,
                    # ответ приходит без ozon_id, который нам нужен для загрузки кол-ва.

                    print('===================Status of Task Id=========================')
                    task_1  = {
                        "task_id": task_id
                    }
                    response=requests.post('https://api-seller.ozon.ru/v1/product/import/info', json=task_1, headers=headers)
                    json=response.json() 
                    print(json)
                    # a=json['result']
                    # task_id=a['task_id']
                    # print('============================================================')
                    # print('')
                    time.sleep(1.0)
            return redirect("log")
        else:
            # context = {
            #     "categories": categories,
            #     }
            #return render(request, "documents/delivery_auto.html", context) 
            return render(request, "marketplaces/ozon_product_create.html") 

    else:
        return redirect ('login')

def getting_ozon_id (request):
    if request.user.is_authenticated:
        #categories = ProductCategory.objects.all()
        #category = ProductCategory.objects.get(name='Аксы')
        headers = {
                    "Client-Id": "867100",
                    "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                }
        if request.method == "POST":
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            n=0
            cycle = len(df1)
            for i in range(cycle):
                time.sleep(0.5)
                n += 1
                row = df1.iloc[i]#reads each row of the df1 one by one
                imei=row.Imei
                if '/' in str(imei):
                    imei=imei.replace('/', '_')
                if Product.objects.filter(imei=imei).exists():
                    product=Product.objects.get(imei=imei)

                #getting ozon_id assigned by Ozon for further saving it in erms product model
                #and using it for changing quantity of product at ozon
                #существует два метода получения ozon_id
                task=    {
                        "filter": {
                            "offer_id": [
                                str(product.EAN),
                            ],
                           
                            "visibility": "ALL"
                        },
                        "last_id": "",
                        "limit": 100
                    }
                response=requests.post('https://api-seller.ozon.ru/v2/product/list', json=task, headers=headers) 
                time.sleep(0.5)
                json=response.json()
                print(json)
                ozon_id=json['result']['items'][0]['product_id']
                # a=json['result']
                # b=a['items']
                # c=b[0]
                # d=c['product_id']
                print(ozon_id)
                product.ozon_id=ozon_id
                product.save()


                
                #print('===========Второй метод получения ozon product_id=============')
                # task_2 = {
                #     "filter": {
                #         "offer_id": [ erms_product_id ],
                #     "visibility": "ALL"
                # },
                #     "last_id": "",
                #     "limit": 100
                # }
                # response=requests.post('https://api-seller.ozon.ru/v2/product/list', json=task_2, headers=headers)
                # json=response.json()
                # ozon_id=json['result']['items'][0]['product_id']
                # # a=json['result']
                # # b=a['items']
                # # c=b[0]
                # # d=c['product_id']
                # product.ozon_id=ozon_id
                # product.save()
                #print(json)
                #print('ozon product_id is ' +  str(ozon_product_id))
                #print('===============================================================')
      
            return redirect("log")
        else:
            return render(request, "marketplaces/getting_ozon_id.html") 

def change_ozon_qnty(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            headers = {
                        "Client-Id": "867100",
                        "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                    }
            if request.method == "POST":
                file = request.FILES["file_name"]
                
                df1 = pandas.read_excel(file)
                cycle = len(df1)
                for i in range(cycle):
                    time.sleep(0.5)
                    #n += 1
                    row = df1.iloc[i]#reads each row of the df1 one by one
                    imei=row.Imei
                    if Product.objects.filter(imei=imei).exists():
                        product=Product.objects.get(imei=imei)
                        task =   {
                            "stocks": [
                                {
                                    "offer_id": str(product.EAN),
                                    "product_id": str(product.ozon_id),
                                    "stock": str(row.Quantity),
                                    #warehouse Гордеевская
                                    "warehouse_id": 1020001938106000 
                                }
                            ]
                        }
                    response=requests.post('https://api-seller.ozon.ru/v2/products/stocks', json=task, headers=headers)
                    
                return redirect("log")
        else:
            return render(request, "marketplaces/change_ozon_qnty.html") 

    else:
        return redirect("log")


def ozon_product_archive(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            for i in range(cycle):
                row = df1.iloc[i]#reads each row of the df1 one by one
                imei=row.Imei
                if Product.objects.filter(imei=imei).exists():
                    product=Product.objects.get(imei=imei)
                headers = {
                        "Client-Id": "867100",
                        "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
                    }
                erms_product_id=str(product.id)

                #=======================перенести товар в архив===========================
                task = {
                    "product_id": [
            
                    "0"
                    ]
                }
                response=requests.post('https://api-seller.ozon.ru/v1/product/archive', json=task, headers=headers)  
                status_code=response.status_code
                print('+++++++++++++++++++++++++')
                print(status_code)
                json=response.json()
                print(json)

                #==========================удалить товар==============================
                task = {
                    "products": [
                    {
                    "offer_id": erms_product_id
                    }
                ]
                }
                response=requests.post('https://api-seller.ozon.ru/v2/products/delete', json=task, headers=headers)  
                status_code=response.status_code
                print('======================')
                print(status_code)
                json=response.json()
                print(json)
            return redirect("log")
            
        else:
            return render(request, "documents/delete_product_at_ozon.html")

    else:
        return redirect ('login')
    
def ozon_create_test(request):
    if request.user.is_authenticated:
        headers = {
            "Client-Id": "867100",
            "Api-Key": '6bbf7175-6585-4c35-8314-646f7253bef6'
        }
           
        task = {
            "items": [
                {
                    "attributes":[
                        {
                            "complex_id": 0,
                            "id": 85,
                            "values": [
                                {
                                    "dictionary_value_id": 0,
                                    "value": "Нет бренда"
                                }
                            ]
                        },
        
                        {
                            "complex_id": 0,
                            "id": 6134,
                            "values": [
                                {
                                    "dictionary_value_id": 0,
                                    "value": "0.3"
                                }
                            ]
                        },
                        {
                            "complex_id": 0,
                            "id": 4383,
                            "values": [
                                {
                                    "value": "18"
                                }
                            ]
                        },
                        {
                            "complex_id": 0,
                            "id": 11049,
                            "values": [
                                {
                                    "dictionary_value_id": 970788953,
                                    "value": "3D"
                                }
                            ]
                        },
                    ],

                                
                    "barcode":"",
                    "description_category_id": 15621050,
                    "color_image": "",
                    "complex_attributes": [],
                    "currency_code": "RUB",
                    "depth":200,
                    "dimension_unit": "mm",
                    "height": 20,
                    "images": "",
                    "images360": [],
                    "name":"",
                    "offer_id": "",
                    "old_price": 14900,
                    "pdf_list": [],
                    "price": 14900,
                    "primary_image":"" ,
                    "vat": "0",
                    "weight": 100,
                    "weight_unit": "g",
                    "width": 100
                }
                ]
        }
               
        #uploading new or updating existing product
        response=requests.post('https://api-seller.ozon.ru/v3/product/import', json=task, headers=headers)  
        status_code=response.status_code
        json=response.json()
        print('=========Request Status & Task ID==========================')
        print(status_code)
        print(json)
        #a=json['result']
        # task_id=json['result']['task_id']
        # print('Task_id: ' + str(task_id))
        # в качестве ответ данный метод возвращает task_id. Мы можем использовать task id 
        #в методе response=requests.post('https://api-seller.ozon.ru/v1/product/import/info', json=task_1, headers=headers)
        #для того, чтобы узнать статус загрузки наименования. Если всё ок, то данный метод должен возвратить ozon_id,
        #но обычто озону нужно время, чтобы отмодерировать новое наименование, поэтому, если сделать запрос сразу,
        # ответ приходёт без ozon_id, который нам нужен для загрузки кол-ва.

        # print('===================Status of Task Id=========================')
        # task_1  = {
        #     "task_id": task_id
        # }
        # response=requests.post('https://api-seller.ozon.ru/v1/product/import/info', json=task_1, headers=headers)
        # json=response.json() 
        # print(json)
        # a=json['result']
        # task_id=a['task_id']
        # print('============================================================')
        # print('')
        return redirect("log")
    else:
        return redirect ('login')

