from django.db.models.fields import BLANK_CHOICE_DASH, NullBooleanField
from django.http import request
from app_product.admin import RemainderHistoryAdmin
from app_clients.models import Customer
from app_personnel.models import BonusAccount
from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Document,
    Delivery,
    Recognition,
    SignOff,
    Sale,
    Transfer,
    Returning,
    Revaluation,
    RemainderHistory,
    Register,
    Identifier,
    RemainderCurrent,
    AvPrice,
)
from app_cash.models import CashRemainder, Cash, Credit, Card
from datetime import datetime, date
from app_reference.models import (
    Shop,
    Supplier,
    Product,
    ProductCategory,
    DocumentType,
    Expense,
    Voucher,
)
from app_cash.models import Cash, CashRemainder, Credit, Card
from app_cashback.models import Cashback
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.utils import timezone
from django.contrib import messages
import decimal
import random
import pandas

# import datetime
from datetime import datetime
import pytz
from twilio.rest import Client

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        # auth.logout(request)
        return redirect("login")

def search(request):
    if request.method == "POST":
        keyword = request.POST["keyword"]
        try:
            remainders = RemainderCurrent.objects.filter(name__icontains=keyword)
        except:
            messages.error(request, "УУУУУПС. Такого наименования не существует")
            return redirect("seach")

        context = {"remainders": remainders}
        return render(request, "documents/search_results.html", context)

    else:
        return render(request, "documents/search.html")

def close_search(request):
    return redirect("log")

def close_without_save(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if Register.objects.filter(identifier=identifier).exists():
        registers = Register.objects.filter(identifier=identifier)
        for register in registers:
            register.delete()
        identifier.delete()
        return redirect("log")
    else:
        identifier.delete()
        return redirect("log")

def close_edited_document(request, document_id):
    document = Document.objects.get(id=document_id)
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document)
        for register in registers:
            register.delete()
        return redirect("log")
    else:
        return redirect("log")

def close_unposted_document(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document, new=True)
    for register in registers:
        register.delete()
    registers = Register.objects.filter(document=document, deleted=True)
    for register in registers:
        register.deleted = False
        register.save()
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
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document)
        for register in registers:
            register.delete()
    document.delete()
    return redirect("log")
# ================================Sale Operations=================================
def identifier_sale(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("sale", identifier.id)
    else:
        return redirect("login")

def check_sale(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    shops = Shop.objects.all()
    # if imei in request.GET:
    #     imei=request.GET['imei']
    #     if imei:
    if request.method == "POST":
        try:
            shop = request.POST["shop"]
        except:
            messages.error(request, "Введите ТТ, откуда осуществляется продажа")
            return redirect("sale", identifier.id)
        imei = request.POST["imei"]
        quantity = request.POST["quantity"]
        quantity = int(quantity)
        shop = Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
                remainder_current = RemainderCurrent.objects.get(imei=imei, shop=shop)
                if remainder_current.current_remainder < quantity:
                    messages.error(
                        request,
                        "Количество, необходимое для продажи отсутствует на данном складе",
                    )
                    return redirect("sale", identifier.id)
                else:
                    product = Product.objects.get(imei=imei)
                    if Register.objects.filter(
                        identifier=identifier, product=product
                    ).exists():
                        register = Register.objects.get(
                            identifier=identifier, product=product
                        )
                        register.quantity += quantity
                        register.save()
                        register.sub_total = register.price * register.quantity
                        register.save()
                        return redirect("sale", identifier.id)
                    else:
                        register = Register.objects.create(
                            shop=shop,
                            quantity=quantity,
                            identifier=identifier,
                            product=product,
                            price=remainder_current.retail_price,
                            sub_total=quantity * remainder_current.retail_price,
                        )
                        return redirect("sale", identifier.id)
            else:
                messages.error(
                    request,
                    "Данное наименование для продажи отсутствует на данном складе",
                )
                return redirect("sale", identifier.id)
        else:
            messages.error(
                request, "Данное наименование для продажи отсутствует в базе данных"
            )
            return redirect("sale", identifier.id)

def sale(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        shops = Shop.objects.all()
        sum = 0
        registers = Register.objects.filter(identifier=identifier)
        for register in registers:
            sum += register.sub_total
        register = Register.objects.last()
        context = {
            "identifier": identifier,
            "registers": registers,
            "shops": shops,
            "sum": sum,
            "register": register,
        }
        # if request.session.expires():
        #     identifier.delete()
        #     for register in registers:
        #         register.delete()
        #     return redirect ('login')
        # else:
        return render(request, "documents/sale.html", context)
    else:
        return redirect("login")

def delete_line_sale(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.filter(identifier=identifier, product=product)
    item.delete()
    return redirect("sale", identifier.id)

def payment(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        sum = 0
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
        }
        return render(request, "payment/payment.html", context)
    else:
        return redirect("login")

def sale_input_cash(request, identifier_id, client_id, cashback_off):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        shop = registers[0].shop
        shop = Shop.objects.get(name=shop)
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            dateTime = request.POST["dateTime"]
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            if imeis:
                if dateTime:
                    # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                    dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                else:
                    dateTime = datetime.now()
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    sale_item = Sale.objects.create(
                        document=document,
                        category=product.category,
                        created=dateTime,
                        shop=shop,
                        name=names[i],
                        imei=imeis[i],
                        price=prices[i],
                        quantity=quantities[i],
                        sub_total=int(quantities[i]) * int(prices[i]),
                    )
                    # cashback calculations
                    if client.f_name != "default":
                        cashback = Cashback.objects.get(category=product.category)
                        client.accum_cashback += (
                            decimal.Decimal(sale_item.sub_total / 100) * cashback.size
                        )
                        client.save()
                    document_sum += sale_item.sub_total
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        remainder_current.save()
                    else:
                        messages.error(
                            request, "Данное наименование отсутствует на данном складе."
                        )
                        return redirect("sale", identifier.id)
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        rho_type=doc_type,
                        user=request.user,
                        shop=shop,
                        product_id=product,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        retail_price=prices[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        - int(quantities[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()
                    AvPrice.objects.filter(imei=imeis[i])
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()

                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
                        )
                        sequence_rhos_after = sequence_rhos_after.all().order_by(
                            "created"
                        )
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

                document.sum = document_sum
                document.save()
                sum_to_pay = document_sum - cashback_off

                # operations with cash
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    chos = Cash.objects.filter(
                        shop=shop, created__lt=dateTime
                    )  # cash history objects
                    cho_before = chos.latest("created")  # cash history object
                    cash_pre_remainder = cho_before.current_remainder
                else:
                    cash_pre_remainder = 0
                cash = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    user=request.user,
                    pre_remainder=cash_pre_remainder,
                    cash_in=sum_to_pay,
                    current_remainder=cash_pre_remainder + document_sum,
                )
                if CashRemainder.objects.filter(shop=shop).exists():
                    cash_remainder = CashRemainder.objects.get(shop=shop)
                else:
                    cash_remainder = CashRemainder.objects.create(
                        shop=shop, remainder=0
                    )
                cash_remainder.remainder = cash.current_remainder
                cash_remainder.save()
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(
                        shop=shop, created__gt=document.created
                    )
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder.remainder
                        obj.current_remainder = (
                            cash_remainder.remainder + obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder.remainder = obj.current_remainder
                        cash_remainder.save()
                # end of operations with cash

                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def sale_input_credit(request, identifier_id, client_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        client = Customer.objects.get(id=client_id)
        registers = Register.objects.filter(identifier=identifier)
        shop = registers[0].shop
        shop = Shop.objects.get(name=shop)
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            dateTime = request.POST["dateTime"]
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            if imeis:
                if dateTime:
                    # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                    dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                else:
                    dateTime = datetime.now()
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    sale_item = Sale.objects.create(
                        document=document,
                        category=product.category,
                        created=dateTime,
                        shop=shop,
                        name=names[i],
                        imei=imeis[i],
                        price=prices[i],
                        quantity=quantities[i],
                        sub_total=int(quantities[i]) * int(prices[i]),
                    )
                    if client.f_name != "default":
                        cashback = Cashback.objects.get(category=product.category)
                        client.accum_cashback += (
                            decimal.Decimal(sale_item.sub_total / 100) * cashback.size
                        )
                        client.save()
                    document_sum += sale_item.sub_total
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        remainder_current.save()
                    else:
                        messages.error(
                            request, "Данное наименование отсутствует на данном складе."
                        )
                        return redirect("sale", identifier.id)
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        retail_price=prices[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        - int(quantities[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()
                    AvPrice.objects.filter(imei=imeis[i])
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
                        )
                        sequence_rhos_after = sequence_rhos_after.all().order_by(
                            "created"
                        )
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
                document.sum = document_sum
                document.save()
                credit = Credit.objects.create(
                    shop=shop, document=document, user=request.user, sum=document.sum
                )
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")
            else:
                print("error")
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def sale_input_card(request, identifier_id, client_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        client = Customer.objects.get(id=client_id)
        shop = registers[0].shop
        shop = Shop.objects.get(name=shop)
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            dateTime = request.POST["dateTime"]
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            if imeis:
                if dateTime:
                    # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                    dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                else:
                    dateTime = datetime.now()
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    sale_item = Sale.objects.create(
                        document=document,
                        # category=category,
                        created=dateTime,
                        shop=shop,
                        name=names[i],
                        imei=imeis[i],
                        price=prices[i],
                        quantity=quantities[i],
                        sub_total=int(quantities[i]) * int(prices[i]),
                    )
                    if client.f_name != "default":
                        cashback = Cashback.objects.get(category=product.category)
                        client.accum_cashback += (
                            decimal.Decimal(sale_item.sub_total / 100) * cashback.size
                        )
                        client.save()
                    document_sum += sale_item.sub_total
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        remainder_current.save()
                    else:
                        messages.error(
                            request, "Данное наименование отсутствует на данном складе."
                        )
                        return redirect("sale", identifier.id)
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        retail_price=prices[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        - int(quantities[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()
                    AvPrice.objects.filter(imei=imeis[i])
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
                        )
                        sequence_rhos_after = sequence_rhos_after.all().order_by(
                            "created"
                        )
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
                document.sum = document_sum
                document.save()
                card = Card.objects.create(
                    created=dateTime,
                    shop=shop,
                    document=document,
                    user=request.user,
                    sum=document.sum,
                )
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")
            else:
                print("error")
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def pre_change_sale(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document)
    shop_current = rhos.first().shop
    identifier = Identifier.objects.create()
    for rho in rhos:
        product = Product.objects.get(imei=rho.imei)
        register = Register.objects.create(
            product=product,
            quantity=rho.outgoing_quantity,
            price=rho.retail_price,
            identifier=identifier,
            sub_total=rho.retail_price * rho.outgoing_quantity,
        )
    return redirect("change_sale", document.id, identifier.id)

def change_sale(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
    creator = document.user
    identifier = Identifier.objects.get(id=identifier_id)
    rhos = RemainderHistory.objects.filter(document=document)
    # sales=Sale.objects.filter(document=document)
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    registers = Register.objects.filter(identifier=identifier)
    if Cash.objects.filter(document=document).exists():
        cash = Cash.objects.get(document=document)
    else:
        cash = None
    if Card.objects.filter(document=document).exists():
        card = Card.objects.get(document=document)
    else:
        card = None
    if Credit.objects.filter(document=document).exists():
        credit = Credit.objects.get(document=document)
    else:
        credit = None
    if request.method == "POST":
        cash_new = request.POST["cash"]
        # if not card_new:
        if cash_new:
            cash_new = int(cash_new)
        else:
            cash_new = 0
        card_new = request.POST["card"]
        if card_new:
            card_new = int(card_new)
        else:
            card_new = 0
        credit_new = request.POST["credit"]
        if credit_new:
            credit_new = int(credit_new)
        else:
            credit_new = 0
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        names = request.POST.getlist("name", None)
        imeis = request.POST.getlist("imei", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        # deleting current rhos
        for rho in rhos:
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
                remainder_current.current_remainder = (
                    rho_latest_before.current_remainder
                )
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

        if imeis:
            n = len(names)
            document_sum = 0
            for i in range(n):
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=dateTime
                ).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    )
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_current = RemainderCurrent.objects.get(
                        shop=shop, imei=imeis[i]
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    # remainder_current.av_price=remainder_history.av_price
                    # remainder_current.total_av_price=remainder_history.sub_total
                    remainder_current.save()
                else:
                    if RemainderCurrent.objects.filter(
                        imei=imeis[i], shop=shop
                    ).exists():
                        remainder_current = RemainderCurrent.objects.get(
                            imei=imeis[i], shop=shop
                        )
                        remainder_current.current_remainder = 0
                        # remainder_current.av_price=0
                        # remainder_current.total_av_price=0
                        remainder_current.save()

                    else:
                        remainder_current = RemainderCurrent.objects.create(
                            updated=dateTime,
                            shop=shop,
                            imei=imeis[i],
                            name=names[i],
                            current_remainder=0,
                            # av_price=0,
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
                    outgoing_quantity=quantities[i],
                    current_remainder=remainder_current.current_remainder
                    + int(quantities[i]),
                    retail_price=int(prices[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )
                document_sum += remainder_history.sub_total
                remainder_current.current_remainder = (
                    remainder_history.current_remainder
                )
                remainder_current.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=document.created
                ).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
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
        else:
            identifier.delete()
            return redirect("delete_sale_input", document.id)
        # card operations
        check_sum = credit_new + cash_new + card_new
        if check_sum == document_sum:

            if card:
                card.delete()
            if card_new and card_new != 0:
                card_new_obj = Card.objects.create(
                    created=dateTime,
                    document=document,
                    user=creator,
                    shop=shop,
                    sum=card_new,
                )
            # credit operations
            if credit:
                credit.delete()
            if credit_new and credit_new != 0:
                credit_new_obj = Credit.objects.create(
                    created=dateTime,
                    document=document,
                    user=creator,
                    shop=shop,
                    sum=credit_new,
                )
            # operations with cash
            # deleting cash
            if cash:
                if Cash.objects.filter(
                    shop=shop, created__lt=document.created
                ).exists():
                    chos = Cash.objects.filter(
                        shop=shop_current, created__lt=document.created
                    )  # cash history objects
                    cho_before = chos.latest("created")  # cash history object
                    cash_remainder = CashRemainder.objects.get(shop=shop_current)
                    cash_remainder.remainder = cho_before.current_remainder
                else:
                    if CashRemainder.objects.filter(shop=shop_current).exists():
                        cash_remainder = CashRemainder.objects.get(shop=shop_current)
                        cash_remainder.remainder = 0
                    else:
                        cash_remainder = CashRemainder.objects.create(
                            shop=shop_current, remainder=0
                        )
                if Cash.objects.filter(
                    shop=shop_current, created__gt=document.created
                ).exists():
                    sequence_chos_after = Cash.objects.filter(
                        shop=shop_current, created__gt=document.created
                    )
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    for obj in sequence_chos_after:
                        obj.pre_remainder = remainder_current.current_remainder
                        obj.current_remainder = (
                            remainder_current.current_remainder
                            + obj.cash_in
                            - obj.cash_out
                        )
                        obj.save()
                        cash_remainder.remainder = obj.current_remainder
                        cash_remainder.save()
                cash.delete()
            # creating cash
            if cash_new and cash_new != 0:
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    chos = Cash.objects.filter(
                        shop=shop, created__lt=dateTime
                    )  # cash history objects
                    cho_before = chos.latest("created")  # cash history object
                    cash_remainder = CashRemainder.objects.get(shop=shop)
                    cash_remainder.remainder = cho_before.current_remainder
                else:
                    if CashRemainder.objects.filter(shop=shop).exists():
                        cash_remainder = CashRemainder.objects.get(shop=shop)
                        cash_remainder.remainder = 0
                        cash_remainder.save()
                    else:
                        cash_remainder = CashRemainder.objects.create(
                            shop=shop, remainder=0
                        )

                cash_new_obj = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    user=request.user,
                    pre_remainder=cash_remainder.remainder,
                    cash_in=cash_new,
                    current_remainder=cash_remainder.remainder + int(cash_new),
                )
                cash_remainder.remainder = cash_new_obj.current_remainder
                cash_remainder.save()
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(
                        shop=shop, created__gt=document.created
                    )
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder.remainder
                        obj.current_remainder = (
                            cash_remainder.remainder + obj.cash_in - obj.cash_out
                        )
                        obj.save()
                        cash_remainder.remainder = obj.current_remainder
                        cash_remainder.save()
                # end of operations with cash
        else:
            messages.error(
                request, "Сумма товара не соответствует вносимым денежным средствам"
            )
            return redirect("change_sale", document_id, identifier_id)

        document.sum = document_sum
        document.created = dateTime
        document.save()
        for register in registers:
            register.delete()
        identifier.delete()
        return redirect("log")
    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
            "shop_current": shop_current,
            "identifier": identifier,
            "cash": cash,
            "card": card,
            "credit": credit,
        }
        return render(request, "documents/change_sale.html", context)

def check_sale_change(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document)
    shop = rhos.first().shop
    identifier = Identifier.objects.get(id=identifier_id)
    # shops=Shop.objects.all()
    # if imei in request.GET:
    #     imei=request.GET['imei']
    #     if imei:
    if request.method == "POST":
        # try:
        #     shop=request.POST['shop']
        # except:
        #     messages.error(request, 'Введите ТТ, откуда осуществляется продажа')
        #     return redirect ('change_sale', document.id, identifier.id)
        imei = request.POST["imei"]
        # quantity=request.POST['quantity']
        # quantity=int(quantity)
        # shop=Shop.objects.get(id=shop)
        # if Product.objects.filter(imei=imei).exists():
        #     if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
        #         remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
        #         if remainder_current.current_remainder < quantity:
        #             messages.error(request, 'Количество, необходимое для продажи отсутствует на данном складе')
        #             return redirect ('sale', identifier.id)
        #         else:
        try:
            remainder_current = RemainderCurrent.objects.get(imei=imei, shop=shop)
        except:
            messages.error(
                request, "Данное наименование для продажи отсутствует в базе данных"
            )
            return redirect("change_sale", document.id, identifier.id)
        product = Product.objects.get(imei=imei)
        if Register.objects.filter(identifier=identifier, product=product).exists():
            register = Register.objects.get(identifier=identifier, product=product)
            register.quantity += 1
            register.save()
            register.sub_total = register.price * register.quantity
            register.save()
            return redirect("change_sale", document.id, identifier.id)
        else:
            register = Register.objects.create(
                shop=shop,
                quantity=1,
                identifier=identifier,
                product=product,
                price=remainder_current.retail_price,
                sub_total=1 * remainder_current.retail_price,
            )
        return redirect("change_sale", document.id, identifier.id)
        #     else:
        #         messages.error(request, 'Данное наименование для продажи отсутствует на данном складе')
        #         return redirect ('change_sale', document.id, identifier.id)
        # else:
        #     messages.error(request, 'Данное наименование для продажи отсутствует в базе данных')
        #     return redirect ('sale', identifier.id)

def delete_line_change_sale(request, document_id, identifier_id, imei):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(identifier=identifier, product=product)
    item.delete()
    # for item in items:
    #     item.delete()
    return redirect("change_sale", document.id, identifier.id)

def sale_input_complex(request, identifier_id, client_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        client = Customer.objects.get(id=client_id)
        shop = registers[0].shop
        shop = Shop.objects.get(name=shop)
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        if request.method == "POST":
            dateTime = request.POST["dateTime"]
            cash = request.POST["cash"]
            # cash=int(cash)
            credit = request.POST["credit"]
            # credit=int(credit)
            card = request.POST["card"]
            # card=int(card)
            # category=request.POST['category']
            imeis = request.POST.getlist("imei", None)
            names = request.POST.getlist("name", None)
            quantities = request.POST.getlist("quantity", None)
            prices = request.POST.getlist("price", None)
            if imeis:
                if dateTime:
                    # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                    dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
                else:
                    dateTime = datetime.now()
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    sale_item = Sale.objects.create(
                        document=document,
                        category=product.category,
                        created=dateTime,
                        shop=shop,
                        name=names[i],
                        imei=imeis[i],
                        price=prices[i],
                        quantity=quantities[i],
                        sub_total=int(quantities[i]) * int(prices[i]),
                    )
                    if client.f_name != "default":
                        cashback = Cashback.objects.get(category=product.category)
                        client.accum_cashback += (
                            decimal.Decimal(sale_item.sub_total / 100) * cashback.size
                        )
                        client.save()
                    document_sum += sale_item.sub_total
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        remainder_current.save()
                    else:
                        messages.error(
                            request, "Данное наименование отсутствует на данном складе."
                        )
                        return redirect("sale", identifier.id)
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
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        - int(quantities[i]),
                        # sub_total= int(int(quantities[i]) * int(prices[i])),
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()
                    AvPrice.objects.filter(imei=imeis[i])
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    av_price_obj.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
                        )
                        sequence_rhos_after = sequence_rhos_after.all().order_by(
                            "created"
                        )
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
                document.sum = document_sum
                document.save()
                sum = int(cash) + int(credit) + int(card)
                if sum != document_sum:
                    print("error")
                    messages.error(
                        request, "Сумма в чеке не совпадает с суммой продажи."
                    )
                    return redirect("sale", identifier.id)
                # operations with cash
                if cash:
                    if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                        chos = Cash.objects.filter(
                            shop=shop, created__lt=dateTime
                        )  # cash history objects
                        cho_before = chos.latest("created")  # cash history object
                        cash_pre_remainder = cho_before.current_remainder
                    else:
                        cash_pre_remainder = 0
                    cash = Cash.objects.create(
                        shop=shop,
                        created=dateTime,
                        document=document,
                        user=request.user,
                        pre_remainder=cash_pre_remainder,
                        cash_in=cash,
                        current_remainder=cash_pre_remainder + int(cash),
                    )
                    if CashRemainder.objects.filter(shop=shop).exists():
                        cash_remainder = CashRemainder.objects.get(shop=shop)
                    else:
                        cash_remainder = CashRemainder.objects.create(
                            shop=shop, remainder=0
                        )
                    cash_remainder.remainder = cash.current_remainder
                    cash_remainder.save()
                    if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                        sequence_chos_after = Cash.objects.filter(
                            shop=shop, created__gt=document.created
                        )
                        sequence_chos_after = sequence_chos_after.all().order_by(
                            "created"
                        )
                        for obj in sequence_chos_after:
                            obj.pre_remainder = cash_remainder.remainder
                            obj.current_remainder = (
                                cash_remainder.remainder + obj.cash_in - obj.cash_out
                            )
                            obj.save()
                            cash_remainder.remainder = obj.current_remainder
                            cash_remainder.save()
                    # end of operations with cash

                if card:
                    card = Card.objects.create(
                        shop=shop, document=document, user=request.user, sum=card
                    )
                if credit:
                    credit = Credit.objects.create(
                        shop=shop, document=document, user=request.user, sum=credit
                    )
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")

            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("sale", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def delete_sale_input(request, document_id):
    document = Document.objects.get(id=document_id)
    sales = Sale.objects.filter(document=document)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price_obj = AvPrice.objects.get(imei=rho.imei)
        av_price_obj.current_remainder += rho.outgoing_quantity
        av_price_obj.sum += rho.outgoing_quantity * av_price_obj.av_price
        av_price_obj.save()

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
    for sale in sales:
        sale.delete()

    if Cash.objects.filter(document=document):
        cho = Cash.objects.get(document=document)
        # for cho in cash_history_objects:
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            sequence_chos_before = Cash.objects.filter(
                shop=cho.shop, created__lt=cho.created
            )
            cho_latest_before = sequence_chos_before.latest("created")
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = cho_latest_before.current_remainder
            cash_remainder.save()
        else:
            cash_remainder = CashRemainder.objects.get()
            cash_remainder.remainder = 0
            cash_remainder.save()

        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            sequence_chos_after = Cash.objects.filter(
                shop=cho.shop, created__gt=cho.created
            )
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
        cho.delete()
    if Card.objects.filter(document=document).exists():
        cho = Card.objects.get(document=document)  # card history object
        cho.delete()
    if Credit.objects.filter(document=document).exists():
        cho = Credit.objects.get(document=document)  # credit history object
        cho.delete()

    document.delete()
    return redirect("log")

# ====================================Delivery Operations==============================================
def delivery_auto(request):
    shops = Shop.objects.all()
    suppliers = Supplier.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    if request.method == "POST":
        dateTime = request.POST["dateTime"]
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        # print(file)
        # df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        document = Document.objects.create(
            created=dateTime, user=request.user, title=doc_type
        )
        document_sum = 0
        for i in range(cycle):
            row = df1.iloc[i]
            print(row.Imei)
            try:
                Product.objects.get(imei=row.Imei)
            except Product.DoesNotExist:
                product = Product.objects.create(
                    imei=row.Imei, category=category, name=row.Title
                )
            product = Product.objects.get(imei=row.Imei)
            delivery_item = Delivery.objects.create(
                document=document,
                # category=category,
                created=dateTime,
                supplier=supplier,
                shop=shop,
                name=row.Title,
                imei=row.Imei,
                price=row.Price,
                quantity=row.Quantity,
                sub_total=int(row.Quantity) * int(row.Price),
            )
            # checking docs before remainder_history
            if RemainderHistory.objects.filter(
                imei=row.Imei, shop=shop, created__lt=dateTime
            ).exists():
                sequence_rhos_before = RemainderHistory.objects.filter(
                    imei=row.Imei, shop=shop, created__lt=dateTime
                )
                remainder_history = sequence_rhos_before.latest("created")
                remainder_current = RemainderCurrent.objects.get(
                    shop=shop, imei=row.Imei
                )
                remainder_current.current_remainder = (
                    remainder_history.current_remainder
                )
                # remainder_current.av_price=remainder_history.av_price
                # remainder_current.total_av_price=remainder_history.sub_total
                remainder_current.save()
            else:
                if RemainderCurrent.objects.filter(imei=row.Imei, shop=shop).exists():
                    remainder_current = RemainderCurrent.objects.get(
                        imei=row.Imei, shop=shop
                    )
                    remainder_current.current_remainder = 0
                    # remainder_current.av_price=0
                    # remainder_current.total_av_price=0
                    remainder_current.save()
                else:
                    remainder_current = RemainderCurrent.objects.create(
                        # updated=dateTime,
                        shop=shop,
                        imei=row.Imei,
                        name=row.Title,
                        current_remainder=0,
                        # av_price=0,
                        # total_av_price=0
                    )
            # creating remainder_history
            remainder_history = RemainderHistory.objects.create(
                document=document,
                rho_type=document.title,
                created=dateTime,
                shop=shop,
                category=product.category,
                supplier=supplier,
                product_id=product.id,
                imei=row.Imei,
                name=row.Title,
                pre_remainder=remainder_current.current_remainder,
                incoming_quantity=row.Quantity,
                outgoing_quantity=0,
                current_remainder=remainder_current.current_remainder
                + int(row.Quantity),
                wholesale_price=int(row.Price),
                sub_total=int(row.Price) * int(row.Quantity),
            )
            document_sum += int(remainder_history.sub_total)
            remainder_current.current_remainder = remainder_history.current_remainder
            remainder_current.save()

            if AvPrice.objects.filter(imei=row.Imei).exists():
                av_price_obj = AvPrice.objects.get(imei=row.Imei)
                av_price_obj.current_remainder += int(row.Quantity)
                av_price_obj.sum += int(row.Quantity) * int(row.Price)
                av_price_obj.av_price = int(av_price_obj.sum) / int(
                    av_price_obj.current_remainder
                )
                av_price_obj.save()
            else:
                av_price_obj = AvPrice.objects.create(
                    name=row.Title,
                    imei=row.Imei,
                    current_remainder=int(row.Quantity),
                    sum=int(row.Quantity) * int(row.Price),
                    av_price=int(row.Price),
                )
            # checking docs after remainder_history
            if RemainderHistory.objects.filter(
                imei=row.Imei, shop=shop, created__gt=dateTime
            ).exists():
                sequence_rhos_after = RemainderHistory.objects.filter(
                    imei=row.Imei, shop=shop, created__gt=dateTime
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

        document.sum = document_sum
        document.save()
        return redirect("log")

    context = {"shops": shops, "suppliers": suppliers, "categories": categories}
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
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("delivery", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, product=product
                )
                return redirect("delivery", identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("delivery", identifier.id)

def check_delivery_change(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(
                document=document, product=product, deleted=True
            ).exists():
                register = Register.objects.get(
                    document=document, product=product, deleted=True
                )
                register.deleted = False
                register.quantity = 1
                register.price = 0
                register.sub_total = 0
                register.save()
            elif Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_delivery_posted", document.id)
            else:
                register = Register.objects.create(document=document, product=product)
            return redirect("change_delivery_posted", document.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("change_delivery_posted", document.id)

def check_delivery_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=False).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_delivery_unposted", document.id)
            elif Register.objects.filter(
                document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                register.save()
                return redirect("change_delivery_unposted", document.id)
            else:
                register = Register.objects.create(
                    document=document, product=product, new=True
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
    shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier).order_by("created")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "suppliers": suppliers,
        "shops": shops,
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

def delete_line_change_delivery(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.deleted = True
    item.save()
    return redirect("change_delivery_posted", document.id)

def delete_line_unposted_delivery(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.deleted = True
    item.save()
    return redirect("change_delivery_unposted", document.id)

def enter_new_product(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
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

def enter_new_product_from_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)

        if Product.objects.filter(imei=imei).exists():
            messages.error(
                request,
                "Наименование в базу данных не введено, так как IMEI не является уникальным",
            )
            return redirect("change_delivery_posted", document.id)
        else:
            product = Product.objects.create(
                name=name,
                imei=imei,
                category=category,
            )
            return redirect("change_delivery_posted", document.id)

def delivery_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier).order_by("created")
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        sub_totals = request.POST.getlist("sub_total", None)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
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
        # posting delivery document
        if post_check == True:
            if imeis:
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime, posted=True
                )

                n = len(names)
                document_sum = 0
                for i in range(n):
                    # imei=imeis[i]
                    product = Product.objects.get(imei=imeis[i])
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(
                            imei=imeis[i], shop=shop
                        ).exists():
                            remainder_current = RemainderCurrent.objects.get(
                                imei=imeis[i], shop=shop
                            )
                            remainder_current.current_remainder = 0
                            # remainder_current.av_price=0
                            # remainder_current.total_av_price=0
                            remainder_current.save()
                        else:
                            remainder_current = RemainderCurrent.objects.create(
                                # updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                category=product.category,
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        supplier=supplier,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    document_sum += remainder_history.sub_total
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()

                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        av_price_obj.av_price = (
                            av_price_obj.sum / av_price_obj.current_remainder
                        )
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )

                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
                        )
                        sequence_rhos_after = sequence_rhos_after.all().order_by(
                            "created"
                        )
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

                document.sum = document_sum
                document.save()
                register = Register.objects.get(identifier=identifier, product=product)
                register.delete()
                identifier.delete()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("delivery", identifier.id)
        # saving uposted delivery document
        else:
            if imeis:
                document = Document.objects.create(
                    title=doc_type, user=request.user, created=dateTime, posted=False
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(
                        identifier=identifier, product=product
                    )
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.supplier = supplier
                    register.shop = shop
                    register.new = False
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum += int(register.sub_total)
                document.sum = document_sum
                document.save()
                identifier.delete()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("delivery", identifier.id)

def change_delivery_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    suppliers = Supplier.objects.all()
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    if Register.objects.filter(document=document).exists():
        registers = (
            Register.objects.filter(document=document)
            .exclude(deleted=True)
            .order_by("created")
        )
    else:
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # creating new registers
            register = Register.objects.create(
                shop=shop_current,
                supplier=rho.supplier,
                product=product,
                quantity=rho.incoming_quantity,
                price=rho.wholesale_price,
                document=document,
                sub_total=rho.wholesale_price * rho.incoming_quantity,
            )
        registers = Register.objects.filter(document=document).order_by("created")

    numbers = registers.exclude(deleted=True).count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()

    if request.method == "POST":
        try:
            supplier = request.POST["supplier"]
            supplier = Supplier.objects.get(id=supplier)
        except:
            messages.error(request, "Введите поставщика")
            return redirect("change_delivery_posted", document.id)
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        names = request.POST.getlist("name", None)
        imeis = request.POST.getlist("imei", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        if Register.objects.filter(document=document, deleted=True).exists():
            deleted_registers = Register.objects.filter(document=document, deleted=True)
            for del_reg in deleted_registers:
                del_reg.delete()

        for rho in rhos:
            # deleting current rhos
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
                remainder_current.current_remainder = (
                    rho_latest_before.current_remainder
                )
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

        # creating new rhos & deleting registers
        if imeis:
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()

            n = len(names)
            document_sum = 0
            for i in range(n):
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=dateTime
                ).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    )
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_current = RemainderCurrent.objects.get(
                        shop=shop, imei=imeis[i]
                    )
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    # remainder_current.av_price=remainder_history.av_price
                    # remainder_current.total_av_price=remainder_history.sub_total
                    remainder_current.save()
                else:
                    if RemainderCurrent.objects.filter(
                        imei=imeis[i], shop=shop
                    ).exists():
                        remainder_current = RemainderCurrent.objects.get(
                            imei=imeis[i], shop=shop
                        )
                        remainder_current.current_remainder = 0
                        # remainder_current.av_price=0
                        # remainder_current.total_av_price=0
                        remainder_current.save()

                    else:
                        remainder_current = RemainderCurrent.objects.create(
                            updated=dateTime,
                            shop=shop,
                            imei=imeis[i],
                            name=names[i],
                            current_remainder=0,
                            # av_price=0,
                            # total_av_price=0
                        )
                remainder_history = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    # category=category,
                    supplier=supplier,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=remainder_current.current_remainder
                    + int(quantities[i]),
                    wholesale_price=int(prices[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i])),
                )
                document_sum += remainder_history.sub_total
                remainder_current.current_remainder = (
                    remainder_history.current_remainder
                )
                remainder_current.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=document.created
                ).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
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

            document.sum = document_sum
            document.created = dateTime
            document.save()
            for register in registers:
                register.delete()
            return redirect("log")

        else:
            messages.error(request, "Вы не ввели ни одного наименования")
            return redirect("change_delivery_posted", document.id)
    else:
        context = {
            "registers": registers,
            "suppliers": suppliers,
            "document": document,
            "shops": shops,
            "suppliers": suppliers,
            "categories": categories,
        }
        return render(request, "documents/change_delivery_posted.html", context)

def change_delivery_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        sub_totals = request.POST.getlist("sub_total", None)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            supplier = request.POST["supplier"]
        except:
            messages.error(request, "Введите поставщика")
            return redirect("change_delivery_unposted", document.id)
        supplier = Supplier.objects.get(id=supplier)
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        # posting the document
        if post_check == True:
            if imeis:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(
                            imei=imeis[i], shop=shop
                        ).exists():
                            remainder_current = RemainderCurrent.objects.get(
                                imei=imeis[i], shop=shop
                            )
                            remainder_current.current_remainder = 0
                            # remainder_current.av_price=0
                            # remainder_current.total_av_price=0
                            remainder_current.save()

                        else:
                            remainder_current = RemainderCurrent.objects.create(
                                # updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                category=product.category,
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        supplier=supplier,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    document_sum += remainder_history.sub_total
                    remainder_current.current_remainder = (remainder_history.current_remainder)
                    remainder_current.save()

                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        av_price_obj.av_price = (av_price_obj.sum / av_price_obj.current_remainder)
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )

                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
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

                document.sum = document_sum
                document.posted = True
                document.save()
                registers = Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_delivery_unposted", document.id)
        # saving uposted document
        else:
            if imeis:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    if Register.objects.filter(
                        document=document, product=product, deleted=True
                    ).exists():
                        register = Register.objects.filter(
                            document=document, product=product, deleted=True
                        )
                        register.delete()
                    else:
                        register = Register.objects.get(
                            document=document, product=product
                        )
                        register.price = prices[i]
                        register.quantity = quantities[i]
                        register.sub_total = sub_totals[i]
                        register.document = document
                        register.supplier = supplier
                        register.shop = shop
                        register.new = False
                        register.save()
                        document_sum += int(register.sub_total)
                document.sum = document_sum
                document.save()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_delivery_unposted", document.id)

    else:
        context = {
            "registers": registers,
            "shops": shops,
            "suppliers": suppliers,
            "document": document,
            "categories": categories,
        }

    return render(request, "documents/change_delivery_unposted.html", context)

def unpost_delivery(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    shop_current = rhos.first().shop
    supplier = rhos.first().supplier
    for rho in rhos:
        product = Product.objects.get(imei=rho.imei)
        # deleting existing rhos
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
        document.posted = False
        document.save()
    return redirect("log")

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
    if "check_imei" in request.GET:
        imei = request.GET["check_imei"]
        shop = request.GET["shop"]
        shop = Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
                remainder_current = RemainderCurrent.objects.get(imei=imei, shop=shop)
                product = Product.objects.get(imei=imei)
                if Register.objects.filter(
                    identifier=identifier, product=product
                ).exists():
                    register = Register.objects.get(
                        identifier=identifier, product=product
                    )
                    register.quantity += 1
                    register.save()
                    register.sub_total = remainder_current.retail_price
                    return redirect("transfer", identifier.id)
                else:
                    register = Register.objects.create(
                        product=product,
                        identifier=identifier,
                        price=remainder_current.retail_price,
                        quantity=1,
                    )
                    register.sub_total = (
                        register.quantity * remainder_current.retail_price
                    )
                    return redirect("transfer", identifier.id)
            else:
                messages.error(
                    request, "Данное наименование отсутствует на данном складе"
                )
                return redirect("transfer", identifier.id)
        else:
            messages.error(request, "Данное наименование отсутствует в базе данных")
            return redirect("transfer", identifier.id)
    else:
        return redirect("transfer", identifier.id)

def check_transfer_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    shop_sender = registers.first().shop_sender
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei_check"]
        quantity = request.POST["quantity_input"]
        quantity = int(quantity)
        # price=request.POST['price']
        # price=int(price)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(shop=shop_sender, imei=imei).exists():
                remainder_current = RemainderCurrent.objects.get(
                    shop=shop_sender, imei=imei
                )
                if remainder_current.current_remainder >= quantity:
                    product = Product.objects.get(imei=imei)
                    if Register.objects.filter(
                        document=document, product=product
                    ).exists():
                        register = Register.objects.get(
                            document=document, product=product
                        )
                        register.quantity += quantity
                        register.save()
                        return redirect("change_transfer_posted", document.id)
                    else:
                        register = Register.objects.create(
                            document=document,
                            product=product,
                            quantity=quantity,
                            new=True
                            # price=retail_price,
                        )
                        register.sub_total = register.quantity * register.price
                        register.save()
                        return redirect("change_transfer_posted", document.id)
                else:
                    messages.error(
                        request,
                        "Необходимое количество отсутствует на складе фирмы-отправителя",
                    )
                    return redirect("change_transfer_posted", document.id)
            else:
                messages.error(
                    request,
                    "Данное наименование отсутствует на складе фирмы-отправителя",
                )
                return redirect("change_transfer_posted", document.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("change_transfer_posted", document.id)

def check_transfer_unposted(request, document_id):
    shops = Shop.objects.all()
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    shop_sender = registers.first().shop_sender
    if "imei_check" in request.GET:
        imei = request.GET["imei_check"]
        quantity = request.GET["quantity_input"]
        # shop = request.GET["shop"]
        # shop = Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(imei=imei, shop=shop_sender).exists():
                remainder_current = RemainderCurrent.objects.get(
                    imei=imei, shop=shop_sender
                )
                if remainder_current.current_remainder >= int(quantity):
                    product = Product.objects.get(imei=imei)
                    if Register.objects.filter(
                        document=document, product=product
                    ).exists():
                        register = Register.objects.get(
                            document=document, product=product
                        )
                        register.quantity += 1
                        register.save()
                        register.sub_total = remainder_current.retail_price
                        return redirect("change_transfer_unposted", document.id)
                    else:
                        register = Register.objects.create(
                            product=product,
                            document=document,
                            price=remainder_current.retail_price,
                            quantity=1,
                            new=True,
                        )
                        # register.sub_total = (
                        #     register.quantity * remainder_current.retail_price
                        # )
                        return redirect("change_transfer_unposted", document.id)
                else:
                    messages.error(
                        request,
                        "На складе фирмы-отправителя отсутствует необходимое количество",
                    )
                    return redirect("change_transfer_unposted", document.id)
            else:
                messages.error(
                    request, "Данное наименование отсутствует на данном складе"
                )
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
    register.deleted = True
    register.save()
    return redirect("change_transfer_unposted", document.id)

def delete_line_posted_transfer(request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    register = Register.objects.get(document=document, product=product)
    register.deleted = True
    register.save()
    return redirect("change_transfer_posted", document.id)

def transfer_input(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
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
            # shop_sender = request.POST["shop_sender"]
            shop_receiver = request.POST["shop_receiver"]
            dateTime = request.POST["dateTime"]
            try:
                shop_sender = request.POST["shop_sender"]
                shop_sender = Shop.objects.get(id=shop_sender)
            except:
                messages.error(request, "Введите фирму-отправитель")
                return redirect("transfer", identifier.id)
            try:
                shop_receiver = request.POST["shop_receiver"]
                shop_receiver = Shop.objects.get(id=shop_receiver)
            except:
                messages.error(request, "Введите фирму-получатель")
                return redirect("transfer", identifier.id)
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()
            if shop_sender == shop_receiver:
                messages.error(
                    request,
                    "Документ не проведен. Выберите фирму получателя отличную от отправителя",
                )
                return redirect("transfer", identifier.id)
            else:
                # checking posting (version 1)
                # x = request.POST.get('post_check')
                # if x == 'on':
                # checking posting (version 2)
                try:
                    if request.POST["post_check"]:
                        post_check = True
                except KeyError:
                    post_check = False

                # posting transfer document
                if post_check == True:
                    check_point = []
                    n = len(names)
                    for i in range(n):
                        if RemainderCurrent.objects.filter(
                            imei=imeis[i], shop=shop_sender
                        ).exists():
                            remainder_current_sender = RemainderCurrent.objects.get(
                                imei=imeis[i], shop=shop_sender
                            )
                            if remainder_current_sender.current_remainder < int(
                                quantities[i]
                            ):
                                check_point.append(False)
                            else:
                                check_point.append(True)
                        else:
                            check_point.append(False)
                    if False in check_point:
                        messages.error(
                            request,
                            "Документ не проведен. Одно или несколько наименование отсутствуют на балансе данной фирмы.",
                        )
                        return redirect("transfer", identifier.id)
                    else:
                        document = Document.objects.create(
                            created=dateTime,
                            title=doc_type,
                            user=request.user,
                            posted=True,
                        )
                        sum = 0
                        for i in range(n):
                            sum += int(prices[i]) * int(quantities[i])
                            # checking shop_sender
                            if RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__lt=dateTime
                            ).exists():
                                sequence_rhos_before = RemainderHistory.objects.filter(
                                    imei=imeis[i],
                                    shop=shop_sender,
                                    created__lt=dateTime,
                                )
                                remainder_history = sequence_rhos_before.latest(
                                    "created"
                                )
                                remainder_current = RemainderCurrent.objects.get(
                                    shop=shop_sender, imei=imeis[i]
                                )
                                remainder_current.current_remainder = (
                                    remainder_history.current_remainder
                                )
                                # remainder_current.av_price=remainder_history.av_price
                                # remainder_current.total_av_price=remainder_history.sub_total
                                remainder_current.save()
                            else:
                                if RemainderCurrent.objects.filter(
                                    imei=imeis[i], shop=shop_sender
                                ).exists():
                                    remainder_current = RemainderCurrent.objects.get(
                                        shop=shop_sender, imei=imeis[i]
                                    )
                                    remainder_current.current_remainder = 0
                                    # remainder_current.av_price=0
                                    # remainder_current.total_av_price=0
                                    remainder_current.save()
                                else:
                                    remainder_current = RemainderCurrent.objects.create(
                                        imei=imeis[i],
                                        name=names[i],
                                        shop=shop_sender,
                                        # av_price=0,
                                        # total_av_price=0,
                                        current_remainder=0,
                                    )

                            remainder_history = RemainderHistory.objects.create(
                                created=dateTime,
                                document=document,
                                rho_type=document.title,
                                shop=shop_sender,
                                # category=category,
                                imei=imeis[i],
                                name=names[i],
                                # av_price=remainder_current.av_price,
                                retail_price=prices[i],
                                pre_remainder=remainder_current.current_remainder,
                                incoming_quantity=0,
                                outgoing_quantity=quantities[i],
                                current_remainder=remainder_current.current_remainder
                                - int(quantities[i]),
                                # sub_total=remainder_current.av_price*(remainder_current.current_remainder-int(quantities[i]))
                            )
                            remainder_current.current_remainder = (
                                remainder_history.current_remainder
                            )
                            # remainder_current.av_price=remainder_history.av_price
                            # remainder_current.total_av_price=remainder_history.sub_total
                            remainder_current.save()
                            # av_price_sender=remainder_history.av_price

                            # checking docs after remainder_history for shop_sender
                            if RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__gt=dateTime
                            ).exists():
                                sequence_rhos_after = RemainderHistory.objects.filter(
                                    imei=imeis[i],
                                    shop=shop_sender,
                                    created__gt=dateTime,
                                )
                                sequence_rhos_after = (
                                    sequence_rhos_after.all().order_by("created")
                                )
                                for obj in sequence_rhos_after:

                                    obj.pre_remainder = (
                                        remainder_current.current_remainder
                                    )
                                    obj.current_remainder = (
                                        remainder_current.current_remainder
                                        + obj.incoming_quantity
                                        - obj.outgoing_quantity
                                    )

                                    obj.save()
                                    remainder_current.current_remainder = (
                                        obj.current_remainder
                                    )
                                    remainder_current.save()

                            # checking shop_receiver
                            if RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__lt=dateTime
                            ).exists():
                                sequence_rhos_after = RemainderHistory.objects.filter(
                                    imei=imeis[i],
                                    shop=shop_receiver,
                                    created__lt=dateTime,
                                )
                                remainder_history = sequence_rhos_after.latest(
                                    "created"
                                )
                                remainder_current = RemainderCurrent.objects.get(
                                    shop=shop_receiver, imei=imeis[i]
                                )
                                remainder_current.current_remainder = (
                                    remainder_history.current_remainder
                                )
                                # remainder_current.av_price=remainder_history.av_price
                                # remainder_current.total_av_price=remainder_history.sub_total
                                remainder_current.save()
                            else:
                                if RemainderCurrent.objects.filter(
                                    imei=imeis[i], shop=shop_receiver
                                ).exists():
                                    remainder_current = RemainderCurrent.objects.get(
                                        shop=shop_receiver, imei=imeis[i]
                                    )
                                    remainder_current.current_remainder = 0
                                    # remainder_current.av_price=0
                                    # remainder_current.total_av_price=0
                                    remainder_current.save()
                                else:
                                    remainder_current = RemainderCurrent.objects.create(
                                        imei=imeis[i],
                                        name=names[i],
                                        shop=shop_receiver,
                                        # av_price=0,
                                        # total_av_price=0,
                                        current_remainder=0,
                                    )
                            remainder_history = RemainderHistory.objects.create(
                                created=dateTime,
                                document=document,
                                rho_type=document.title,
                                shop=shop_receiver,
                                # category=category,
                                imei=imeis[i],
                                name=names[i],
                                retail_price=prices[i],
                                pre_remainder=remainder_current.current_remainder,
                                incoming_quantity=quantities[i],
                                outgoing_quantity=0,
                                current_remainder=remainder_current.current_remainder
                                + int(quantities[i]),
                                status=True
                                # sub_total=remainder_current.total_av_price+av_price_sender*int(quantities[i]),
                                # av_price=(remainder_current.total_av_price+av_price_sender*int(quantities[i]))/(remainder_current.current_remainder+int(quantities[i]))
                            )

                            remainder_current.current_remainder = (
                                remainder_history.current_remainder
                            )
                            remainder_current.retail_price = (
                                remainder_history.retail_price
                            )
                            # remainder_current.total_av_price=remainder_history.sub_total
                            remainder_current.save()

                            # checking docs after remainder_history for shop_receiver
                            if RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__gt=dateTime
                            ).exists():
                                sequence_rhos_after = RemainderHistory.objects.filter(
                                    imei=imeis[i],
                                    shop=shop_receiver,
                                    created__gt=dateTime,
                                )
                                sequence_rhos_after = (
                                    sequence_rhos_after.all().order_by("created")
                                )
                                for obj in sequence_rhos_after:

                                    obj.pre_remainder = (
                                        remainder_current.current_remainder
                                    )
                                    obj.current_remainder = (
                                        remainder_current.current_remainder
                                        + obj.incoming_quantity
                                        - obj.outgoing_quantity
                                    )
                                    obj.save()
                                    remainder_current.current_remainder = (
                                        obj.current_remainder
                                    )
                                    # remainder_current.total_av_price=obj.sub_total
                                    # remainder_current.av_price=obj.av_price
                                    remainder_current.save()

                        document.sum = sum
                        document.save()
                        for register in registers:
                            register.delete()
                        identifier.delete()
                        return redirect("log")
                # saving unposted document
                else:
                    document = Document.objects.create(
                        title=doc_type,
                        user=request.user,
                        created=dateTime,
                        posted=False,
                    )
                    n = len(names)
                    sum = 0
                    for i in range(n):
                        sum += int(prices[i]) * int(quantities[i])
                        product = Product.objects.get(imei=imeis[i])
                        register = Register.objects.get(
                            identifier=identifier, product=product
                        )
                        register.price = prices[i]
                        register.quantity = quantities[i]
                        register.sub_total = int(prices[i]) * int(quantities[i])
                        register.document = document
                        register.shop_sender = shop_sender
                        register.shop_receiver = shop_receiver
                        register.new = False
                        register.identifier = None
                        register.save()
                    identifier.delete()
                    document.sum = sum
                    document.save()
                    return redirect("log")
        else:
            return redirect("transfer", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")

def change_transfer_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    rhos = RemainderHistory.objects.filter(document=document)
    if Register.objects.filter(document=document).exists():
        registers = (
            Register.objects.filter(document=document)
            .exclude(deleted=True)
            .order_by("created")
        )
    else:
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            if Register.objects.filter(document=document, product=product).exists():
                register = Register.objects.get(document=document, product=product)
                try:
                    if rho.status == False:
                        register.shop_sender = rho.shop
                    else:
                        register.shop_receiver = rho.shop
                except KeyError:
                    if rho.status == True:
                        register.shop_receiver = rho.shop
                    else:
                        register.shop_sender = rho.shop
                register.save()
            else:
                # creating new register
                if rho.status == False:
                    register = Register.objects.create(
                        shop_sender=rho.shop,
                        product=product,
                        quantity=rho.outgoing_quantity,
                        price=rho.retail_price,
                        document=document,
                        sub_total=rho.retail_price * rho.outgoing_quantity,
                    )
                else:
                    register = Register.objects.create(
                        shop_receiver=rho.shop,
                        product=product,
                        quantity=rho.incoming_quantity,
                        price=rho.retail_price,
                        document=document,
                        sub_total=rho.retail_price * rho.incoming_quantity,
                    )
        registers = Register.objects.filter(document=document).order_by("created")
        numbers = registers.count()
        for register, i in zip(registers, range(numbers)):
            register.number = i + 1
            register.save()
    shop_sender_current = registers.first().shop_sender
    shop_receiver_current = registers.first().shop_receiver

    if request.method == "POST":
        dateTime = request.POST["dateTime"]
        shop_sender = request.POST["shop_sender"]
        shop_sender_changed = Shop.objects.get(id=shop_sender)
        shop_receiver = request.POST["shop_receiver"]
        shop_receiver_changed = Shop.objects.get(id=shop_receiver)
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        sum = 0
        n = len(names)
        # checking if date has been changed
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = document.created

        for rho in rhos:
            # changing docs for receiver_shop. It comes before sender_shop since we'll need av_prices of sender_shop
            # deleting rho for shop_receiver_current
            if RemainderHistory.objects.filter(
                imei=rho.imei, shop=shop_receiver_current, created__lt=rho.created
            ).exists():
                remainder_current = RemainderCurrent.objects.get(
                    imei=rho.imei, shop=shop_receiver_current
                )
                # rho_before=RemainderHistory.objects.filter(imei=rho.imei, shop=shop_receiver_current, created__lt=rho.created).latest('created')
                rho_sequence_before = RemainderHistory.objects.filter(
                    imei=rho.imei, shop=shop_receiver_current, created__lt=rho.created
                )
                rho_before = rho_sequence_before.latest("created")
                remainder_current.current_remainder = rho_before.current_remainder
                # remainder_current.total_av_price=rho_before.sub_total
                # remainder_current.av_price=rho_before.av_price
                remainder_current.save()
            else:
                remainder_current = RemainderCurrent.objects.get(
                    imei=rho.imei, shop=shop_receiver_current
                )
                remainder_current.current_remainder = 0
                remainder_current.total_av_price = 0
                remainder_current.av_price = 0
                remainder_current.save()
            if RemainderHistory.objects.filter(
                imei=rho.imei, shop=shop_receiver_current, created__gt=rho.created
            ).exists():
                sequence_rhos = RemainderHistory.objects.filter(
                    imei=rho.imei, shop=shop_receiver_current, created__gt=rho.created
                )
                for obj in sequence_rhos:
                    obj.pre_remainder = remainder_current.current_remainder
                    # obj.sub_total=remainder_current.total_av_price+obj.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                    obj.current_remainder = (
                        remainder_current.current_remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    # obj.av_price=obj.sub_total/obj.current_remainder
                    obj.save()
                    remainder_current.current_remainder = obj.current_remainder
                    # remainder_current.total_av_price=obj.sub_total
                    # remainder_current.av_price=obj.av_price
                    remainder_current.save()
            # deleting rho for shop_sender_current
            if RemainderHistory.objects.filter(
                imei=rho.imei, shop=shop_sender_current, created__lt=rho.created
            ).exists():
                remainder_current = RemainderCurrent.objects.get(
                    imei=rho.imei, shop=shop_sender_current
                )
                rho_sequence_before = RemainderHistory.objects.filter(
                    imei=rho.imei, shop=shop_sender_current, created__lt=rho.created
                )
                rho_before = rho_sequence_before.latest("created")
                remainder_current.current_remainder = rho_before.current_remainder
                # remainder_current.total_av_price=rho_before.sub_total
                # remainder_current.av_price=rho_before.av_price
                remainder_current.save()
            else:
                remainder_current = RemainderCurrent.objects.get(
                    imei=rho.imei, shop=shop_sender_current
                )
                remainder_current.current_remainder = 0
                # remainder_current.total_av_price=0
                # remainder_current.av_price=0
                remainder_current.save()
            if RemainderHistory.objects.filter(
                imei=rho.imei, shop=shop_sender_current, created__gt=rho.created
            ).exists():
                sequence_rhos = RemainderHistory.objects.filter(
                    imei=rho.imei, shop=shop_sender_current, created__gt=rho.created
                )
                for obj in sequence_rhos:
                    obj.pre_remainder = remainder_current.current_remainder
                    # obj.sub_total=remainder_current.total_av_price+obj.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                    obj.current_remainder = (
                        remainder_current.current_remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    # obj.av_price=obj.sub_total/obj.current_remainder
                    obj.save()
                    remainder_current.current_remainder = obj.current_remainder
                    # remainder_current.total_av_price=obj.sub_total
                    # remainder_current.av_price=obj.av_price
                    remainder_current.save()
            rho.delete()

        for i in range(n):
            # creating new rho for chop_receiver_changed
            if RemainderHistory.objects.filter(
                imei=imeis[i], shop=shop_receiver_changed, created__lt=dateTime
            ).exists():
                rho_hist_objs_before = RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop_receiver_changed, created__lt=dateTime
                )
                rho_hist_before = rho_hist_objs_before.latest("created")
                remainder_current = RemainderCurrent.objects.get(
                    imei=imeis[i], shop=shop_receiver_changed
                )
                remainder_current.current_remainder = rho_hist_before.current_remainder
                # remainder_current.total_av_price=rho_hist_before.sub_total
                # remainder_current.av_price=rho_hist_before.av_price
                remainder_current.save()
            else:
                if RemainderCurrent.objects.filter(
                    imei=imeis[i], shop=shop_receiver_changed
                ).exists():
                    remainder_current = RemainderCurrent.objects.get(
                        imei=imeis[i], shop=shop_receiver_changed
                    )
                    remainder_current.current_remainder = 0
                    remainder_current.total_av_price = 0
                    # remainder_current.av_price=av_price
                    remainder_current.save()
                else:
                    remainder_current = RemainderCurrent.objects.create(
                        imei=imeis[i],
                        shop=shop_receiver_changed,
                        current_remainder=0,
                        # total_av_price=0,
                        # av_price=av_price,
                        # retail_price=0
                    )
            rho_new = RemainderHistory.objects.create(
                shop=shop_receiver_changed,
                created=dateTime,
                document=document,
                name=names[i],
                imei=imeis[i],
                incoming_quantity=int(quantities[i]),
                outgoing_quantity=0,
                pre_remainder=remainder_current.current_remainder,
                current_remainder=remainder_current.current_remainder
                + int(quantities[i]),
                retail_price=int(prices[i]),
                status=True,
                # sub_total=remainder_current.total_av_price+remainder_current.av_price*int(quantities[i]),
                # av_price= (remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price))/(remainder_current.current_remainder+int(quantities[i]))
            )
            remainder_current.current_remainder = rho_new.current_remainder
            # remainder_current.total_av_price=rho_new.sub_total
            # remainder_current.av_price=rho_new.av_price
            remainder_current.save()

            if RemainderHistory.objects.filter(
                imei=imeis[i], shop=shop_receiver_changed, created__gt=rho_new.created
            ).exists():
                sequence_rhos = RemainderHistory.objects.filter(
                    imei=imeis[i],
                    shop=shop_receiver_changed,
                    created__gt=rho_new.created,
                )
                for obj in sequence_rhos:
                    obj.pre_remainder = remainder_current.current_remainder
                    # obj.sub_total=remainder_current.total_av_price+remainder_current.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                    obj.current_remainder = (
                        remainder_current.current_remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    # obj.av_price=obj.sub_total/obj.current_remainder
                    obj.save()
                    remainder_current.current_remainder = obj.current_remainder
                    # remainder_current.total_av_price=obj.sub_total
                    # remainder_current.av_price=obj.av_price
                    remainder_current.save()

            # creating new rho for shop_sender_changed
            if RemainderHistory.objects.filter(
                imei=imeis[i], shop=shop_sender_changed, created__lt=dateTime
            ).exists():
                rho_hist_objs_before = RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop_sender_changed, created__lt=dateTime
                )
                rho_hist_before = rho_hist_objs_before.latest("created")
                remainder_current = RemainderCurrent.objects.get(
                    imei=imeis[i], shop=shop_sender_changed
                )
                # remainder_current=RemainderCurrent(imei=imeis[i], shop=shop_current)#creates a new object which we don't need
                remainder_current.current_remainder = rho_hist_before.current_remainder
                # remainder_current.total_av_price=rho_hist_before.sub_total
                # remainder_current.av_price=rho_hist_before.av_price
                remainder_current.save()
            else:
                if RemainderCurrent.objects.filter(
                    imei=imeis[i], shop=shop_sender_changed
                ).exists():
                    remainder_current = RemainderCurrent.objects.get(
                        imei=imeis[i], shop=shop_sender_changed
                    )
                    remainder_current.current_remainder = 0
                    # remainder_current.total_av_price=0
                    # remainder_current.av_price=av_price
                    remainder_current.save()
                else:
                    remainder_current = RemainderCurrent.objects.create(
                        imei=imeis[i],
                        shop=shop_sender_changed,
                        current_remainder=0,
                        # total_av_price=0,
                        # av_price=av_price,
                        retail_price=0,
                    )
            rho_new = RemainderHistory.objects.create(
                shop=shop_sender_changed,
                created=dateTime,
                document=document,
                name=names[i],
                imei=imeis[i],
                incoming_quantity=0,
                outgoing_quantity=int(quantities[i]),
                pre_remainder=remainder_current.current_remainder,
                current_remainder=remainder_current.current_remainder
                + int(quantities[i]),
                retail_price=int(prices[i]),
                # sub_total=remainder_current.total_av_price+remainder_current.av_price*int(quantities[i]),
                # av_price= (remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price))/(remainder_current.current_remainder+int(quantities[i]))
            )
            remainder_current.current_remainder = rho_new.current_remainder
            # remainder_current.total_av_price=rho_new.sub_total
            # remainder_current.av_price=rho_new.av_price
            remainder_current.save()

            if RemainderHistory.objects.filter(
                imei=imeis[i], shop=shop_sender_changed, created__gt=rho_new.created
            ).exists():
                sequence_rhos = RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop_sender_changed, created__gt=rho_new.created
                )
                for obj in sequence_rhos:
                    obj.pre_remainder = remainder_current.current_remainder
                    # obj.sub_total=remainder_current.total_av_price+remainder_current.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                    obj.current_remainder = (
                        remainder_current.current_remainder
                        + obj.incoming_quantity
                        - obj.outgoing_quantity
                    )
                    # obj.av_price=obj.sub_total/obj.current_remainder
                    obj.save()
                    remainder_current.current_remainder = obj.current_remainder
                    # remainder_current.total_av_price=obj.sub_total
                    # remainder_current.av_price=obj.av_price
                    remainder_current.save()
        document.sum = sum
        document.created = dateTime
        document.save()
        registers = Register.objects.filter(document=document)
        for register in registers:
            register.delete()
        return redirect("log")
    else:
        context = {
            "document": document,
            "registers": registers,
            "shops": shops,
        }
        return render(request, "documents/change_transfer_posted.html", context)

def change_transfer_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = (
        Register.objects.filter(document=document)
        .exclude(deleted=True)
        .order_by("created")
    )
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
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
        dateTime = request.POST["dateTime"]
        shop_sender = Shop.objects.get(id=shop_sender)
        shop_receiver = Shop.objects.get(id=shop_receiver)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        if shop_sender == shop_receiver:
            messages.error(
                request,
                "Документ не проведен. Выберите фирму получателя отличную от отправителя",
            )
            return redirect("change_transfer_unposted", document.id)
        else:
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
            # posting transfer document
            if post_check == True:
                check_point = []
                n = len(names)
                for i in range(n):
                    if RemainderCurrent.objects.filter(
                        imei=imeis[i], shop=shop_sender
                    ).exists():
                        remainder_current_sender = RemainderCurrent.objects.get(
                            imei=imeis[i], shop=shop_sender
                        )
                        if remainder_current_sender.current_remainder < int(
                            quantities[i]
                        ):
                            check_point.append(False)
                        else:
                            check_point.append(True)
                    else:
                        check_point.append(False)
                if False in check_point:
                    messages.error(
                        request,
                        "Документ не проведен. Одно или несколько наименование отсутствуют на балансе данной фирмы.",
                    )
                    return redirect("change_transfer_unposted", document.id)
                else:
                    document.posted = True
                    document.save()
                    sum = 0
                    for i in range(n):
                        sum += int(prices[i]) * int(quantities[i])
                        # checking shop_sender
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_sender, created__lt=dateTime
                        ).exists():
                            sequence_rhos_before = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__lt=dateTime
                            )
                            remainder_history = sequence_rhos_before.latest("created")
                            remainder_current = RemainderCurrent.objects.get(
                                shop=shop_sender, imei=imeis[i]
                            )
                            remainder_current.current_remainder = (
                                remainder_history.current_remainder
                            )
                            # remainder_current.av_price=remainder_history.av_price
                            # remainder_current.total_av_price=remainder_history.sub_total
                            remainder_current.save()
                        else:
                            if RemainderCurrent.objects.filter(
                                imei=imeis[i], shop=shop_sender
                            ).exists():
                                remainder_current = RemainderCurrent.objects.get(
                                    shop=shop_sender, imei=imeis[i]
                                )
                                remainder_current.current_remainder = 0
                                # remainder_current.av_price=0
                                # remainder_current.total_av_price=0
                                remainder_current.save()
                            else:
                                remainder_current = RemainderCurrent.objects.create(
                                    imei=imeis[i],
                                    name=names[i],
                                    shop=shop_sender,
                                    # av_price=0,
                                    # total_av_price=0,
                                    current_remainder=0,
                                )

                        remainder_history = RemainderHistory.objects.create(
                            created=dateTime,
                            document=document,
                            rho_type=document.title,
                            shop=shop_sender,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            # av_price=remainder_current.av_price,
                            retail_price=prices[i],
                            pre_remainder=remainder_current.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity=quantities[i],
                            current_remainder=remainder_current.current_remainder
                            - int(quantities[i]),
                            # sub_total=remainder_current.av_price*(remainder_current.current_remainder-int(quantities[i]))
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                        # av_price_sender=remainder_history.av_price

                        # checking docs after remainder_history for shop_sender
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_sender, created__gt=dateTime
                        ).exists():
                            sequence_rhos_after = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_sender, created__gt=dateTime
                            )
                            sequence_rhos_after = sequence_rhos_after.all().order_by(
                                "created"
                            )
                            for obj in sequence_rhos_after:

                                obj.pre_remainder = remainder_current.current_remainder
                                obj.current_remainder = (
                                    remainder_current.current_remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )

                                obj.save()
                                remainder_current.current_remainder = (
                                    obj.current_remainder
                                )
                                remainder_current.save()

                        # checking shop_receiver
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_receiver, created__lt=dateTime
                        ).exists():
                            sequence_rhos_after = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__lt=dateTime
                            )
                            remainder_history = sequence_rhos_after.latest("created")
                            remainder_current = RemainderCurrent.objects.get(
                                shop=shop_receiver, imei=imeis[i]
                            )
                            remainder_current.current_remainder = (
                                remainder_history.current_remainder
                            )
                            # remainder_current.av_price=remainder_history.av_price
                            # remainder_current.total_av_price=remainder_history.sub_total
                            remainder_current.save()
                        else:
                            if RemainderCurrent.objects.filter(
                                imei=imeis[i], shop=shop_receiver
                            ).exists():
                                remainder_current = RemainderCurrent.objects.get(
                                    shop=shop_receiver, imei=imeis[i]
                                )
                                remainder_current.current_remainder = 0
                                # remainder_current.av_price=0
                                # remainder_current.total_av_price=0
                                remainder_current.save()
                            else:
                                remainder_current = RemainderCurrent.objects.create(
                                    imei=imeis[i],
                                    name=names[i],
                                    shop=shop_receiver,
                                    # av_price=0,
                                    # total_av_price=0,
                                    current_remainder=0,
                                )
                        remainder_history = RemainderHistory.objects.create(
                            created=dateTime,
                            document=document,
                            rho_type=document.title,
                            shop=shop_receiver,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            pre_remainder=remainder_current.current_remainder,
                            incoming_quantity=quantities[i],
                            outgoing_quantity=0,
                            current_remainder=remainder_current.current_remainder
                            + int(quantities[i]),
                            status=True
                            # sub_total=remainder_current.total_av_price+av_price_sender*int(quantities[i]),
                            # av_price=(remainder_current.total_av_price+av_price_sender*int(quantities[i]))/(remainder_current.current_remainder+int(quantities[i]))
                        )

                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        remainder_current.retail_price = remainder_history.retail_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()

                        # checking docs after remainder_history for shop_receiver
                        if RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop_receiver, created__gt=dateTime
                        ).exists():
                            sequence_rhos_after = RemainderHistory.objects.filter(
                                imei=imeis[i], shop=shop_receiver, created__gt=dateTime
                            )
                            sequence_rhos_after = sequence_rhos_after.all().order_by(
                                "created"
                            )
                            for obj in sequence_rhos_after:

                                obj.pre_remainder = remainder_current.current_remainder
                                obj.current_remainder = (
                                    remainder_current.current_remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )
                                obj.save()
                                remainder_current.current_remainder = (
                                    obj.current_remainder
                                )
                                # remainder_current.total_av_price=obj.sub_total
                                # remainder_current.av_price=obj.av_price
                                remainder_current.save()
                    document.sum = sum
                    document.save()
                    registers = Register.objects.filter(document=document)
                    for register in registers:
                        register.delete()
                    return redirect("log")
            # saving unposted document
            else:
                if Register.objects.filter(deleted=True).exists():
                    deleted_registers = Register.objects.filter(deleted=True)
                    for register in deleted_registers:
                        register.delete()
                n = len(names)
                sum = 0
                for i in range(n):
                    sum += int(prices[i]) * int(quantities[i])
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(document=document, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.document = document
                    register.shop_sender = shop_sender
                    register.shop_receiver = shop_receiver
                    register.new = False
                    register.save()
                document.sum = sum
                document.save()
                return redirect("log")

    else:
        context = {
            "registers": registers,
            "shops": shops,
            "document": document,
            "categories": categories,
        }
        return render(request, "documents/change_transfer_unposted.html", context)

def unpost_transfer(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    for rho in rhos:
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
            remainder_current.save()
        else:
            remainder_current = RemainderCurrent.objects.get(
                shop=rho.shop, imei=rho.imei
            )
            remainder_current.current_remainder = 0
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
        # no need to create new registers since they have been created by 'change_transfer_posted'
    document.posted = False
    document.save()
    return redirect("log")

# =======================================================================================
def identifier_recognition(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("recognition", identifier.id)
    else:
        return redirect("login")

def check_recognition(request, identifier_id):
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["check_imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                register = Register.objects.get(identifier=identifier, product=product)
                register.quantity += 1
                register.save()
                return redirect("recognition", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, product=product
                )
                return redirect("recognition", identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("recognition", identifier.id)

def check_recognition_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                # register.quantity = 1
                # register.price = 0
                # register.sub_total = 0
                register.save()
            elif Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
            else:
                register = Register.objects.create(
                    document=document, 
                    product=product, 
                    new=True
                )
            return redirect("change_recognition_unposted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_recognition_unposted", document.id)

def check_recognition_posted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                # register.quantity = 1
                # register.price = 0
                # register.sub_total = 0
                register.save()
            elif Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_recognition_posted", document.id)
            else:
                register = Register.objects.create(
                    document=document, 
                    product=product,
                    new=True
                    )
            return redirect("change_recognition_posted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_recognition_posted", document.id)

def recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
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
    item.deleted = True
    item.save()
    return redirect("change_recognition_unposted", document.id)

def delete_line_recognition_posted (request, imei, document_id):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.deleted = True
    item.save()
    return redirect("change_recognition_posted", document.id)

def clear_recognition(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("recognition", identifier.id)

def recognition_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Оприходование ТМЦ")
    if request.method == "POST":
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False

        if imeis:
            if post_check == True:
                document = Document.objects.create(
                title=doc_type, 
                user=request.user, 
                created=dateTime,
                posted=True
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    # imei=imeis[i]
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime
                        )
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(
                            shop=shop, imei=imeis[i]
                        )
                        remainder_current.current_remainder = (
                            remainder_history.current_remainder
                        )
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(
                            imei=imeis[i], shop=shop
                        ).exists():
                            remainder_current = RemainderCurrent.objects.get(
                                imei=imeis[i], shop=shop
                            )
                            remainder_current.current_remainder = 0
                            # remainder_current.av_price=0
                            # remainder_current.total_av_price=0
                            remainder_current.save()

                        else:
                            remainder_current = RemainderCurrent.objects.create(
                                updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        rho_type=doc_type,
                        shop=shop,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total= int(quantities[i]) * int(prices[i]),
                    )
                    document_sum += remainder_history.sub_total
                    remainder_current.current_remainder = (
                        remainder_history.current_remainder
                    )
                    remainder_current.save()

                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        av_price_obj.av_price = (
                            av_price_obj.sum / av_price_obj.current_remainder
                        )
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )

                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__gt=document.created
                    ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__gt=document.created
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
                for register in registers:
                    register.delete()
            else:
                document = Document.objects.create(
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
                    register.shop = shop
                    register.new = False
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
            document.sum = document_sum
            document.save()
            identifier.delete()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("recognition", identifier.id)

def change_recognition_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    else:
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # creating new registers
            register = Register.objects.create(
                shop=shop_current,
                supplier=rho.supplier,
                product=product,
                quantity=rho.incoming_quantity,
                price=rho.wholesale_price,
                document=document,
                sub_total=rho.wholesale_price * rho.incoming_quantity,
            )
        registers = Register.objects.filter(document=document).order_by("created")

    numbers = registers.exclude(deleted=True).count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()

    if request.method == "POST":
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        if imeis:
            if Register.objects.filter(document=document, deleted=True).exists():
                deleted_registers = Register.objects.filter(document=document, deleted=True)
                for del_reg in deleted_registers:
                    del_reg.delete()
            for rho in rhos:
            # deleting current rhos
                if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, 
                    created__lt=rho.created).exists():
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
                if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, 
                    created__gt=rho.created).exists():
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
            # creating new rhos & deleting registers
            n = len(names)
            document_sum = 0
            for i in range(n):
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime)
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                    remainder_current.current_remainder = (remainder_history.current_remainder)
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
                            shop=shop,
                            imei=imeis[i],
                            name=names[i],
                            current_remainder=0,
                            # av_price=0,
                            # total_av_price=0
                        )
                remainder_history = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=remainder_current.current_remainder
                    + int(quantities[i]),
                    wholesale_price=int(prices[i]),
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += remainder_history.sub_total
                remainder_current.current_remainder = remainder_history.current_remainder
                remainder_current.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=dateTime).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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

            document.sum = document_sum
            document.created = dateTime
            document.save()
            for register in registers:
                register.delete()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("change_recognition_posted", document.id)

    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
            "categories": categories,
        }
        return render(request, "documents/change_recognition_posted.html", context)

def change_recognition_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        if imeis:
            if post_check == True:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__lt=dateTime).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                        remainder_current.current_remainder = (remainder_history.current_remainder)
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
                                # updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                category=product.category,
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    document_sum += remainder_history.sub_total
                    remainder_current.current_remainder = remainder_history.current_remainder
                    remainder_current.save()
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * int(prices[i])
                        av_price_obj.av_price = (av_price_obj.sum / av_price_obj.current_remainder)
                        av_price_obj.save()
                    else:
                        av_price_obj = AvPrice.objects.create(
                            name=names[i],
                            imei=imeis[i],
                            current_remainder=int(quantities[i]),
                            sum=int(quantities[i]) * int(prices[i]),
                            av_price=int(prices[i]),
                        )

                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__gt=dateTime).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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
                document.posted = True
                document.created=dateTime
                registers = Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
            else:
                n = len(names)
                document_sum = 0
                if Register.objects.filter(document=document, deleted=True).exists():
                    registers=Register.objects.filter(document=document, deleted=True)
                    for register in registers:
                        register.delete()
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(document=document, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.shop = shop
                    register.new = False
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
            document.sum = document_sum
            document.save()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("change_recognition_unposted", document.id)
    else:
        context = {
            "registers": registers,
            "shops": shops,
            "document": document,
            "categories": categories,
        }
        return render(request, "documents/change_recognition_unposted.html", context)

def unpost_recognition(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    shop_current = rhos.first().shop
    for rho in rhos:
        product = Product.objects.get(imei=rho.imei)
        # deleting existing rhos
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
        if RemainderHistory.objects.filter(
            shop=rho.shop, imei=rho.imei, created__gt=rho.created).exists():
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
    if Register.objects.filter(document=document, deleted=True).exists():
        registers=Register.objects.filter(document=document, deleted=True)
        for register in registers:
            register.delete()
    if Register.objects.filter(document=document, new=True).exists():
        registers=Register.objects.filter(document=document, new=True)
        register.new=False
        register.save()
    document.posted = False
    document.save()
    return redirect("log")

def delete_recognition(request, document_id):
    document = Document.objects.get(id=document_id)
    recognitions = Recognition.objects.filter(document=document)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder -= rho.incoming_quantity
        av_price.sum -= rho.incoming_quantity * rho.wholesale_price
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
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                register = Register.objects.get(identifier=identifier, product=product)
                register.quantity += 1
                register.save()
                return redirect("signing_off", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, product=product
                )
                return redirect("signing_off", identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("signing_off", identifier.id)

def check_signing_off_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                # register.quantity = 1
                # register.price = 0
                # register.sub_total = 0
                register.save()
            elif Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
            else:
                register = Register.objects.create(
                    document=document, 
                    product=product, 
                    new=True
                )
            return redirect ('change_signing_off_unposted', document_id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect ('change_signing_off_unposted', document_id)

def check_signing_off_posted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                # register.quantity = 1
                # register.price = 0
                # register.sub_total = 0
                register.save()
            elif Register.objects.filter(document=document, product=product).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_signing_off_posted", document.id)
            else:
                register = Register.objects.create(
                    document=document, 
                    product=product,
                    new=True
                    )
            return redirect("change_signing_off_posted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_signing_off_posted", document.id)

def signing_off(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "shops": shops,
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
    item.deleted = True
    item.save()
    return redirect("change_signing_off_unposted", document.id)

def delete_line_posted_signing_off (request, imei, document_id):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(document=document, product=product)
    item.deleted = True
    item.save()
    return redirect("change_signing_off_posted", document.id)

def clear_signing_off(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("signing_off", identifier.id)

def signing_off_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Списание ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices=request.POST.getlist('price', None)
        sub_totals=request.POST.getlist('sub_total', None)
        shop = Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)
    
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        if imeis:
            if post_check == True:
                document = Document.objects.create(
                title=doc_type, 
                user=request.user, 
                created=dateTime,
                posted=True
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime
                    ).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(
                            imei=imeis[i], shop=shop, created__lt=dateTime)
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                        remainder_current.current_remainder = remainder_history.current_remainder
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        messages.error(request,"Данное наименование отсутсвует на балансе. Вы не можете его списать.")
                        return redirect("signing_off", identifier.id)
                    # if AvPrice.objects.filter(imei=imeis[i]).exists():
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder -= int(quantities[i])
                    av_price_obj.sum -= int(quantities[i]) * av_price_obj.av_price
                    # av_price_obj.av_price=av_price_obj.sum/av_price_obj.current_remainder
                    av_price_obj.save()

                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=document.title,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        #wholesale_price=int(prices[i]),
                        sub_total=int(quantities[i]) * av_price_obj.av_price,
                    )
                    document_sum=remainder_history.sub_total
                    remainder_current.current_remainder =remainder_history.current_remainder
                    remainder_current.save()
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created
                        ).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created)
                        sequence_rhos_after = sequence_rhos_after.all().order_by("created")
                        for obj in sequence_rhos_after:
                            obj.pre_remainder = remainder_current.current_remainder
                            obj.current_remainder = (
                                remainder_current.current_remainder
                                + int(obj.incoming_quantity)
                                - int(obj.outgoing_quantity)
                            )
                            obj.save()
                            remainder_current.current_remainder = obj.current_remainder
                            remainder_current.save()
                document.sum = document_sum
                document.save()
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")           
            else:
                document = Document.objects.create(
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
                    register.shop = shop
                    register.new = False
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
                document.sum = document_sum
                document.save()
                identifier.delete()
                return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования для списания.")
            return redirect("signing_off", identifier.id)

def delete_signing_off(request, document_id):
    document = Document.objects.get(id=document_id)
    signoffs = SignOff.objects.filter(document=document)
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
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    else:
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # creating new registers
            register = Register.objects.create(
                shop=shop_current,
                product=product,
                quantity=rho.outgoing_quantity,
                price=rho.wholesale_price,
                document=document,
                sub_total=rho.wholesale_price * rho.incoming_quantity,
            )
        registers = Register.objects.filter(document=document).order_by("created")

    numbers = registers.exclude(deleted=True).count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    if request.method == 'POST':
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        if imeis:
            if Register.objects.filter(document=document, deleted=True).exists():
                deleted_registers = Register.objects.filter(document=document, deleted=True)
                for del_reg in deleted_registers:
                    del_reg.delete()
            for rho in rhos:
            # deleting current rhos
                if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, 
                    created__lt=rho.created).exists():
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
                if RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei, 
                    created__gt=rho.created).exists():
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
            # creating new rhos & deleting registers
            n = len(names)
            document_sum = 0
            for i in range(n):
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime)
                    remainder_history = sequence_rhos_before.latest("created")
                    remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                    remainder_current.current_remainder = (remainder_history.current_remainder)
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
                            shop=shop,
                            imei=imeis[i],
                            name=names[i],
                            current_remainder=0,
                            # av_price=0,
                            # total_av_price=0
                        )
                remainder_history = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    rho_type=document.title,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=remainder_current.current_remainder
                    - int(quantities[i]),
                    wholesale_price=int(prices[i]),
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += remainder_history.sub_total
                remainder_current.current_remainder = remainder_history.current_remainder
                remainder_current.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=dateTime).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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

            document.sum = document_sum
            document.created = dateTime
            document.save()
            for register in registers:
                register.delete()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("change_recognition_posted", document.id)
    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
            "categories": categories,
        }
        return render(request, "documents/change_signing_off_posted.html", context)
    
        


def change_signing_off_unposted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Списание ТМЦ")
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        if imeis:
            if post_check == True:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__lt=dateTime).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
                        remainder_history = sequence_rhos_before.latest("created")
                        remainder_current = RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                        remainder_current.current_remainder = (remainder_history.current_remainder)
                        # remainder_current.av_price=remainder_history.av_price
                        # remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.save()
                    else:
                        messages.error(request,"Данное наименование отсутсвует на балансе. Вы не можете его списать.")
                        return redirect("change_signing_off_posted", document.id)

                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        rho_type=document.title,
                        created=dateTime,
                        shop=shop,
                        category=product.category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=0,
                        outgoing_quantity=quantities[i],
                        current_remainder=remainder_current.current_remainder
                        - int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=int(int(quantities[i]) * int(prices[i])),
                    )
                    document_sum += remainder_history.sub_total
                    remainder_current.current_remainder = remainder_history.current_remainder
                    remainder_current.save()
                #     if AvPrice.objects.filter(imei=imeis[i]).exists():
                #         av_price_obj = AvPrice.objects.get(imei=imeis[i])
                #         av_price_obj.current_remainder -= int(quantities[i])
                #         av_price_obj.sum += int(quantities[i]) * int(prices[i])
                #         av_price_obj.av_price = (av_price_obj.sum / av_price_obj.current_remainder)
                #         av_price_obj.save()
                #     else:
                #         av_price_obj = AvPrice.objects.create(
                #             name=names[i],
                #             imei=imeis[i],
                #             current_remainder=int(quantities[i]),
                #             sum=int(quantities[i]) * int(prices[i]),
                #             av_price=int(prices[i]),
                    #checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__gt=dateTime).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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
                            remainder_current.save          
                document.posted = True
                document.sum=document_sum
                document.created=dateTime
                document.save()
                registers = Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
                return redirect ('log')
               
            else:
                n = len(names)
                document_sum = 0
                if Register.objects.filter(document=document, deleted=True).exists():
                    registers=Register.objects.filter(document=document, deleted=True)
                    for register in registers:
                        register.delete()
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(document=document, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.shop = shop
                    register.new = False
                    register.identifier = None
                    register.sub_total = int(prices[i]) * int(quantities[i])
                    register.save()
                    document_sum+=int(register.sub_total)
            document.sum = document_sum
            document.save()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("change_signing_off_unposted", document.id)
    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
        }
        return render(request, "documents/change_signing_off_unposted.html", context)


def unpost_signing_off (request, document_id):
    pass

# ================================================================================================
def identifier_return(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("return_doc", identifier.id)
    else:
        return redirect("login")

def check_return(request, identifier_id):
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                register = Register.objects.get(identifier=identifier, product=product)
                register.quantity += 1
                register.save()
                return redirect("return_doc", identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, product=product
                )
                return redirect("return_doc", identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("return_doc", identifier.id)

def check_return_unposted(request, document_id):
    # shops = Shop.objects.all()
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=False).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_return_unposted", document.id)
            elif Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted=False
                #register.price=0
                #register.sub_total=0
                register.save()
                return redirect("change_return_unposted", document.id)
            else:
                register = Register.objects.create(
                    document=document,
                    product=product,
                    new=True
                )
                return redirect("change_return_unposted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_return_unposted", document.id)

def check_return_posted (request, document_id):
    document = Document.objects.get(id=document_id)
    registers = Register.objects.filter(document=document) 
    if request.method == "POST":
        imei = request.POST["imei"]
        if Product.objects.filter(imei=imei).exists():
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(document=document, product=product, deleted=False).exists():
                messages.error(request, "Вы уже ввели данное наименование.")
                return redirect("change_return_posted", document.id)
            elif Register.objects.filter(document=document, product=product, deleted=True).exists():
                register = Register.objects.get(document=document, product=product, deleted=True)
                register.deleted = False
                register.save()
                return redirect("change_return_posted", document.id)
            else:
                register = Register.objects.create(
                    document=document, 
                    product=product, 
                    new=True
                )
                return redirect("change_return_posted", document.id)
        else:
            messages.error(request, "Данное наименование отсутствует в БД. Введите его.")
            return redirect("change_return_posted", document.id)

def return_doc(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    numbers = registers.count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()
    context = {
        "identifier": identifier,
        "categories": categories,
        "shops": shops,
        "registers": registers,
    }
    return render(request, "documents/return_doc.html", context)

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
    register.deleted = True
    register.save()
    return redirect("change_return_unposted", document.id)

def delete_line_posted_return (request, document_id, imei):
    document = Document.objects.get(id=document_id)
    product = Product.objects.get(imei=imei)
    register = Register.objects.get(document=document, product=product)
    register.deleted = True
    register.save()
    return redirect("change_return_posted", document.id)

def clear_return(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("return_doc", identifier.id)

def return_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Возврат ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        # try:
        #     supplier=request.POST['supplier']
        # except:
        #     messages.error(request, 'Введите поставщика')
        #     return redirect ('delivery', identifier.id)
        if imeis:
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()
            try:
                if request.POST["post_check"]:
                    post_check = True
            except KeyError:
                post_check = False
                # posting transfer document
            if post_check == True:
                document = Document.objects.create(
                    title=doc_type, 
                    user=request.user, 
                    created=dateTime, 
                    posted=True
                )
                n = len(names)
                document_sum = 0
                for i in range(n):
                    # imei=imeis[i]
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
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
                                updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                        # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        retail_price=prices[i],
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        sub_total= int(quantities[i]) * int(prices[i]),
                    )
                    document_sum+=remainder_history.sub_total
                    remainder_current.current_remainder = remainder_history.current_remainder
                    remainder_current.save()
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * av_price_obj.av_price
                        # av_price_obj.av_price=av_price_obj.sum/av_price_obj.current_remainder
                        av_price_obj.save()
                    else:
                        messages.error(request,"Данное наименование никогда не было учтено на балансе фирмы. Вы не можете сделать возврат",)
                        return redirect("return_doc", identifier.id)
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
                document.sum = document_sum
                document.save()

                # operations with cash
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    chos = Cash.objects.filter(shop=shop, created__lt=dateTime)  # cash history objects
                    cho_before = chos.latest("created")  # cash history object
                    cash_pre_remainder = cho_before.current_remainder
                else:
                    cash_pre_remainder = 0
                cash = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    user=request.user,
                    pre_remainder=cash_pre_remainder,
                    cash_out=document_sum,
                    cash_in=0,
                    current_remainder=cash_pre_remainder - document_sum,
                )
                if CashRemainder.objects.filter(shop=shop).exists():
                    cash_remainder = CashRemainder.objects.get(shop=shop)
                else:
                    cash_remainder = CashRemainder.objects.create(
                        shop=shop,
                        remainder=0
                    )
                cash_remainder.remainder = cash.current_remainder
                cash_remainder.save()
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created)
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder.remainder
                        obj.current_remainder = (cash_remainder.remainder + obj.cash_in - obj.cash_out)
                        obj.save()
                        cash_remainder.remainder = obj.current_remainder
                        cash_remainder.save()
                # end of operations with cash
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect("log")
            else:
                document = Document.objects.create(
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
                    register.new = False
                    register.identifier = None
                    register.save()
                identifier.delete()
                document.sum = sum
                document.save()
                return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("return_doc", identifier.id)

def change_return_unposted(request, document_id):
    document = Document.objects.get(id=document_id)
    registers = (Register.objects.filter(document=document).exclude(deleted=True).order_by("created"))
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    doc_type = DocumentType.objects.get(name="Возврат ТМЦ")
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
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        try:
            if request.POST["post_check"]:
                post_check = True
        except KeyError:
            post_check = False
        # posting the document
        if post_check == True:
            if imeis:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    # checking docs before remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime).exists():
                        sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
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
                                updated=dateTime,
                                shop=shop,
                                imei=imeis[i],
                                name=names[i],
                                current_remainder=0,
                                # av_price=0,
                                # total_av_price=0
                            )
                    # creating remainder_history
                    remainder_history = RemainderHistory.objects.create(
                        document=document,
                        created=dateTime,
                        shop=shop,
                        rho_type=doc_type,
                        # category=category,
                        imei=imeis[i],
                        name=names[i],
                        retail_price=prices[i],
                        pre_remainder=remainder_current.current_remainder,
                        incoming_quantity=quantities[i],
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder
                        + int(quantities[i]),
                        sub_total= int(quantities[i]) * int(prices[i]),
                    )
                    document_sum+=remainder_history.sub_total
                    remainder_current.current_remainder = remainder_history.current_remainder
                    remainder_current.save()
                    if AvPrice.objects.filter(imei=imeis[i]).exists():
                        av_price_obj = AvPrice.objects.get(imei=imeis[i])
                        av_price_obj.current_remainder += int(quantities[i])
                        av_price_obj.sum += int(quantities[i]) * av_price_obj.av_price
                        # av_price_obj.av_price=av_price_obj.sum/av_price_obj.current_remainder
                        av_price_obj.save()
                    else:
                        messages.error(request,"Данное наименование никогда не было учтено на балансе фирмы. Вы не можете сделать возврат",)
                        return redirect("change_return_unposted", document.id)
                    # checking docs after remainder_history
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                        created__gt=dateTime).exists():
                        sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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
                document.sum = document_sum
                document.posted=True
                document.save()
                # operations with cash
                if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                    chos = Cash.objects.filter(shop=shop, created__lt=dateTime)  # cash history objects
                    cho_before = chos.latest("created")  # cash history object
                    cash_pre_remainder = cho_before.current_remainder
                else:
                    cash_pre_remainder = 0
                cash = Cash.objects.create(
                    shop=shop,
                    created=dateTime,
                    document=document,
                    user=request.user,
                    pre_remainder=cash_pre_remainder,
                    cash_out=document_sum,
                    cash_in=0,
                    current_remainder=cash_pre_remainder - document_sum,
                )
                if CashRemainder.objects.filter(shop=shop).exists():
                    cash_remainder = CashRemainder.objects.get(shop=shop)
                else:
                    cash_remainder = CashRemainder.objects.create(
                        shop=shop,
                        remainder=0
                    )
                cash_remainder.remainder = cash.current_remainder
                cash_remainder.save()
                #changing cash objects after
                if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                    sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=document.created)
                    sequence_chos_after = sequence_chos_after.all().order_by("created")
                    for obj in sequence_chos_after:
                        obj.pre_remainder = cash_remainder.remainder
                        obj.current_remainder = (cash_remainder.remainder + obj.cash_in - obj.cash_out)
                        obj.save()
                        cash_remainder.remainder = obj.current_remainder
                        cash_remainder.save()
                # end of operations with cash
                registers=Register.objects.filter(document=document)
                for register in registers:
                    register.delete()
                return redirect ('log')
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_return_unposted", document.id)
        else:
            if imeis:
                n = len(names)
                document_sum = 0
                for i in range(n):
                    product = Product.objects.get(imei=imeis[i])
                    register = Register.objects.get(document=document, product=product)
                    register.price = prices[i]
                    register.quantity = quantities[i]
                    register.sub_total = sub_totals[i]
                    register.document = document
                    register.shop = shop
                    register.new = False
                    register.save()
                    document_sum += int(register.sub_total)
                if Register.objects.filter(document=document, deleted=True).exists():
                    registers=Register.objects.filter(document=document, deleted=True)
                    for register in registers:
                        register.delete()
                document.sum = document_sum
                document.save()
                return redirect("log")
            else:
                messages.error(request, "Вы не ввели ни одного наименования.")
                return redirect("change_return_unposted", document.id)
    else:
        context = {
            "registers": registers,
            "shops": shops,
            "document": document,
        }
        return render(request, "documents/change_return_unposted.html", context)

def change_return_posted(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document).order_by("created")
    #categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    if Register.objects.filter(document=document).exists():
        registers = Register.objects.filter(document=document).exclude(deleted=True).order_by("created")
    else:
        for rho in rhos:
            product = Product.objects.get(imei=rho.imei)
            # creating new registers
            register = Register.objects.create(
                shop=shop_current,
                product=product,
                quantity=rho.incoming_quantity,
                price=rho.retail_price,
                document=document,
                sub_total=rho.retail_price * rho.incoming_quantity,
            )
        registers = Register.objects.filter(document=document).order_by("created")

    numbers = registers.exclude(deleted=True).count()
    for register, i in zip(registers, range(numbers)):
        register.number = i + 1
        register.save()

    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        names = request.POST.getlist("name", None)
        imeis = request.POST.getlist("imei", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        if Register.objects.filter(document=document, deleted=True).exists():
            deleted_registers = Register.objects.filter(document=document, deleted=True)
            for del_reg in deleted_registers:
                del_reg.delete()
        for rho in rhos:
            # deleting current rhos
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

        # creating new rhos & deleting registers
        if imeis:
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()

            n = len(names)
            document_sum = 0
            for i in range(n):
                if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, 
                    created__lt=dateTime).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__lt=dateTime)
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
                            updated=dateTime,
                            shop=shop,
                            imei=imeis[i],
                            name=names[i],
                            current_remainder=0,
                            # av_price=0,
                            # total_av_price=0
                        )
                remainder_history = RemainderHistory.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    rho_type=document.title,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=remainder_current.current_remainder + int(quantities[i]),
                    retail_price=int(prices[i]),
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += remainder_history.sub_total
                remainder_current.current_remainder = remainder_history.current_remainder
                remainder_current.save()
                # checking docs after remainder_history
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__gt=dateTime).exists():
                    sequence_rhos_after = RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=dateTime)
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

            #operations with cahs
            #deleting current cho
            cho=Cash.objects.get(document=document)
            if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
                chos = Cash.objects.filter(shop=shop, created__lt=cho.created)  # cash history objects
                cho_before = chos.latest("created")  # cash history object
                cash_remainder=CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder=cho_before.currrent_remainder
                cash_remainder.save()
            else:
                if CashRemainder.objects.filter(shop=cho.shop).exists():
                    cash_remainder=CashRemainder.objects.get(shop=cho.shop)
                    cash_remainder.remainder = 0
                    cash_remainder.save()
                else:
                    cash_remainder=CashRemainder.objects.create(
                        shop=cho.shop,
                        remainder=0
                    )
            if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=cho.created)
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (cash_remainder.remainder + obj.cash_in - obj.cash_out)
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()
            cho.delete()
            #creating new cho
            if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
                chos = Cash.objects.filter(shop=shop, created__lt=dateTime)  # cash history objects
                cho_before = chos.latest("created")  # cash history object
                cash_remainder=CashRemainder.objects.get(shop=shop)
                cash_remainder.remainder=cho_before.currrent_remainder
                cash_remainder.save()
            else:
                if CashRemainder.objects.filter(shop=shop).exists():
                    cash_remainder=CashRemainder.objects.get(shop=shop)
                    cash_remainder.remainder = 0
                    cash_remainder.save()
                else:
                    cash_remainder=CashRemainder.objects.create(
                        shop=shop,
                        remainder=0
                    )
            new_cho=Cash.objects.create(
                shop=shop,
                created=dateTime,
                document=document,
                user=request.user,
                pre_remainder=cash_remainder.remainder,
                cash_out=document_sum,
                cash_in=0,
                current_remainder=cash_remainder.remainder - document_sum,
            )
            cash_remainder.remainder=new_cho.current_remainder
            cash_remainder.save()
            if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=dateTime)
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (cash_remainder.remainder + obj.cash_in - obj.cash_out)
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()
             # end of operations with cash
            document.sum = document_sum
            document.created = dateTime
            document.save()
            for register in registers:
                register.delete()
            return redirect("log")

        else:
            messages.error(request, "Вы не ввели ни одного наименования")
            return redirect("change_return_posted", document.id)
    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
        }
        return render(request, "documents/change_return_posted.html", context)

def unpost_return(request, document_id):
    document = Document.objects.get(id=document_id)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder -= rho.incoming_quantity
        av_price.sum -= rho.incoming_quantity * av_price.av_price
        # av_price.av_price=av_price.sum/av_price.current_remainder
        av_price.save()

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
    document.posted = False
    document.save()
    #deleting cash operations
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        sequence_chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
        cho_latest_before = sequence_chos_before.latest("created")
        cash_remainder = CashRemainder.objects.get(shop=cho.shop)
        cash_remainder.remainder = cho_latest_before.current_remainder
        cash_remainder.save()
    else:
        cash_remainder = CashRemainder.objects.get(shop=cho.shop)
        cash_remainder.remainder = 0
        cash_remainder.save()

    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        sequence_chos_after = Cash.objects.filter(shop=cho.shop, created__gt=cho.created)
        sequence_chos_after = sequence_chos_after.all().order_by("created")
        for obj in sequence_chos_after:
            obj.pre_remainder = cash_remainder.remainder
            obj.current_remainder = (
                cash_remainder.remainder + obj.cash_in - obj.cash_out
            )
            obj.save()
            cash_remainder.remainder = obj.current_remainder
            cash_remainder.save()
    cho.delete()
    return redirect("log")
#===============================================================================================
def list_sale(request):
    shops = Shop.objects.all()
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        imei = request.POST["IMEI"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        sales = Sale.objects.filter(imei=imei, shop=shop)
        if start_date:
            sales = sales.filter(created__gte=start_date)
        if end_date:
            sales = sales.filter(created__lte=end_date)
        context = {"sales": sales, "shops": shops}
        return render(request, "documents/list_sale.html", context)

    context = {"shops": shops}
    return render(request, "documents/list_sale.html", context)
#=================================================================================================
def identifier_revaluation(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        return redirect("revaluation", identifier.id)
    else:
        return redirect("login")

def check_revaluation(request, identifier_id):
    # shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
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
            product = Product.objects.get(imei=imei)
            # remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
            if Register.objects.filter(
                identifier=identifier, product=product, shop=shop
            ).exists():
                register = Register.objects.get(identifier=identifier, product=product)
                register.quantity += 1
                register.save()
                return redirect("revaluation", identifier.id)
            else:
                register = Register.objects.create(
                    shop=shop, identifier=identifier, product=product
                )
                return redirect("revaluation", identifier.id)
        else:
            messages.error(
                request,
                "Данное наименование отсутствует на данном складе. Вы не можете переоценить его.",
            )
            return redirect("revaluation", identifier.id)

def clear_revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("revaluation", identifier.id)

def delete_line_revaluation(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("revaluation", identifier.id)

def revaluation(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    context = {
        "identifier": identifier,
        "categories": categories,
        "shops": shops,
        "registers": registers,
    }
    return render(request, "documents/revaluation.html", context)

def revaluation_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        shops = request.POST.getlist("shop", None)
        quantities = request.POST.getlist("quantity", None)
        # prices_current=request.POST.getlist('price_current', None)
        prices_new = request.POST.getlist("price_new", None)
        # shop=Shop.objects.get(id=shop)
        if imeis:
            if dateTime:
                # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            else:
                dateTime = datetime.now()
            document = Document.objects.create(
                title=doc_type, user=request.user, created=dateTime
            )
            n = len(names)
            # document_sum=0
            for i in range(n):
                shop = Shop.objects.get(name=shops[i])
                if RemainderHistory.objects.filter(
                    imei=imeis[i], shop=shop, created__lt=dateTime
                ).exists():
                    sequence_rhos_before = RemainderHistory.objects.filter(
                        imei=imeis[i], shop=shop, created__lt=dateTime
                    )
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

# =================================================================================================
def log(request):
    queryset_list = Document.objects.all().order_by("-created")
    doc_types = DocumentType.objects.all()
    users = User.objects.all()
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    if request.method == "POST":
        # shop = request.POST['shop']
        # supplier = request.POST['supplier']
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        user = request.POST["user"]
        supplier = request.POST["supplier"]
        doc_type = request.POST["doc_type"]
        # if shop:
        #     queryset_list = queryset_list.filter(shop=shop)
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        if doc_type:
            doc_type = DocumentType.objects.get(id=doc_type)
            queryset_list = queryset_list.filter(title=doc_type)
        if user:
            queryset_list = queryset_list.filter(user=user)
        if supplier:
            doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
            queryset_list = queryset_list.filter(title=doc_type)
            supplier = Supplier.objects.get(id=supplier)
            new_list = []
            for item in queryset_list:
                if item.delivery.first().supplier == supplier:
                    new_list.append(item)
            queryset_list = new_list
            print(queryset_list)
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        context = {
            "queryset_list": queryset_list,
            "doc_types": doc_types,
            "users": users,
            "suppliers": suppliers,
            "shops": shops,
        }
        return render(request, "documents/log.html", context)

    else:
        context = {
            "queryset_list": queryset_list,
            "doc_types": doc_types,
            "users": users,
            "suppliers": suppliers,
            "shops": shops,
        }
        return render(request, "documents/log.html", context)

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

# ================================Cashback Operations=============================================
def cashback(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        if request.method == "POST":
            phone = request.POST["phone"]
            if Customer.objects.filter(phone=phone).exists():
                client = Customer.objects.get(phone=phone)
                return redirect("cashback_off_choice", identifier.id, client.id)
            else:
                messages.error(
                    request,
                    "Клиент не зарегистрирован в системе. Введите данные клиента.",
                )
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
    if request.user.is_authenticated:
        client = Customer.objects.get(id=client_id)
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        # if request.method=="POST":
        security_code = []
        for i in range(4):
            a = random.randint(0, 9)
            security_code.append(a)
        code_string = "".join(
            str(i) for i in security_code
        )  # transforming every integer into string
        print(code_string)
        # ===========Twilio API==================
        account_sid = "ACb9a5209252abd7219e19a812f8108acc"
        auth_token = ""
        client_twilio = Client(account_sid, auth_token)
        message = client_twilio.messages.create(
            body=code_string, from_="+16624993114", to="+79200711112"
        )
        # ================================
        context = {
            "identifier": identifier,
            "client": client,
            # 'cashback_off': cashback_off,
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
            messages.error(request, "Неверный код. Попробуйте еще раз.")
            return redirect("security_code", identifier.id, client.id)

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

# =========================================Cash_off operations ==============================
def cash_off_salary(request):
    shops = Shop.objects.all()
    users = User.objects.all()
    expense = Expense.objects.get(name="Зарплата")
    if request.method == "POST":
        doc_type = DocumentType.objects.get(name="РКО (зарплата)")
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        cash_receiver = request.POST["user"]
        cash_receiver = User.objects.get(id=cash_receiver)
        last_name = cash_receiver.last_name
        sum = request.POST["sum"]
        sum = int(sum)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        # operations with cash
        if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop, created__lt=dateTime)
            # cash history objects
            cho_before = chos.latest("created")  # cash history object
            cash_pre_remainder = cho_before.current_remainder
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_off_salary")
        if cash_pre_remainder < sum:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_off_salary")
        else:
            document = Document.objects.create(
                title=doc_type, user=request.user, created=dateTime
            )
            cash = Cash.objects.create(
                shop=shop,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                cash_receiver=cash_receiver,
                cash_off_reason=expense,
                pre_remainder=cash_pre_remainder,
                cash_out=sum,
                current_remainder=cash_pre_remainder - sum,
            )
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
            cash_remainder.remainder = cash.current_remainder
            cash_remainder.save()
            if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                sequence_chos_after = Cash.objects.filter(
                    shop=shop, created__gt=document.created
                )
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (
                        cash_remainder.remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()
            # end of operations with cash
            document.sum = sum
            document.save()
            return redirect("log")
    context = {"shops": shops, "users": users}
    return render(request, "documents/cash_off_salary.html", context)

def delete_cash_off_salary(request, document_id):
    document = Document.objects.get(id=document_id)
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
        cho_latest_before = chos_before.latest("created")
        if CashRemainder.objects.filter(shop=cho.shop).exists():
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = cho_latest_before.current_remainder
            cash_remainder.save()
        else:
            cash_remainder = CashRemainder.objects.create(shop=cho.shop, remainder=0)
    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        chos_after = Cash.objects.filter(
            shop=cho.shop, created__gt=cho.created
        ).order_by("created")
        for obj in chos_after:
            obj.pre_remainder = cash_remainder.remainder
            obj.current_remainder = (
                cash_remainder.remainder + obj.cash_in - obj.cash_out
            )
            obj.save()
            cash_remainder.remainder = obj.current_remainder
            cash_remainder.save()

    cho.delete()
    document.delete()
    return redirect("log")

def change_cash_off_salary(request, document_id):
    document = Document.objects.get(id=document_id)
    expense = Expense.objects.get(name="Зарплата")
    shops = Shop.objects.all()
    users = User.objects.all()
    cho = Cash.objects.get(document=document)
    if request.method == "POST":
        dateTime = request.POST["dateTime"]
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        cash_receiver = request.POST["user"]
        cash_receiver = User.objects.get(id=cash_receiver)
        sum = request.POST["sum"]
        sum = int(sum)
        # =====================Checking new cho against cash_remaidner================
        if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
            chos_before = Cash.objects.filter(shop=shop, created__lt=dateTime)
            cho_latest_before = chos_before.latest("created")
            if cho_latest_before.current_remainder < sum:
                messages.error(
                    request,
                    "В кассе недостаточно денежных средств",
                )
                return redirect("change_cash_off_salary", document.id)
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("change_cash_off_salary", document.id)

        # =========================Deleting existing CHO============================
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        else:
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=cho.shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            chos_after = Cash.objects.filter(
                shop=cho.shop, created__gt=cho.created
            ).order_by("created")
            for obj in chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()

        # ====================New CHO=========================
        if (
            Cash.objects.filter(shop=shop, created__lt=dateTime)
            .exclude(document=document)
            .exists()
        ):
            chos_before = Cash.objects.filter(shop=shop, created__lt=dateTime).exclude(
                document=document
            )
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        else:
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        new_cho = Cash.objects.create(
            shop=shop,
            created=dateTime,
            document=document,
            user=request.user,
            cash_off_reason=expense,
            cash_receiver=cash_receiver,
            pre_remainder=cash_remainder.remainder,
            cash_out=sum,
            current_remainder=cash_remainder.remainder - sum,
        )
        cash_remainder.remainder = new_cho.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=dateTime)
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
            # end of operations with cash
        cho.delete()
        document.sum = sum
        document.creted = dateTime
        document.save()
        return redirect("log")

    context = {"document": document, "cho": cho, "shops": shops, "users": users}
    return render(request, "documents/change_cash_off_salary.html", context)

def cash_off_expenses(request):
    shops = Shop.objects.all()
    expenses = Expense.objects.all().exclude(name="Зарплата")
    if request.method == "POST":
        doc_type = DocumentType.objects.get(name="РКО (хоз.расходы)")
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        expense = request.POST["expense"]
        expense = Expense.objects.get(id=expense)
        sum = request.POST["sum"]
        sum = int(sum)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        # operations with cash
        if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop, created__lt=dateTime)
            # cash history objects
            cho_before = chos.latest("created")  # cash history object
            cash_pre_remainder = cho_before.current_remainder
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_off_expenses")
        if cash_pre_remainder < sum:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_off_expenses")
        else:
            document = Document.objects.create(
                title=doc_type, user=request.user, created=dateTime
            )
            cash = Cash.objects.create(
                shop=shop,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                cash_off_reason=expense,
                pre_remainder=cash_pre_remainder,
                cash_out=sum,
                current_remainder=cash_pre_remainder - sum,
            )
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
            cash_remainder.remainder = cash.current_remainder
            cash_remainder.save()
            if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
                sequence_chos_after = Cash.objects.filter(
                    shop=shop, created__gt=document.created
                )
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (
                        cash_remainder.remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()
            # end of operations with cash
            document.sum = sum
            document.save()
            return redirect("log")
    context = {"shops": shops, "expenses": expenses}
    return render(request, "documents/cash_off_expenses.html", context)

def delete_cash_off_expenses(request, document_id):
    document = Document.objects.get(id=document_id)
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
        cho_latest_before = chos_before.latest("created")
        if CashRemainder.objects.filter(shop=cho.shop).exists():
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = cho_latest_before.current_remainder
            cash_remainder.save()
        else:
            cash_remainder = CashRemainder.objects.create(shop=cho.shop, remainder=0)
    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        chos_after = Cash.objects.filter(
            shop=cho.shop, created__gt=cho.created
        ).order_by("created")
        for obj in chos_after:
            obj.pre_remainder = cash_remainder.remainder
            obj.current_remainder = (
                cash_remainder.remainder + obj.cash_in - obj.cash_out
            )
            obj.save()
            cash_remainder.remainder = obj.current_remainder
            cash_remainder.save()

    cho.delete()
    document.delete()
    return redirect("log")

def change_cash_off_expenses(request, document_id):
    document = Document.objects.get(id=document_id)
    expenses = Expense.objects.all().exclude(name="Зарплата")
    shops = Shop.objects.all()
    cho = Cash.objects.get(document=document)
    if request.method == "POST":
        dateTime = request.POST["dateTime"]
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        expense = request.POST["expense"]
        expense = Expense.objects.get(id=expense)
        sum = request.POST["sum"]
        sum = int(sum)
        # =====================Checking new cho against cash_remaidner================
        if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
            chos_before = Cash.objects.filter(shop=shop, created__lt=dateTime)
            cho_latest_before = chos_before.latest("created")
            if cho_latest_before.current_remainder < sum:
                messages.error(
                    request,
                    "В кассе недостаточно денежных средств",
                )
                return redirect("change_cash_off_expense", document.id)
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("change_cash_off_expense", document.id)

        # =========================Deleting existing CHO============================
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        else:
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=cho.shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            chos_after = Cash.objects.filter(
                shop=cho.shop, created__gt=cho.created
            ).order_by("created")
            for obj in chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()

        # ====================New CHO=========================
        if (
            Cash.objects.filter(shop=shop, created__lt=dateTime)
            .exclude(document=document)
            .exists()
        ):
            chos_before = Cash.objects.filter(shop=shop, created__lt=dateTime).exclude(
                document=document
            )
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        else:
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        new_cho = Cash.objects.create(
            shop=shop,
            created=dateTime,
            document=document,
            user=request.user,
            cash_off_reason=expense,
            pre_remainder=cash_remainder.remainder,
            cash_out=sum,
            current_remainder=cash_remainder.remainder - sum,
        )
        cash_remainder.remainder = new_cho.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=dateTime)
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
            # end of operations with cash
        cho.delete()
        document.sum = sum
        document.creted = dateTime
        document.save()
        return redirect("log")

    context = {"document": document, "cho": cho, "shops": shops, "expenses": expenses}
    return render(request, "documents/change_cash_off_expenses.html", context)

def cash_receipt(request):
    vouchers = Voucher.objects.all()
    users = User.objects.all()
    shops = Shop.objects.all()
    if request.method == "POST":
        doc_type = DocumentType.objects.get(name="ПКО")
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
        voucher = request.POST["voucher"]
        voucher = Voucher.objects.get(id=voucher)
        contributor = request.POST["contributor"]
        contributor = User.objects.get(id=contributor)
        sum = request.POST["sum"]
        sum = int(sum)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        if Cash.objects.filter(shop=shop, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop, created__lt=dateTime)
            cho_before = chos.latest("created")  # cash history object
            cash_remainder = CashRemainder.objects.get(shop=shop)
            cash_remainder.remainder = cho_before.current_remainder
            cash_remainder.save()
        else:
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        document = Document.objects.create(
            title=doc_type, user=request.user, created=dateTime
        )
        cash = Cash.objects.create(
            shop=shop,
            created=dateTime,
            document=document,
            cho_type=doc_type,
            user=request.user,
            cash_contributor=contributor,
            cash_in_reason=voucher,
            pre_remainder=cash_remainder.remainder,
            cash_in=sum,
            current_remainder=cash_remainder.remainder + sum,
        )
        cash_remainder.remainder = cash.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(
                shop=shop, created__gt=document.created
            )
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
        # end of operations with cash
        document.sum = sum
        document.save()
        return redirect("log")

    context = {
        "vouchers": vouchers,
        "users": users,
        "shops": shops,
    }
    return render(request, "documents/cash_receipt.html", context)

def delete_cash_receipt(request, document_id):
    document = Document.objects.get(id=document_id)
    cho = Cash.objects.get(document=document)
    if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
        chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
        cho_latest_before = chos_before.latest("created")
        if CashRemainder.objects.filter(shop=cho.shop).exists():
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = cho_latest_before.current_remainder
            cash_remainder.save()
        else:
            cash_remainder = CashRemainder.objects.create(shop=cho.shop, remainder=0)
    if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
        chos_after = Cash.objects.filter(
            shop=cho.shop, created__gt=cho.created
        ).order_by("created")
        for obj in chos_after:
            obj.pre_remainder = cash_remainder.remainder
            obj.current_remainder = (
                cash_remainder.remainder + obj.cash_in - obj.cash_out
            )
            obj.save()
            cash_remainder.remainder = obj.current_remainder
            cash_remainder.save()

    cho.delete()
    document.delete()
    return redirect("log")

def change_cash_receipt(request, document_id):
    document = Document.objects.get(id=document_id)
    vouchers = Voucher.objects.all()
    users = User.objects.all()
    shops = Shop.objects.all()
    cho = Cash.objects.get(document=document)
    if request.method == "POST":
        dateTime = request.POST["dateTime"]
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        voucher = request.POST["voucher"]
        voucher = Voucher.objects.get(id=voucher)
        contributor = request.POST["contributor"]
        contributor = User.objects.filter(id=contributor)
        sum = request.POST["sum"]
        sum = int(sum)

        # =========================Deleting existing CHO============================
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            chos_before = Cash.objects.filter(shop=cho.shop, created__lt=cho.created)
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        else:
            if CashRemainder.objects.filter(shop=cho.shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=cho.shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=cho.shop, remainder=0
                )
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            chos_after = Cash.objects.filter(
                shop=cho.shop, created__gt=cho.created
            ).order_by("created")
            for obj in chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()

        # ====================New CHO=========================
        if (
            Cash.objects.filter(shop=shop, created__lt=dateTime)
            .exclude(document=document)
            .exists()
        ):
            chos_before = Cash.objects.filter(shop=shop, created__lt=dateTime).exclude(
                document=document
            )
            cho_latest_before = chos_before.latest("created")
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        else:
            if CashRemainder.objects.filter(shop=shop).exists():
                cash_remainder = CashRemainder.objects.filter(shop=shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(shop=shop, remainder=0)
        new_cho = Cash.objects.create(
            shop=shop,
            created=dateTime,
            document=document,
            user=request.user,
            cash_in_reason=voucher,
            cash_contributor=contributor,
            pre_remainder=cash_remainder.remainder,
            cash_out=sum,
            current_remainder=cash_remainder.remainder + sum,
        )
        cash_remainder.remainder = new_cho.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(shop=shop, created__gt=dateTime)
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
            # end of operations with cash
        cho.delete()
        document.sum = sum
        document.creted = dateTime
        document.save()
        return redirect("log")

    context = {
        "document": document,
        "cho": cho,
        "shops": shops,
        "vouchers": vouchers,
        "users": users,
    }
    return render(request, "documents/change_cash_receipt.html", context)

def cash_movement(request):
    shops = Shop.objects.all()
    if request.method == "POST":
        doc_type = DocumentType.objects.get(name="Перемещение денег")
        shop_cash_sender = request.POST["shop_cash_sender"]
        shop_cash_sender = Shop.objects.get(id=shop_cash_sender)
        shop_cash_receiver = request.POST["shop_сash_receiver"]
        shop_cash_receiver = Shop.objects.get(id=shop_cash_receiver)
        dateTime = request.POST["dateTime"]
        sum = request.POST["sum"]
        sum = int(sum)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()

        # SHOP SENDER OPERATIONS
        # checking if cash remainder is enough to send the the sum indicated
        if Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime)
            cho_before = chos.latest("created")  # cash history object
            cash_pre_remainder = cho_before.current_remainder
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_movement")
        if cash_pre_remainder < sum:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_movement")
        else:
            document = Document.objects.create(
                title=doc_type, user=request.user, created=dateTime
            )
            cash = Cash.objects.create(
                shop=shop_cash_sender,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                pre_remainder=cash_pre_remainder,
                cash_out=sum,
                current_remainder=cash_pre_remainder - sum,
            )
            if CashRemainder.objects.filter(shop=shop_cash_sender).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop_cash_sender)
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=shop_cash_sender, remainder=0
                )
            cash_remainder.remainder = cash.current_remainder
            cash_remainder.save()
            if Cash.objects.filter(
                shop=shop_cash_sender, created__gt=dateTime
            ).exists():
                sequence_chos_after = Cash.objects.filter(
                    shop=shop_cash_sender, created__gt=document.created
                )
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (
                        cash_remainder.remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()

        # SHOP RECEIVER OPERATIONS
        if Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime)
            cho_before = chos.latest("created")  # cash history object
            cash_remainder = CashRemainder.objects.get(shop=shop_cash_receiver)
            cash_remainder.remainder = cho_before.current_remainder
            cash_remainder.save()
        else:
            if CashRemainder.objects.filter(shop=shop_cash_receiver).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop_cash_receiver)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=shop_cash_receiver, remainder=0
                )
        cash = Cash.objects.create(
            shop=shop_cash_receiver,
            created=dateTime,
            document=document,
            cho_type=doc_type,
            user=request.user,
            pre_remainder=cash_remainder.remainder,
            cash_in=sum,
            current_remainder=cash_remainder.remainder + sum,
        )
        cash_remainder.remainder = cash.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop_cash_receiver, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(
                shop=shop_cash_receiver, created__gt=document.created
            )
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
        document.sum = sum
        document.save()
        return redirect("log")

    context = {"shops": shops}
    return render(request, "documents/cash_movement.html", context)

def delete_cash_movement(request, document_id):
    document = Document.objects.get(id=document_id)
    chos = Cash.objects.filter(document=document)
    for cho in chos:
        if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
            sequence_chos_before = Cash.objects.filter(
                shop=cho.shop, created__lt=cho.created
            )
            cho_latest_before = sequence_chos_before.latest("created")
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = cho_latest_before.current_remainder
            cash_remainder.save()
        else:
            cash_remainder = CashRemainder.objects.get(shop=cho.shop)
            cash_remainder.remainder = 0
            cash_remainder.save()
        if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
            sequence_chos_after = Cash.objects.filter(
                shop=cho.shop, created__gt=cho.created
            )
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
        cho.delete()
    document.delete()
    return redirect("log")

def change_cash_movement(request, document_id):
    document = Document.objects.get(id=document_id)
    doc_type = DocumentType.objects.get(name="Перемещение денег")
    shops = Shop.objects.all()
    chos = Cash.objects.filter(document=document)
    if request.method == "POST":
        dateTime = request.POST["dateTime"]
        shop_cash_sender = request.POST["shop_cash_sender"]
        shop_cash_sender = Shop.objects.get(id=shop_cash_sender)
        shop_cash_receiver = request.POST["shop_cash_receiver"]
        shop_cash_receiver = Shop.objects.get(id=shop_cash_receiver)
        sum = request.POST["sum"]
        sum = int(sum)
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = document.created
        # DELETING EXISTING CHOS
        for cho in chos:
            if Cash.objects.filter(shop=cho.shop, created__lt=cho.created).exists():
                sequence_chos_before = Cash.objects.filter(
                    shop=cho.shop, created__lt=cho.created
                )
                cho_latest_before = sequence_chos_before.latest("created")
                cash_remainder = CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder = cho_latest_before.current_remainder
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.get(shop=cho.shop)
                cash_remainder.remainder = 0
                cash_remainder.save()
            if Cash.objects.filter(shop=cho.shop, created__gt=cho.created).exists():
                sequence_chos_after = Cash.objects.filter(
                    shop=cho.shop, created__gt=cho.created
                )
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (
                        cash_remainder.remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()
            cho.delete()
        # CREATING NEW CHOS
        # SHOP_CASH_SENDER OPERATIONS
        if Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop_cash_sender, created__lt=dateTime)
            cho_before = chos.latest("created")  # cash history object
            cash_pre_remainder = cho_before.current_remainder
        else:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_movement")
        if cash_pre_remainder < sum:
            messages.error(
                request,
                "В кассе недостаточно денежных средств",
            )
            return redirect("cash_movement")
        else:
            cash_sender = Cash.objects.create(
                shop=shop_cash_sender,
                created=dateTime,
                document=document,
                cho_type=doc_type,
                user=request.user,
                pre_remainder=cash_pre_remainder,
                cash_out=sum,
                current_remainder=cash_pre_remainder - sum,
            )
            if CashRemainder.objects.filter(shop=shop_cash_sender).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop_cash_sender)
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=shop_cash_sender, remainder=0
                )
            cash_remainder.remainder = cash_sender.current_remainder
            cash_remainder.save()
            if Cash.objects.filter(
                shop=shop_cash_sender, created__gt=dateTime
            ).exists():
                sequence_chos_after = Cash.objects.filter(
                    shop=shop_cash_sender, created__gt=document.created
                )
                sequence_chos_after = sequence_chos_after.all().order_by("created")
                for obj in sequence_chos_after:
                    obj.pre_remainder = cash_remainder.remainder
                    obj.current_remainder = (
                        cash_remainder.remainder + obj.cash_in - obj.cash_out
                    )
                    obj.save()
                    cash_remainder.remainder = obj.current_remainder
                    cash_remainder.save()

        # SHOP RECEIVER OPERATIONS
        if Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime).exists():
            chos = Cash.objects.filter(shop=shop_cash_receiver, created__lt=dateTime)
            cho_before = chos.latest("created")  # cash history object
            cash_remainder = CashRemainder.objects.get(shop=shop_cash_receiver)
            cash_remainder.remainder = cho_before.current_remainder
            cash_remainder.save()
        else:
            if CashRemainder.objects.filter(shop=shop_cash_receiver).exists():
                cash_remainder = CashRemainder.objects.get(shop=shop_cash_receiver)
                cash_remainder.remainder = 0
                cash_remainder.save()
            else:
                cash_remainder = CashRemainder.objects.create(
                    shop=shop_cash_receiver, remainder=0
                )
        cash = Cash.objects.create(
            shop=shop_cash_receiver,
            created=dateTime,
            document=document,
            cho_type=doc_type,
            user=request.user,
            pre_remainder=cash_remainder.remainder,
            cash_in=sum,
            current_remainder=cash_remainder.remainder + sum,
        )
        cash_remainder.remainder = cash.current_remainder
        cash_remainder.save()
        if Cash.objects.filter(shop=shop_cash_receiver, created__gt=dateTime).exists():
            sequence_chos_after = Cash.objects.filter(
                shop=shop_cash_receiver, created__gt=document.created
            )
            sequence_chos_after = sequence_chos_after.all().order_by("created")
            for obj in sequence_chos_after:
                obj.pre_remainder = cash_remainder.remainder
                obj.current_remainder = (
                    cash_remainder.remainder + obj.cash_in - obj.cash_out
                )
                obj.save()
                cash_remainder.remainder = obj.current_remainder
                cash_remainder.save()
        document.sum = sum
        document.save()
        return redirect("log")

    else:
        context = {
            "document": document,
            "shops": shops,
        }
        return render(request, "documents/change_cash_movement.html", context)

# ========================================End of cash_off operations ============================
def inventory(request):
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)
        dateTime = request.POST["dateTime"]
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = datetime.now()
        if RemainderCurrent.objects.filter(category=category, shop=shop).exists():
            queryset = RemainderCurrent.objects.filter(category=category, shop=shop)
        else:
            messages.error(
                request,
                "Товаров данной категории на данном складе не найдено",
            )
            return redirect("inventory")

        сontext = {"queryset": queryset, "shops": shops, "categories": categories}
        return render(request, "documents/inventory.html", сontext)
    context = {"shops": shops, "categories": categories}
    return render(request, "documents/inventory.html", context)
