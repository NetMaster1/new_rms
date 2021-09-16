from django.db.models.fields import NullBooleanField
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
from app_reference.models import Shop, Supplier, Product, ProductCategory, DocumentType
from app_cash.models import Cash, CashRemainder, Credit, Card
from app_cashback.models import Cashback
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.utils import timezone
from django.contrib import messages
import decimal
import random
import pandas
import datetime
import pytz
from twilio.rest import Client

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        # auth.logout(request)
        return redirect("login")


def close_without_save(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if Register.objects.filter(identifier=identifier).exists():
        registers = Register.objects.filter(identifier=identifier)
        for register in registers:
            register.delete()
        identifier.delete()
        return redirect("index")
    else:
        identifier.delete()
        return redirect("index")


def close_edited_document(request, identifier_id):
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
                        shop=shop,
                        # category=category,
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
                        # category=category,
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
                        # category=category,
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


# =======================================================================================
def delivery_auto(request):
    shops = Shop.objects.all()
    suppliers = Supplier.objects.all()
    categories = ProductCategory.objects.all()
    if request.method == "POST":
        # shop = request.POST['shop']
        # shop=Shop.objects.get(id=shop)
        # supplier = request.POST['supplier']
        # supplier=Supplier.objects.get(id=supplier)
        # category = request.POST['category']
        # category=ProductCategory.objects.get(id=category)
        file = request.FILES['file_name']
        print(file)

        df1 = pandas.read_excel(file)
        #df1 = pandas.read_excel('Delivery_21_06_21.xlsx')
        cycle = len(df1)
        for i in range(cycle):
            row = df1.iloc[i]
            print(row)

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

            # context= {
            #     'suppliers': suppliers,
            #     # 'shops': shops,
            #     'categories': categories,
            #     'identifier': identifier,
            #     'registers': registers
            # }
            # return render (request, 'documents/delivery.html', context)


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


def enter_new_product(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category = ProductCategory.objects.get(id=category)
        product = Product.objects.create(name=name, imei=imei, category=category)
        return redirect("delivery", identifier.id)
    else:
        return redirect("delivery", identifier.id)


def delivery_input(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    if request.method == "POST":
        shop = request.POST["shop"]
        dateTime = request.POST["dateTime"]
        # category=request.POST['category']
        imeis = request.POST.getlist("imei", None)
        names = request.POST.getlist("name", None)
        quantities = request.POST.getlist("quantity", None)
        prices = request.POST.getlist("price", None)
        try:
            supplier = request.POST["supplier"]
        except:
            messages.error(request, "Введите поставщика")
            return redirect("delivery", identifier.id)
        shop = Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)
        supplier = Supplier.objects.get(id=supplier)

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
                # imei=imeis[i]
                delivery_item = Delivery.objects.create(
                    document=document,
                    # category=category,
                    created=dateTime,
                    supplier=supplier,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price=prices[i],
                    quantity=quantities[i],
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += delivery_item.sub_total
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
                    # sub_total= int(int(quantities[i]) * int(prices[i])),
                )
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

            document.sum = document_sum
            document.save()
            for register in registers:
                register.delete()
            identifier.delete()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("delivery", identifier.id)


def delete_delivery(request, document_id):
    document = Document.objects.get(id=document_id)
    deliveries = Delivery.objects.filter(document=document)
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
    for delivery in deliveries:
        delivery.delete()
    document.delete()
    return redirect("log")


def pre_change_delivery(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document)
    shop_current = rhos.first().shop
    identifier = Identifier.objects.create()
    for rho in rhos:
        product = Product.objects.get(imei=rho.imei)
        register = Register.objects.create(
            product=product,
            quantity=rho.incoming_quantity,
            price=rho.wholesale_price,
            identifier=identifier,
            sub_total=rho.wholesale_price * rho.incoming_quantity,
        )
    return redirect("change_delivery", document.id, identifier.id)


def change_delivery(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    rhos = RemainderHistory.objects.filter(document=document)
    # deliveries=Delivery.objects.filter(document=document)
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    shop_current = rhos.first().shop
    registers = Register.objects.filter(identifier=identifier)

    # if RemainderHistory.objects.filter(document=document).exists():
    #     rem_hist_objs=RemainderHistory.objects.filter(document=document)

    # else:
    #     document.delete()
    #     return redirect ('log')

    if request.method == "POST":
        try:
            supplier = request.POST["supplier"]
        except:
            messages.error(request, "Введите поставщика")
            return redirect("change_delivery", document.id, identifier.id)
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        dateTime = request.POST["dateTime"]
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
                # creating remainder_history
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
            identifier.delete()
            return redirect("log")
    else:
        context = {
            "registers": registers,
            "document": document,
            "shops": shops,
            "suppliers": suppliers,
            "identifier": identifier,
        }
        return render(request, "documents/change_delivery.html", context)


def delete_line_change_delivery(request, document_id, identifier_id, imei):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(identifier=identifier, product=product)
    item.delete()
    # for item in items:
    #     item.delete()
    return redirect("change_delivery", document.id, identifier.id)


def check_delivery_change(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
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
                return redirect("change_delivery", document.id, identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier, product=product
                )
                return redirect("change_delivery", document.id, identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("change_delivery", document.id, identifier.id)


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
    if "imei" in request.GET:
        imei = request.GET["imei"]
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


def delete_line_transfer(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.filter(identifier=identifier_id, product=product)
    item.delete()
    return redirect("transfer", identifier.id)


def transfer_input(request, identifier_id):
    if request.user.is_authenticated:
        identifier = Identifier.objects.get(id=identifier_id)
        registers = Register.objects.filter(identifier=identifier)
        doc_type = DocumentType.objects.get(name="Перемещение ТМЦ")
        if request.method == "POST":
            # imeis=request.GET.getlist('imei', None )
            # names=request.GET.getlist('name', None )
            # prices=request.GET.getlist('price', None )
            # quantities=request.GET.getlist('quantity', None )
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
                return redirect("transfer", identifier.id)
            else:
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
                        created=dateTime, title=doc_type, user=request.user
                    )
                    sum = 0
                    for i in range(n):
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

                                # if obj.document.title.name =='Перемещение ТМЦ':
                                #     obj.pre_remainder=remainder_current.current_remainder
                                #     obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                                #     obj.av_price=remainder_current.av_price
                                #     obj.sub_total=remainder_current.av_price*obj.current_remainder
                                #     obj.save()
                                #     remainder_current.current_remainder=obj.current_remainder
                                #     remainder_current.total_av_price=obj.sub_total
                                #     remainder_current.av_price=obj.av_price
                                #     remainder_current.save()
                                #     av_price_sequence=remainder_current.av_price

                                #     document_new=Document.objects.get(id=obj.document)
                                #     shop_receiver= document_new.transfer_set.first().shop_receiver
                                #     if shop_receiver!=remainder_history.shop:
                                #         rho_receiver=RemainderHistory.objects.get(imei=imeis[i], shop=shop_receiver, document=document_new.id)
                                #         if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__lt=rho_receiver.created).exists():
                                #             rhos_receiver_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__lt=rho_receiver.created)
                                #             rho_receiver_before=rhos_receiver_before.latest('created')
                                #             rho_receiver.pre_remainder=rho_receiver_before.current_remainder
                                #             rho_receiver.current_remainder=rho_receiver_before.pre_remainder+rho_receiver.incoming_quantity-rho_receiver.outgoing_quantity
                                #             rho_receiver.sub_total=(rho_receiver_before.current_remainder*rho_receiver_before.av_price)+(rho_receiver.incoming_quantity-rho_receiver.outgoing_quantity)*av_price_sequence
                                #             rho_receiver.av_price=rho_receiver.sub_total/rho_receiver.current_remainder
                                #             rho_receiver.save()
                                #             remainder_current=RemainderHistory.objects.get(imei=imeis[i], shop=shop_receiver)
                                #             remainder_current.av_price=rho_receiver.av_price
                                #             remainder_current.total_av_price=rho_receiver.sub_total
                                #             remainder_current.current_remainder=rho_receiver.current_remainder
                                #             remainder_current.save()

                                # if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, document=document_new.id, created__gt=dateTime).exists():
                                #     new_sequence=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__gt=dateTime, document=document_new)
                                #     for new_obj in new_sequence:
                                #         new_obj.sub_total=new_obj.current_remainder*remainder_current.av_price
                                #         new_obj.av_price=remainder_current.av_price
                                #         new_obj.save()
                                #         remainder_current_new=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver)
                                #         remainder_current_new.av_price=new_obj.av_price
                                #         remainder_current_new.total_av_price=new_obj.sub_total
                                #         remainder_current_new.save()
                                # else:
                                obj.pre_remainder = remainder_current.current_remainder
                                obj.current_remainder = (
                                    remainder_current.current_remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )

                                # if obj.document.title.name =='Перемещение ТМЦ':
                                #     obj.sub_total=remainder_current.total_av_price+(obj.incoming_quantity-obj.outgoing_quantity) * remainder_current.av_price
                                # else:
                                #     obj.sub_total=remainder_current.total_av_price+(obj.incoming_quantity-obj.outgoing_quantity)*obj.wholesale_price
                                # obj.av_price=obj.sub_total/obj.current_remainder
                                obj.save()
                                remainder_current.current_remainder = (
                                    obj.current_remainder
                                )
                                # remainder_current.total_av_price=obj.sub_total
                                # remainder_current.av_price=obj.av_price
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

                                # if obj.document.title.name =='Перемещение ТМЦ':
                                #     obj.pre_remainder=remainder_current.current_remainder
                                #     obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                                #     obj.av_price=remainder_current.av_price
                                #     obj.sub_total=remainder_current.av_price*obj.current_remainder
                                #     obj.save()
                                #     remainder_current.current_remainder=obj.current_remainder
                                #     remainder_current.total_av_price=obj.sub_total
                                #     remainder_current.av_price=obj.av_price
                                #     remainder_current.save()

                                #     document_new=Document.objects.get(id=obj.document)
                                #     shop_receiver= document_new.transfer_set.first().shop_receiver
                                #     if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, document=document_new.id, created__gt=dateTime).exists():
                                #         new_sequence=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver, created__gt=dateTime, document=document_new)
                                #         for new_obj in new_sequence:
                                #             new_obj.sub_total=new_obj.current_remainder*remainder_current.av_price
                                #             new_obj.av_price=remainder_current.av_price
                                #             new_obj.save()
                                #             remainder_current_new=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver)
                                #             remainder_current_new.av_price=new_obj.av_price
                                #             remainder_current_new.total_av_price=new_obj.sub_total
                                #             remainder_current_new.save()
                                # else:
                                obj.pre_remainder = remainder_current.current_remainder
                                obj.current_remainder = (
                                    remainder_current.current_remainder
                                    + obj.incoming_quantity
                                    - obj.outgoing_quantity
                                )

                                # if obj.document.title.name =='Перемещение ТМЦ':
                                #     document_new=Document.objects.get(id=obj.document)
                                #     query=RemainderHistory.objects.filter(document=document_new, imei=obj.imei)
                                #     rho=query.exclude(shop=shop_receiver)
                                #     av_price_prev=rho[0].av_price
                                #     obj.sub_total=remainder_current.total_av_price+(obj.incoming_quantity-obj.outgoing_quantity) * av_price_prev
                                # else:
                                #     obj.sub_total=remainder_current.total_av_price+(obj.incoming_quantity-obj.outgoing_quantity) * remainder_current.av_price
                                #     obj.av_price=obj.sub_total/obj.current_remainder

                                obj.save()
                                remainder_current.current_remainder = (
                                    obj.current_remainder
                                )
                                # remainder_current.total_av_price=obj.sub_total
                                # remainder_current.av_price=obj.av_price
                                remainder_current.save()

                        transfer = Transfer.objects.create(
                            created=dateTime,
                            document=document,
                            shop_sender=shop_sender,
                            shop_receiver=shop_receiver,
                            imei=imeis[i],
                            price=int(prices[i]),
                            name=names[i],
                            quantity=int(quantities[i]),
                            sub_total=int(prices[i]) * int(quantities[i]),
                        )
                        sum += transfer.sub_total

                    document.sum = sum
                    document.save()
                    for register in registers:
                        register.delete()
                    identifier.delete()
                    return redirect("log")
        else:
            return redirect("transfer", identifier.id)
    else:
        auth.logout(request)
        return redirect("login")


def delete_transfer(request, document_id):
    document = Document.objects.get(id=document_id)
    transfers = Transfer.objects.filter(document=document)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
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
    for transfer in transfers:
        transfer.delete()
    document.delete()
    return redirect("log")


def pre_change_transfer(request, document_id):
    document = Document.objects.get(id=document_id)
    rhos = RemainderHistory.objects.filter(document=document)
    transfers = Transfer.objects.filter(document=document)
    # shop_current=rhos.first().shop
    identifier = Identifier.objects.create()
    for transfer in transfers:
        product = Product.objects.get(imei=transfer.imei)
        register = Register.objects.create(
            product=product,
            quantity=transfer.quantity,
            price=transfer.price,
            identifier=identifier,
            sub_total=transfer.price * transfer.quantity,
        )
    return redirect("change_transfer", document.id, identifier.id)


def check_transfer_change(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    transfers = Transfer.objects.filter(document=document)
    shop_receiver_current = transfers.first().shop_receiver
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST["imei_check"]
        quantity = request.POST["quantity_input"]
        quantity = int(quantity)
        # price=request.POST['price']
        # price=int(price)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(
                shop=shop_receiver_current, imei=imei
            ).exists():
                print("ok")
                remainder_current = RemainderCurrent.objects.get(
                    shop=shop_receiver_current, imei=imei
                )
                retail_price = remainder_current.retail_price
            else:
                retail_price = 0
            product = Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                register = Register.objects.get(identifier=identifier, product=product)
                register.quantity += quantity
                register.save()
                register.sub_total = register.price * register.quantity
                register.save()
                return redirect("change_transfer", document.id, identifier.id)
            else:
                register = Register.objects.create(
                    identifier=identifier,
                    product=product,
                    quantity=quantity,
                    price=retail_price,
                )
                register.sub_total = register.quantity * register.price
                register.save()
                return redirect("change_transfer", document.id, identifier.id)
        else:
            messages.error(
                request, "Данное наименование отсутствует в БД. Введите его."
            )
            return redirect("change_transfer", document.id, identifier.id)


def delete_line_change_transfer(request, document_id, identifier_id, imei):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    item = Register.objects.get(identifier=identifier, product=product)
    item.delete()
    # for item in items:
    #     item.delete()
    return redirect("change_transfer", document.id, identifier.id)


def change_transfer(request, document_id, identifier_id):
    document = Document.objects.get(id=document_id)
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    transfers = Transfer.objects.filter(document=document)
    transfer_shops = transfers[0]
    shop_sender_current = transfer_shops.shop_sender
    shop_receiver_current = transfer_shops.shop_receiver
    shops = Shop.objects.all()
    rem_hist_objs = RemainderHistory.objects.filter(document=document)
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
        # for i in range(n)
        # date has been changed
        if dateTime:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
        else:
            dateTime = document.created

        for transfer in transfers:
            transfer.delete()
        # for transfer, i in zip (transfers, range(n)):
        for i in range(n):
            transfer = Transfer.objects.create(
                created=dateTime,
                document=document,
                name=names[i],
                imei=imeis[i],
                shop_sender=shop_sender_changed,
                shop_receiver=shop_receiver_changed,
                price=prices[i],
                quantity=quantities[i],
                sub_total=int(prices[i]) * int(quantities[i]),
            )
            sum += transfer.sub_total

        for rho in rem_hist_objs:
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
        return redirect("log")
    else:
        context = {
            "document": document,
            "identifier": identifier,
            "registers": registers,
            "transfers": transfers,
            "shops": shops,
            "shop_sender_current": shop_sender_current,
            "shop_receiver_current": shop_receiver_current,
        }
        return render(request, "documents/change_transfer.html", context)


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
        imei = request.POST["imei"]
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


def recognition(request, identifier_id):
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
    return render(request, "documents/recognition.html", context)


def delete_line_recognition(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("recognition", identifier.id)


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
        shop = Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)

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
                # imei=imeis[i]
                recognition_item = Recognition.objects.create(
                    document=document,
                    # category=category,
                    created=dateTime,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price=prices[i],  # retail price
                    quantity=quantities[i],
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += recognition_item.sub_total
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
                    # sub_total= int(int(quantities[i]) * int(prices[i])),
                )
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

            document.sum = document_sum
            document.save()
            for register in registers:
                register.delete()
            identifier.delete()
            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("recognition", identifier.id)


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


def signing_off(request, identifier_id):
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
    return render(request, "documents/signing_off.html", context)


def delete_line_signing_off(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("signing_off", identifier.id)


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
        # prices=request.POST.getlist('price', None)
        shop = Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)
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
                # imei=imeis[i]
                signing_off_item = SignOff.objects.create(
                    document=document,
                    # category=category,
                    created=dateTime,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    # price=prices[i],
                    quantity=quantities[i],
                    # sub_total=int(quantities[i]) * int(prices[i])
                )
                document_sum += signing_off_item.sub_total
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
                    messages.error(
                        request,
                        "Данное наименование отсутсвует на балансе. Вы не можете его списать.",
                    )
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
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=0,
                    outgoing_quantity=quantities[i],
                    current_remainder=remainder_current.current_remainder
                    - int(quantities[i]),
                    # wholesale_price=int(prices[i]),
                    sub_total=int(quantities[i]) * av_price_obj.av_price,
                )

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


def return_doc(request, identifier_id):
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
    return render(request, "documents/return_doc.html", context)


def delete_line_return(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("return_doc", identifier.id)


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
        shop = Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)
        # supplier=Supplier.objects.get(id=supplier)
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
                # imei=imeis[i]
                return_item = Returning.objects.create(
                    document=document,
                    created=dateTime,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price=prices[i],
                    quantity=quantities[i],
                    sub_total=int(quantities[i]) * int(prices[i]),
                )
                document_sum += return_item.sub_total
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
                    shop=shop,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=remainder_current.current_remainder
                    + int(quantities[i]),
                    # sub_total= int(int(quantities[i]) * int(prices[i])),
                )
                remainder_current.current_remainder = (
                    remainder_history.current_remainder
                )
                remainder_current.save()
                if AvPrice.objects.filter(imei=imeis[i]).exists():
                    av_price_obj = AvPrice.objects.get(imei=imeis[i])
                    av_price_obj.current_remainder += int(quantities[i])
                    av_price_obj.sum += int(quantities[i]) * av_price_obj.av_price
                    # av_price_obj.av_price=av_price_obj.sum/av_price_obj.current_remainder
                    av_price_obj.save()
                else:
                    messages.error(
                        request,
                        "Данное наименование никогда не было учтено на балансе фирмы. Вы не можете сделать возврат",
                    )
                    return redirect("return_doc", identifier.id)
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
            document.save()

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
                cash_out=document_sum,
                cash_in=0,
                current_remainder=cash_pre_remainder - document_sum,
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

            for register in registers:
                register.delete()
            identifier.delete()

            return redirect("log")
        else:
            messages.error(request, "Вы не ввели ни одного наименования.")
            return redirect("return_doc", identifier.id)


def delete_return(request, document_id):
    document = Document.objects.get(id=document_id)
    returns = Returning.objects.filter(document=document)
    remainder_history_objects = RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        av_price = AvPrice.objects.get(imei=rho.imei)
        av_price.current_remainder -= rho.incoming_quantity
        av_price.sum -= rho.incoming_quantity * av_price.av_price
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

    for returning in returns:
        returning.delete()
    document.delete()
    return redirect("log")


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


def clear_return(request, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    registers = Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect("revaluation", identifier.id)


def delete_line_return(request, imei, identifier_id):
    identifier = Identifier.objects.get(id=identifier_id)
    product = Product.objects.get(imei=imei)
    items = Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect("revaluation", identifier.id)


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


def file_uploading(request):
    pass
