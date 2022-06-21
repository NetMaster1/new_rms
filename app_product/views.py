from turtle import pd
from django.db.models.fields import BLANK_CHOICE_DASH, NullBooleanField
from django.http import request
from app_product.admin import RemainderHistoryAdmin
from app_clients.models import Customer
from app_personnel.models import BonusAccount
from app_error.models import ErrorLog
from django.shortcuts import render, redirect, get_object_or_404
from .smsc_api import *
from .models import (
    Document,
    # IntegratedDailySaleDoc,
    RemainderHistory,
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
    Voucher,
    Contributor,
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


# Create your views here.

def log(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        month=datetime.datetime.now().month
        year=datetime.datetime.now().year
        queryset_list = Document.objects.filter(created__year=year).order_by("-created")
        #============paginator module=================
        paginator = Paginator(queryset_list, 50)
        page = request.GET.get('page')
        paged_queryset_list = paginator.get_page(page)
        #=============end of paginator module===============
        doc_types = DocumentType.objects.all()
        users = User.objects.all()
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
                doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
              
                
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
        queryset_list = Document.objects.filter(user=request.user, created__date=date, posted=True).order_by("-created")
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
    registers = Register.objects.filter(document=document, new=True)
    for register in registers:
        register.delete()
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
                try:
                    product=Product.objects.get(imei=row.Imei)
                except Product.DoesNotExist:
                    product = Product.objects.create(
                        created=dateTime,
                        imei=row.Imei, 
                        category=category, 
                        name=row.Title
                    )
                product = Product.objects.get(imei=row.Imei)
                # checking docs before remainder_history
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__lt=dateTime).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__lt=dateTime).latest ('created')
                    pre_remainder=rho_latest_before.current_remainder
                else:
                    pre_remainder=0
                #=============Calculating av_price========================
                if AvPrice.objects.filter(imei=row.Imei).exists():
                    av_price_obj = AvPrice.objects.get(imei=row.Imei)
                    av_price_obj.current_remainder += int(row.Quantity)
                    av_price_obj.sum += int(row.Quantity) * int(row.Av_price)
                    av_price_obj.av_price = int(av_price_obj.sum) / int(av_price_obj.current_remainder)
                    av_price_obj.save()
                else:
                    av_price_obj = AvPrice.objects.create(
                        name=row.Title,
                        imei=row.Imei,
                        current_remainder=int(row.Quantity),
                        sum=int(row.Quantity) * int(row.Av_price),
                        av_price=int(row.Av_price),
                    )

                # creating remainder_history
                rho = RemainderHistory.objects.create(
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
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__gt=rho.created).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=row.Imei, shop=shop, created__gt=dateTime)
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
                av_price_obj = AvPrice.objects.get(imei=imeis[i])
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
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback       
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
                current_remainder=cash_remainder + document_sum,
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
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
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
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
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
            cash = request.POST["cash"]
            cash=int(cash)
            credit = request.POST["credit"]
            credit=int(credit)
            card = request.POST["card"]
            card=int(card)
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
            #paying with cashback
            document.sum=document_sum
            document.sum_minus_cashback = document_sum - cashback_off
            document.save()
            sum_to_pay = document.sum_minus_cashback
               
        
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
                    if av_price_obj.sum<=0:
                        av_price_obj.sum=0
                        av_price_obj.av_price = 0
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
                #deleting reg where cash/credit/card values have been stored in order do display the in html template
                if PaymentRegister.objects.filter(document=document).exists():
                    temp_cash_reg=PaymentRegister.objects.get(document=document)
                    temp_cash_reg.delete()
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
            av_price_obj.current_remainder= av_price_obj.current_remainder + rho.outgoing_quantity
            #av_price_obj.save()
            av_price_obj.sum+=av_price_obj.current_remainder*rho.av_price
            #av_price_obj.save()
            if av_price_obj.current_remainder > 0:
                av_price_obj.av_price=av_price_obj.sum / av_price_obj.current_remainder
            else:
                av_price_obj.av_price =0
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
#При проведении докумена (продажа) кэшбэк, списанный со счета клиента сохраняется в document.cashback_off.
#При отмене проведения документа (продажа) начисленный кэшбэк обнуляется со счета клиента (customer.accum_cashback); списанный кэшбэк возвращается на счет клиента, но одновременно сохраняется в document.cashback_off.
#При проведении change_sale_unposted рассчитывается новый начисленный кэшбэк, который идет на счет клиенту; списываемый кэшбэк списывается со счета клиента (сумма берется из document.cashback_off). Таким образом, при редактировании документа change_sale_posted сумма кэшбэка к списанию не редактируется.
#При удалении документа кэшбэк с покупки не начисляется; списываемый кэшбэк не списывается со счета клиент, и одновременно удаляется из document.cashback_off вместе с документом.


def cashback(request, identifier_id):
    if request.user.is_authenticated:
        
        identifier = Identifier.objects.get(id=identifier_id)
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
        base_url="https://smsc.ru/sys/send.php?login=NetMaster&psw=ylhio65v&phones={}&mes=code&call=1&fmt=3"
        url=base_url.format(phone)
        api_request=requests.get(url)
        #server's response is returned in json format

        try:
            api=json.loads(api_request.content)
            code_string=api['code']
            messages.success(request, "Сейчас покупатель получит звонок. Необходимо ввести последние 6 цифр номера, с которого будет звонок, чтобы подтвердить списание кэш-бэка.")
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
        cashback_off = 0
        return redirect("payment", identifier.id, client.id, cashback_off)
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
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.datetime.now()
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
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            if Product.objects.filter(imei=row.Imei).exists():
                product=Product.objects.get(imei=row.Imei)
            else:
                product = Product.objects.create(
                    name=row.Title,
                    imei=row.Imei, 
                    category=category,                   
                )
            # checking docs before remainder_history
            if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__lt=document.created).exists():
                rho_latest_before = RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__lt=document.created).latest('created')
                pre_remainder=rho_latest_before.current_remainder
            else:
                pre_remainder=0
            # creating remainder_history
            rho = RemainderHistory.objects.create(
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
            if AvPrice.objects.filter(imei=row.Imei).exists():
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
            if RemainderHistory.objects.filter(imei=row.Imei, shop=shop, created__gt=rho.created).exists():
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
    registers = Register.objects.filter(identifier=identifier).order_by("created")
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
            return redirect("delivery", identifier.id)
        else:
            product = Product.objects.create(name=name, imei=imei, category=category)
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
                #==============av_price module====================
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )
                    rho.av_price=av_price_obj.av_price
                    rho.save()
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
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")

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
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
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
                                wholesale_price=int(prices[i]),
                                sub_total=int(int(quantities[i]) * int(prices[i]))
                            )
                        document_sum+=rho.sub_total
                              #===========Av_price_module================
                        if AvPrice.objects.filter(imei=imeis[i]).exists():
                            av_price_obj = AvPrice.objects.get(imei=imeis[i])
                            av_price_obj.current_remainder += int(quantities[i])
                            av_price_obj.sum += int(quantities[i]) * int(prices[i])
                            av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
                            av_price_obj.save()
                        else:
                            av_price_obj=AvPrice.objects.create(
                                name=names[i],
                                imei=imeis[i],
                                current_remainder=quantities[i],
                                sum=sub_totals[i],
                                av_price=int(sub_totals[i])/ int(quantities[i])
                            )
                #===================End of Av_price module      
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

# =====================================================================================
def identifier_transfer(request):
    identifier = Identifier.objects.create()
    return redirect("transfer", identifier.id)

def transfer(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all()
        shop_default = Shop.objects.get(name="ООС")
        if Register.objects.filter(identifier=identifier).exists():
            registers = Register.objects.filter(identifier=identifier)
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
    shops = Shop.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    #if "check_imei" in request.GET:
    #shop = request.GET["shop"]
    if request.method == "POST":
        imei = request.POST["check_imei"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        # quantity = request.POST["quantity"]
        # quantity=int(quantity)
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
               
                messages.error(request,"Вы уже ввели данное наименование. Запишите нужно кол-во в списке ниже",)
                return redirect("transfer", identifier.id)
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
                    print(product.category)
                    register = Register.objects.create(
                        product=product,
                        identifier=identifier,
                        quantity=1,
                    )
                return redirect ("transfer", identifier.id)
        else:
            messages.error(request, "Данное наименование отсутствует в базе данных")
            return redirect("transfer", identifier.id)
    else:
        return redirect("transfer", identifier.id)

def check_transfer_unposted(request, document_id):
    users = Group.objects.get(name='sales').user_set.all()
    group = Group.objects.get(name='admin').user_set.all()
    shops = Shop.objects.all()
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    for register in registers:
        if register.deleted == True:
            register.delete()
    shop_sender = document.shop_sender
    # if "imei_check" in request.GET:
    if request.method=="POST":
        imei = request.POST["imei_check"]
        if '/' in imei:
            imei=imei.replace('/', '_')
        quantity = request.POST["quantity_input"]
        # shop = request.GET["shop"]
        # shop = Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderHistory.objects.filter(imei=imei, shop=shop_sender).exists():
                rho=RemainderHistory.objects.filter(imei=imei, shop=shop_sender).latest('created')
                if rho.current_remainder >= int(quantity):
                    product = Product.objects.get(imei=imei)
                    if Register.objects.filter(document=document, product=product).exists():
                        messages.error(request,"Вы уже ввели данное наименование. Запишите нужно кол-во в списке ниже",)
                        return redirect("change_transfer_unposted", document.id)
                    else:
                        register = Register.objects.create(
                            product=product,
                            document=document,
                            quantity=quantity,
                            new=True,
                        )
                        if rho.retail_price:
                            register.price=rho.retail_price
                        else:
                            register.price=0
                        register.sub_total = int(quantity) * int(register.price)
                        register.save()
                        return redirect("change_transfer_unposted", document.id)
                else:
                    messages.error(request,
                        "На складе фирмы-отправителя отсутствует необходимое количество",
                    )
                    return redirect("change_transfer_unposted", document.id)
            else:
                messages.error(request, "Данное наименование отсутствует на данном складе")
                return redirect("change_transfer_unposted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в базе данных")
            return redirect("change_transfer_unposted", document.id)
    else:
        messages.error(request, "Вы не ввели IMEI")
        return redirect("change_transfer_unposted", document.id)

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
                            string=f'Документ не проведеден. Товар с IMEI {imeis[i]} отсутствует на балансе фирмы.'
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
    rhos=RemainderHistory.objects.filter(document=document).exclude(shop=shop_receiver)
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
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
        dateTime=document.created
        dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
        shop_receiver=document.shop_receiver
        shop_sender=document.shop_sender
        shops = Shop.objects.all()
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
        shops=Shop.objects.all()
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
            #checking availabiltiy of items to avoid saving only a portion of document
            for i in range(cycle):
                row = df1.iloc[i]#reads rows of excel file one by one
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop_sender, created__lt=dateTime).exists():
                    remainder_history= RemainderHistory.objects.filter(imei=row.Imei, shop=shop_sender, created__lt=dateTime).latest('created')
                    if remainder_history.current_remainder < int(row.Quantity):
                        #check_point.append(False)
                        string=f'Документ не проведеден. Количество товара с данным IMEI {row.Imei} недостаточно для перемещения.'
                        messages.error(request,  string)
                        return redirect("transfer_auto")
                else:
                    string=f'Документ не проведеден. Товар с IMEI {row.Imei} отсутствует на балансе фирмы.'
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
                product=Product.objects.get(imei=row.Imei)
                if AvPrice.objects.filter(imei=row.Imei).exists():
                    av_price=AvPrice.objects.get(imei=row.Imei)
                else:
                    av_price=AvPrice.objects.create(
                        imei=row.Imei,
                        name=row.Title,
                        current_remainder=row.Quantity,
                        av_price=row.Retail_price,
                        sum=int(row.Quantity)*int(row.Retail_price)
                    )
                document_sum+=int(row.Quantity) * int(row.Retail_price)
                # checking shop_sender
                #additional check in case quantities in excel file are 0
                if RemainderHistory.objects.filter(imei=row.Imei,shop=shop_sender,created__lt=document.created).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=row.Imei,shop=shop_sender,created__lt=document.created).latest('created')
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
                    imei=row.Imei,
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
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop_sender, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=row.Imei,shop=shop_sender,created__gt=rho.created).order_by('created')
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
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop_receiver, created__lt=document.created).exists():
                    rho_latest_before = RemainderHistory.objects.filter(imei=row.Imei, shop=shop_receiver, created__lt=document.created).latest('created')
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
                if RemainderHistory.objects.filter(imei=row.Imei, shop=shop_receiver, created__gt=rho.created).exists():
                    remainder=rho.current_remainder
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=row.Imei,shop=shop_receiver,created__gt=rho.created).order_by('created')
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
        if RemainderHistory.objects.filter(inventory_doc=document).exists():
            rhos = RemainderHistory.objects.filter(inventory_doc=document).order_by("created")
        else:
            rhos = RemainderHistory.objects.filter(document=document).order_by("created")
            base_document=None
        numbers = rhos.count()
        for rho, i in zip(rhos, range(numbers)):
            rho.number = i + 1
            rho.save()
        context = {
            "rhos": rhos,
            "document": document,
            "base_document": base_document,
            'dateTime': dateTime,
            'shop': shop
        }
        return render(request, "documents/change_recognition_posted.html", context)
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
            #if shop.retail == True:
            av_price_obj.sum=av_price_obj.current_remainder * av_price_obj.av_price
            if av_price_obj.sum==0:
                av_price_obj.av_price=0
            #else:
            #    av_price_obj.sum-=av_price_obj.current_remainder * rho.wholesale_price
            #if av_price_obj.current_remainder > 0:
            #    av_price_obj.av_price = av_price_obj.sum / av_price_obj.current_remainder
            #else:
            #    av_price_obj.av_price=0
            #    av_price_obj.sum=0
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
                # if RemainderHistory.objects.filter(shop=shop, imei=imei).exists():
                #     remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imei)
                # else:
                #     messages.error(request, "Данное наименование отсутствует на балансе данной торговой точки.")
                #     return redirect("signing_off", identifier.id)
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
                    # if shop.retail:
                    #     register.price=remainder_current.retail_price
                    # else:
                    #     av_price=AvPrice.objects.get(imei=imei)
                    #     register.price=av_price.av_price
                    # register.sub_total=register.price*register.quantity
                    # register.save()
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
    if document.base_doc:
        base_document=Document.objects.get(id=document.base_doc)
    if RemainderHistory.objects.filter(inventory_doc=document).exists():
        rhos = RemainderHistory.objects.filter(inventory_doc=document).order_by("created")
    else:
        rhos = RemainderHistory.objects.filter(document=document).order_by("created")
        base_document=None
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop = document.shop_sender
    dateTime=document.created
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    numbers = rhos.count()
    for rho, i in zip(rhos, range(numbers)):
        rho.number = i + 1
        rho.save()
    
    else:
        context = {
            "rhos": rhos,
            "document": document,
            'base_document': base_document,
            'shop': shop,
            "dateTime": dateTime,
        }
        return render(request, "documents/change_signing_off_posted.html", context)
    
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
            # posting the document
            if post_check == True:
                #checking if return is based on sale for this shop
                # n = len(names)
                # for i in range(n):
                #     if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime, rho_type=base_doc_type).exists():
                #         rho_latest_before= RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime, rho_type=base_doc_type).latest('created')
                #     else:
                #         string=f'Документ не проведен. Товар с IMEI {imeis[i]} никогда не продавался с баланса данной фирмы.'
                #         messages.error(request,  string)
                #         return redirect("return_doc", identifier.id)       
                document = Document.objects.create(
                    shop_receiver=shop,
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=True
                )
                n = len(names)
                document_sum = 0
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
#===============================================================================================
# def list_sale(request):
#     shops = Shop.objects.all()
#     if request.method == "POST":
#         shop = request.POST["shop"]
#         shop = Shop.objects.get(id=shop)
#         imei = request.POST["IMEI"]
#         start_date = request.POST["start_date"]
#         end_date = request.POST["end_date"]
#         sales = Sale.objects.filter(imei=imei, shop=shop)
#         if start_date:
#             sales = sales.filter(created__gte=start_date)
#         if end_date:
#             sales = sales.filter(created__lte=end_date)
#         context = {"sales": sales, "shops": shops}
#         return render(request, "documents/list_sale.html", context)

#     context = {"shops": shops}
#     return render(request, "documents/list_sale.html", context)
#=================================================================================================
def identifier_revaluation(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("revaluation", identifier.id)
    else:
        return redirect("login")

def check_revaluation(request, identifier_id):
    # shops = Shop.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    #registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        shop = request.POST["shop"]
        try:
            shop = Shop.objects.get(id=shop)
        except:
            messages.error(request, "Вы не выбрали ТТ для переоценки")
            return redirect("revaluation", identifier.id)
        if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
            remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
            retail_price=remainder_current.retail_price
            product = Product.objects.get(imei=imei)
            # remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
            if Register.objects.filter(identifier=identifier, product=product, shop=shop).exists():
                messages.error(request, "Вы уже ввели данное наименование")
                return redirect("revaluation", identifier.id)
            else:
                register = Register.objects.create(
                    #shop=shop, 
                    identifier=identifier, 
                    product=product,
                    current_price=retail_price
                )
                return redirect("revaluation", identifier.id)
        else:
            messages.error(request,"Данное наименование отсутствует на данном складе. Вы не можете переоценить его.",)
            return redirect("revaluation", identifier.id)

def check_revaluating_unposted (request, document_id):
    pass

def revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all().exclude(retail=False)
    registers = Register.objects.filter(identifier=identifier)
    context = {
        "identifier": identifier,
        "categories": categories,
        "shops": shops,
        "registers": registers,
    }
    return render(request, "documents/revaluation.html", context)

def delete_line_revaluation(request, imei, identifier_id, shop_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    shop=Shop.objects.get(id=shop_id)
    items = Register.objects.filter(identifier=identifier, product=product, shop=shop)
    for item in items:
        item.delete()
    return redirect("revaluation", identifier.id)

def delete_line_revaluation_unposted (request, imei, document_id):
    pass

def clear_revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("revaluation", identifier.id)

def revaluation_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        shops = request.POST.getlist("shop", None)
        quantities = request.POST.getlist("quantity", None)
        # prices_current=request.POST.getlist('price_current', None)
        prices_new = request.POST.getlist("price_new", None)
        # shop=Shop.objects.get(id=shop)
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
        if imeis:
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()
                document = Document.objects.create(
                title=doc_type, 
                user=request.user, 
                created=dateTime
            )
            n = len(names)
            # document_sum=0
            for i in range(n):
                shop = Shop.objects.get(name=shops[i])
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_current = RemainderCurrent.objects.get(
                        shop=shop, imei=imeis[i]
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.retail_price = remainder_history.retail_price
                    # remainder_current.total_av_price=remainder_history.sub_total
                    remainder_current.save()
                else:
                    messages.error(request, "Остатаки для переоценки отсутствуют.")
                    return redirect("revaluation", identifier.id)

                revaluation_item = Revaluation.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price_currrent=remainder_current.retail_price,
                    price_new=prices_new[i],
                    # quantity=quantities[i],
                    # sub_total=int(quantities[i]) * int(prices[i])
                )

                # creating remainder_history
                remainder_history = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=0,
                    retail_price=prices_new[i],
                    current_remainder=remainder_current.current_remainder
                    # sub_total= int(int(quantities[i]) * int(prices[i])),
                )
                remainder_current.retail_price = remainder_history.retatil_price
                remainder_current.save()

        for register in registers:
            register.delete()
        identifier.delete()
        return redirect("log")
    else:
        messages.error(request, "Вы не ввели ни одного наименования.")
        return redirect("revaluation", identifier.id)

def change_revaluation_posted (request, document_id):
    pass

def change_revaluation_unposted (request, document_id):
    pass

def unpost_revaluation (request, document_id):
    pass
# =========================================Cash_off salary ===========================================

def cash_off_salary(request):
    if request.user.is_authenticated:
        users_sales=Group.objects.get(name='sales').user_set.all()
        users=User.objects.all()
        expense = Expense.objects.get(name="Зарплата")
        doc_type = DocumentType.objects.get(name="РКО (зарплата)")
        shops = Shop.objects.all()
        expenses = Expense.objects.all().exclude(name="Зарплата")
        if request.method == "POST":
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
                        return redirect("change_cash_off_salary_unpostedd")
                else:
                    messages.error(request,"В кассе недостаточно денежных средств",)
                    return redirect("change_cash_off_salary_unposted")
              
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
    document = Document.objects.get(id=document_id)
    dateTime=document.created 
    dateTime=dateTime.strftime('%Y-%m-%dT%H:%M')
    system_users=Group.objects.get(name='sales').user_set.all()
    shops = Shop.objects.all()
    expense = Expense.objects.get(name="Зарплата")
    register = Register.objects.get(document=document)
    users=User.objects.all()
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
                    return redirect("change_cash_off_salary_unposted")
            else:
                messages.error(request,"В кассе недостаточно денежных средств",)
                return redirect("change_cash_off_salary_unposted")
                
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
            'users': users
        }
        return render(request, "documents/change_cash_off_salary_unposted.html", context)

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
            sequence_rhos_before = RemainderHistory.objects.filter(imei=obj.imei, shop=shop, created__lt=dateTime)
            remainder_history = sequence_rhos_before.latest("created")
            register=Register.objects.create(
                identifier=identifier,
                shop=shop,
                name=remainder_history.name,
                imei=remainder_history.imei,
                quantity=remainder_history.current_remainder,
                price=remainder_history.retail_price
            )
        registers=Register.objects.filter(identifier=identifier)
        сontext = {
            "registers": registers, 
            "shops": shops, 
            "categories": categories,
            'identifier': identifier
            }
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
    registers=Register.objects.filter(identifier=identifier)
    context = {
        'registers': registers,
        'identifier': identifier
    }
    return render (request, 'documents/inventory_list.html', context)

def inventory_input (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    doc_type=DocumentType.objects.get(name='Инвентаризация ТМЦ')
    registers=Register.objects.filter(identifier=identifier)
    shop = registers.first().shop
    #dateTime = registers.first().created
    dateTime = datetime.now()
    if request.method == "POST":
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        real_qnts = request.POST.getlist("real_qnt", None)
        prices=request.POST.getlist('price', None)
        #sub_totals=request.POST.getlist('sub_total', None)
        # category=ProductCategory.objects.get(id=category)
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
            document = Document.objects.create(
                title=doc_type, 
                user=request.user, 
                created=dateTime,
                posted=True
            )
            n=len(names)
            sign_off_doc =[]
            recogn_doc=[]
            for i in range(n):
                if quantities[i]>real_qnts[i]:
                    doc_type_1=DocumentType.objects.get(name='Списание ТМЦ')
                    # checking docs before remainder_history
                    sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                    remainder_history = sequence_rhos_before.latest("created")
                    # remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                    # remainder_current.current_remainder = remainder_history.current_remainder
                    new_rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type_1,
                        #rho_type=document.title,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_history.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=int(quantities[i])-int(real_qnts[i]),
                        current_remainder=real_qnts[i],
                        #wholesale_price=int(prices[i]),
                        #sub_total= int(real_qnts[i])*av_price_obj.av_price,
                    )
                    remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                    remainder_current.current_remainder=new_rho.current_remainder
                    remainder_current.save()
                    #remainder_current.total_av_price=remainder_current.current_remainder*remainder_current.av_price
                    #document_sum=remainder_history.sub_total
                    sign_off_doc.append(new_rho)
                elif quantities[i]<real_qnts[i]:
                    doc_type_2=DocumentType.objects.get(name='Оприходование ТМЦ')
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                        remainder_current.current_remainder = remainder_history.current_remainder
                    else:
                        if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop).exists():
                            remainder_current=RemainderCurrent.objects.filter(imei=imeis[i], shop=shop)
                            remainder_current.current_remainder=0
                        else:
                            remainder_current=RemainderCurrent.objects.create(
                                shop=shop,
                                imei=imeis[i],
                                current_remainder=0
                            )
                    new_rho = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type_2,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_history.current_remainder,
                        incoming_quantity=int(real_qnts[i])-int(quantities[i]),
                        outgoing_quantity=0,
                        current_remainder=real_qnts[i],
                        #wholesale_price=int(prices[i]),
                        #sub_total=int(real_qnts[i]) * av_price_obj.av_price,
                    )
                    #document_sum=remainder_history.sub_total
                    remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                    remainder_current.current_remainder=new_rho.current_remainder
                    remainder_current.save()
                    #remainder_current.total_av_price=int(remainder_current.current_remainder)*int(remainder_current.av_price)
                    recogn_doc.append(new_rho)
                else:
                    sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_history.inventory_doc=document
                    remainder_history.save()
            if len(sign_off_doc)>0:
                doc_type_sign_off=DocumentType.objects.get(name='Списание ТМЦ')
                doc_sign_off = Document.objects.create(
                    title=doc_type_sign_off, 
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    base_doc=document.id
                )
                for i in sign_off_doc:
                    i.inventory_doc=doc_sign_off
                    i.save()
            if len(recogn_doc)>0:
                doc_type_recogn=DocumentType.objects.get(name='Оприходование ТМЦ')
                doc_recogn = Document.objects.create(
                    title=doc_type_recogn, 
                    user=request.user, 
                    created=dateTime,
                    posted=True,
                    base_doc=document.id
                )
                for i in recogn_doc:
                    i.inventory_doc=doc_recogn
                    i.save()
            for register in registers:
                register.delete()
            identifier.delete(0)           
            return redirect ('log')
        else:
            document = Document.objects.create(
                title=doc_type, 
                user=request.user, 
                created=dateTime, 
                posted=False
            )
            n = len(names)
            #document_sum = 0
            for i in range(n):
                register = Register.objects.get(identifier=identifier, imei=imeis[i])
                register.document=document
                register.shop=shop
                register.name=names[i]
                register.imei=imeis[i]
                register.quantity=quantities[i]
                register.real_quantity=real_qnts[i]
                register.price=prices[i]
                register.save()
                #identifier.delete()
            return redirect ('log')
    
def change_inventory_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos=RemainderHistory.objects.filter(document=document)
    for rho in rhos:
        if not Register.objects.filter(imei=rho.imei, document=document).exists():
            register=Register.objects.create(
                document=document,
                shop=rho.shop,
                imei=rho.imei,
                name=rho.name,
                price=rho.retail_price,
                quantity=rho.pre_remainder,
                real_quantity=rho.current_remainder
            )
    registers=Register.objects.filter(document=document)
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        'registers': registers,
        'document': document,
    }
    return render (request, 'documents/change_inventory_posted.html', context)
        
def change_inventory_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    doc_type = DocumentType.objects.get(name="Инвентаризация ТМЦ")
    shop=registers.first().shop
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
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        # posting the document
        if post_check == True:
            sign_off_doc =[]
            recogn_doc=[]
            if imeis:
                n = len(names)    
                for i in range(n):
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=document.created).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=document.created)
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                        remainder_current.current_remainder = remainder_history.current_remainder
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop).exists():
                            remainder_current = RemainderCurrent.objects.get(imei=imeis[i], shop=shop)
                            remainder_current.current_remainder = 0
                            # remainder_current.av_price=0
                            # remainder_current.total_av_price=0
                            remainder_current.save()
                        else:
                            remainder_current = RemainderCurrent.objects.create(
                                    updated=document.created,
                                    shop=shop,
                                    imei=imeis[i],
                                    name=names[i],
                                    current_remainder=0,
                                    # av_price=0,
                                    # total_av_price=0
                                )
                    # creating remainder_history
                    if quantities[i]>real_qnts[i]:
                        remainder_history = RemainderHistory.objects.create(
                            document=document,
                            created=document.created,
                            shop=shop,
                            rho_type=doc_type,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            pre_remainder=remainder_current.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity=int(quantities[i])-int(real_qnts[i]),
                            current_remainder=real_qnts[i]
                            #sub_total= int(quantities[i]) * int(prices[i]),
                        )
                        recogn_doc.append(remainder_history)
                    elif quantities[i]<real_qnts[i]:
                        remainder_history = RemainderHistory.objects.create(
                            document=document,
                            created=document.created,
                            shop=shop,
                            rho_type=doc_type,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            pre_remainder=remainder_current.current_remainder,
                            incoming_quantity=int(real_qnts[i])-int(quantities[i]),
                            outgoing_quantity=0,
                            current_remainder=real_qnts[i]
                            #sub_total= int(quantities[i]) * int(prices[i]),
                        )
                    sign_off_doc.append(remainder_history)
                    remainder_current.current_remainder = remainder_history.current_remainder
                    remainder_current.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__gt=document.created).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created)
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
                if len(sign_off_doc)>0:
                    doc_type_sign_off=DocumentType.objects.get(name='Списание ТМЦ')
                    doc_sign_off = Document.objects.create(
                        title=doc_type_sign_off, 
                        user=request.user, 
                        created=document.created,
                        posted=True,
                        base_doc=document.id
                    )
                    for i in sign_off_doc:
                        i.inventory_doc=doc_sign_off
                        i.save()
                if len(recogn_doc)>0:
                    doc_type_recogn=DocumentType.objects.get(name='Оприходование ТМЦ')
                    doc_recogn = Document.objects.create(
                        title=doc_type_recogn, 
                        user=request.user, 
                        created=document.created,
                        posted=True,
                        base_doc=document.id
                    )
                    for i in recogn_doc:
                        i.inventory_doc=doc_recogn
                        i.save()
                for register in registers:
                    register.delete()
                document.posted=True
                document.save()
                return redirect ('log')
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_inventory_unposted", document.id)
        else:
            if imeis:
                n = len(names)
                #document_sum = 0
                for i in range(n):
                    register = Register.objects.get(document=document, imei=imeis[i])
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.real_quantity = real_qnts[i]
                    #register.sub_total = sub_totals[i]
                    #register.new = False
                    register.save()
                    #document_sum += int(register.sub_total)
                    if Register.objects.filter(document=document, deleted=True).exists():
                        registers=Register.objects.filter(document=document, deleted=True)
                        for register in registers:
                            register.delete()
                #document.sum = document_sum
                #document.save()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_inventory_unposted", document.id)
    else:
        context = {
            "registers": registers,
            "shop": shop,
            "document": document,
        }
        return render(request, "documents/change_inventory_unposted.html", context)

def enter_new_product_inventory (request, identifier_id):
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

def check_inventory_unposted (request, document_id):
    document=Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            if Register.objects.filter(document=document,imei=product.imei).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect ('change_inventory_unposted', document.id)
            else:
                product=Product.objects.get(imei=imei)
                register = Register.objects.create(
                    document=document, 
                    imei=product.imei, 
                    name=product.name,
                    quantity=0,
                    new=True
                )
                return redirect ('change_inventory_unposted', document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_inventory_unposted", document.id)

def check_inventory (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier,imei=product.imei).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect ('inventory_list', identifier.id)
            else:
                product=Product.objects.get(imei=imei)
                register = Register.objects.create(
                    identifier=identifier, 
                    imei=product.imei, 
                    name=product.name,
                    quantity=0,
                    new=True
                )
                return redirect ('inventory_list', identifier.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
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


# def email(request):
#     send_mail(
#         'Hello from DjangoDev',
#         'Here goes email text',
#         '79200711112@yandex.ru',
#         ['Sergei_Vinokurov@rambler.ru'],
#         fail_silently=False
#     )
#     return render(request, 'email/email.html')