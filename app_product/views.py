from app_clients.models import Client
from app_personnel.models import BonusAccount
from django.shortcuts import render, redirect, get_object_or_404
from . models import Document, Delivery, Sale, Transfer, Remainder, Register, Identifier
import datetime
from datetime import datetime, date
from app_reference.models import Shop, Supplier, Product, ProductCategory
from app_cash.models import Cash, CashRemainder, Credit, Card
from app_clients.models import Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages


# Create your views here.


def index (request):
    return render(request, 'index.html')

def close_without_save(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if Register.objects.filter(identifier=identifier).exists():
        registers=Register.objects.filter(identifier=identifier)
        for register in registers:
            register.delete()
        identifier.delete()
        return redirect('index')
    else:
        identifier.delete()
        return redirect('index')

def clear_transfer(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect ('transfer', identifier.id)

def clear_delivery(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect ('delivery', identifier.id)

def clear_sale(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect ('sale', identifier.id)

def identifier_sale (request):
    if request.user.is_authenticated:
        identifier=Identifier.objects.create()
        return redirect ('sale', identifier.id)
    else:
        return redirect ('login')

def check_sale(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    shops=Shop.objects.all()
    if request.method == 'POST':
        shop=request.POST['shop']
        imei=request.POST['imei']
        quantity=request.POST['quantity']
        quantity=int(quantity)
        shop=Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if Remainder.objects.filter(imei=imei, shop=shop).exists():
                remainder=Remainder.objects.get(imei=imei, shop=shop)
                if remainder.quantity_remainder < quantity:
                    messages.error(request, 'Количество, необходимое для продажи отсутствует на данном складе')
                    return redirect ('sale', identifier.id)
                else:
                    product=Product.objects.get(imei=imei)
                    if Register.objects.filter(identifier=identifier, product=product).exists():
                        register=Register.objects.get(identifier=identifier, product=product)
                        register.quantity +=quantity
                        register.save()
                        register.sub_total=register.price*register.quantity
                        register.save()
                        return redirect ('sale', identifier.id) 
                    else:
                        register=Register.objects.create(
                            shop=shop,
                            quantity=quantity,
                            identifier=identifier,
                            product=product,
                            price=remainder.retail_price,
                            sub_total=quantity*remainder.retail_price
                        )
                        return redirect ('sale', identifier.id)
            else:
                messages.error(request, 'Данное наименование для продажи отсутствует на данном складе')            
                return redirect ('sale', identifier.id)        
        else:
            messages.error(request, 'Данное наименование для продажи отсутствует в базе данных')            
            return redirect ('sale', identifier.id)
      
def sale(request, identifier_id):
    if request.user.is_authenticated:
        
        identifier=Identifier.objects.get(id=identifier_id)
        shops=Shop.objects.all()
        sum=0
        registers= Register.objects.filter(identifier=identifier)
        for register in registers:
            sum += register.sub_total

        context={
            'identifier': identifier,
            'registers': registers,
            'shops': shops,
            'sum': sum
        }
        return render(request, 'documents/sale.html', context)
    else:
        return redirect ('login')

def delete_line_sale(request, imei, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    product=Product.objects.get(imei=imei)
    item=Register.objects.filter(identifier=identifier, product=product)
    item.delete()
    return redirect ('sale', identifier.id)

def identifier_delivery (request):
    identifier=Identifier.objects.create()
    return redirect ('delivery', identifier.id)

def check_delivery(request, identifier_id):
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    identifier=Identifier.objects.get(id=identifier_id) 
    registers=Register.objects.filter(identifier=identifier)
    # if 'imei' in request.GET:
    if request.method == "POST":
        imei = request.POST['imei']
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            if Register.objects.filter(identifier=identifier, product=product).exists():
                register=Register.objects.get(identifier=identifier, product=product)
                register.quantity +=1
                register.save()
                return redirect('delivery', identifier.id)
            else:
                register=Register.objects.create(
                    identifier = identifier,
                    product=product
                )
                return redirect('delivery', identifier.id)
        else:
            messages.error(request, 'Данное наименование отсутствует в БД. Введите его.')
            
            context= {
                'suppliers': suppliers,
                'shops': shops,
                'categories': categories,
                'identifier': identifier,
                'registers': registers
            }
            return render (request, 'documents/delivery.html', context)

def delivery(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    categories=ProductCategory.objects.all()
    suppliers=Supplier.objects.all()
    shops=Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    context={
        'identifier': identifier,
        'categories': categories,
        'suppliers': suppliers,
        'shops': shops,
        'registers': registers
    }
    return render(request, 'documents/delivery.html', context)

def delete_line_delivery(request, imei, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    product=Product.objects.get(imei=imei)
    items=Register.objects.filter(identifier=identifier, product=product)
    for item in items:
        item.delete()
    return redirect ('delivery', identifier.id)

def enter_new_product (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method == 'POST':
        name=request.POST['name']
        imei=request.POST['imei']
        category=request.POST['category']
        category=ProductCategory.objects.get(id=category)
        product=Product.objects.create(
            name=name,
            imei=imei,
            category=category
        )
        return redirect('delivery', identifier.id)
    else:
        return redirect('delivery', identifier.id)

def delivery_input(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    if request.method == 'POST':
        shop=request.POST['shop']
        supplier=request.POST['supplier']
        category=request.POST['category']
        imeis=request.POST.getlist('imei', None )
        names=request.POST.getlist('name', None )
        quantities=request.POST.getlist('quantity', None)
        prices=request.POST.getlist('price', None)
        shop=Shop.objects.get(id=shop)
        category=ProductCategory.objects.get(id=category)
        supplier=Supplier.objects.get(id=supplier)
        if imeis:
            document=Document.objects.create(
                title= 'Поступление ТМЦ',
                user= request.user
            )
            n=len(names) 
            for i in range(n):
                imei=imeis[i]
                delivery_item=Delivery.objects.create(
                    document=document,
                    category=category,
                    supplier=supplier,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price=prices[i],
                    quantity=quantities[i],
                )
                if Remainder.objects.filter(imei=imei, shop=shop).exists():
                    remainder=Remainder.objects.get(imei=imei, shop=shop)
                    remainder.quantity_remainder += int(quantities[i])
                    remainder.sub_total += int(quantities[i])*int(prices[i])
                    remainder.save()
                    remainder.av_price= remainder.sub_total/remainder.quantity_remainder
                    remainder.save()
                else:
                    remainder=Remainder.objects.create(
                        category=category,
                        shop=shop,
                        name=names[i],
                        imei=imeis[i],
                        quantity_remainder=quantities[i],
                        sub_total=int(quantities[i]) * int(prices[i]),
                        av_price=prices[i]
                    )
            for register in registers:
                register.delete()
            identifier.delete()
            return redirect ('index')
        else:
            messages.error(request, 'Вы не ввели ни одного наименования.')
            return redirect('delivery', identifier.id)


def file_uploading(request):
    pass

def identifier_transfer (request):
    identifier=Identifier.objects.create()
    return redirect ('transfer', identifier.id)

def transfer (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    shops=Shop.objects.all()
    if request.method == 'POST':
        # imeis= request.POST.getlist ('imei', None)
        sender_shop = request.POST['sender_shop']
        receiver_shop = request.POST['receiver_shop']
        imei = request.POST['imei']
        name = request.POST['name']
        quantity = request.POST['quantity']
        quantity=int(quantity)
        price = request.POST['price']
        if Remainder.objects.filter(imei=imei, shop=sender_shop).exists():
            remainder=Remainder.objects.get(imei=imei, shop=sender_shop)
            if remainder.quantity_remainder >= quantity:
                receiver_shop=Shop.objects.get(id=receiver_shop)
                sender_shop=Shop.objects.get(id=sender_shop)
                document=Document.objects.create(
                    title='Перемещение ТМЦ',
                    user=request.user
                )
                transfer=Transfer.objects.create(
                    document=document,
                    sender_shop=sender_shop,
                    receiver_shop = receiver_shop,
                    imei=imei,
                    name=name,
                    quantity=quantity,
                    price=price
                )
                remainder.quantity_remainder -= quantity
                remainder.save()
                if Remainder.objects.filter(imei=imei, shop=receiver_shop).exists():
                    remainder=Remainder.objects.get(imei=imei, shop=receiver_shop)
                    remainder.quantity_remainder += quantity
                    remainder.save()
                    return redirect ('transfer', document.id)
                else:
                    product=Product.objects.get(imei=imei)
                    remainder=Remainder.objects.create(
                        shop=receiver_shop,
                        category=product.category,
                        name=name,
                        imei=imei,
                        quantity_remainder=quantity,
                    )
                    return redirect ('delivery', identifier.id)
            else:
                messages.error(request, 'Документ не проведен. Количество, необходимое для перемещения отсутствует на данном складе')
                return redirect ('transfer', identifier.id)
        else:
            messages.error(request, 'Документ не проведен. Количество, необходимое для перемещения отсутствует на данном складе')
            return redirect ('transfer', identifier.id)
    else:
        if Register.objects.filter(identifier=identifier).exists():
            registers=Register.objects.filter(identifier=identifier)
            context = {
            'identifier': identifier,
            'shops': shops,
            'registers': registers
            }
            return render (request, 'documents/transfer.html', context)
        else:
            context = {
            'identifier': identifier,
            'shops': shops
            }
            return render (request, 'documents/transfer.html', context)

def check_transfer (request, identifier_id):
    shops = Shop.objects.all()
    identifier=Identifier.objects.get(id=identifier_id)
    if 'imei' in request.GET:
        imei = request.GET['imei']
        shop = request.GET['shop']
        shop=Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if Remainder.objects.filter(imei=imei, shop=shop).exists():
                product=Product.objects.get(imei=imei)
                if Register.objects.filter(identifier=identifier, product=product).exists():
                    register=Register.objects.get(identifier=identifier, product=product)
                    register.quantity +=1
                    register.save()
                    return redirect ('transfer', identifier.id)
                else:
                    register=Register.objects.create(
                    product=product,
                    identifier=identifier,
                    quantity=1,
                    )
                    return redirect ('transfer', identifier.id)
            else:
                messages.error(request, 'Данное наименование отсутствует на данном складе')            
                return redirect ('transfer', identifier.id)
        else:
            messages.error(request, 'Данное наименование отсутствует в базе данных')            
            return redirect ('transfer', identifier.id)
    else:
        return redirect ('transfer', identifier.id)

def delete_line_transfer(request, imei, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    product=Product.objects.get(imei=imei)
    item=Register.objects.filter(identifier=identifier_id, product=product)
    item.delete()
    return redirect ('transfer', identifier.id)

def transfer_input(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    if request.method == "POST":
        # imeis=request.GET.getlist('imei', None )
        # names=request.GET.getlist('name', None )
        # prices=request.GET.getlist('price', None )
        # quantities=request.GET.getlist('quantity', None )
        imeis=request.POST.getlist('imei', None )
        names=request.POST.getlist('name', None )
        prices=request.POST.getlist('price', None )
        quantities=request.POST.getlist('quantity', None )
        shop_sender=request.POST['shop_sender']
        shop_receiver=request.POST['shop_receiver']
        date=request.POST['date']
        shop_sender=Shop.objects.get(id=shop_sender)
        shop_receiver=Shop.objects.get(id=shop_receiver)
        
        if shop_sender==shop_receiver:
            messages.error(request, 'Документ не проведен. Выберите фирму получателя отличную от отправителя')
            return redirect ('transfer', identifier.id)
        else:
            check_point = []
            n=len(names)
            for i in range(n):
                if Remainder.objects.filter(imei=imeis[i], shop=shop_sender).exists():
                    remainder_sender=Remainder.objects.get(imei=imeis[i], shop=shop_sender)
                    if remainder_sender.quantity_remainder<int(quantities[i]):
                        check_point.append(False)
                    else:
                        check_point.append(True)
                else:
                    check_point.append(False)
            if False in check_point:
                messages.error(request, 'Документ не проведен. Одно или несколько наименование отсутствуют на балансе данной фирмы.')
                return redirect ('transfer', identifier.id)
            else:
                document=Document.objects.create(
                        title='Перемещение ТМЦ',
                        user=request.user
                    )
                for i in range(n):
                    transfer=Transfer.objects.create(
                        document=document,
                        shop_sender=shop_sender,
                        shop_receiver=shop_receiver,
                        name=names[i],
                        imei=imeis[i],
                        price=prices[i],
                        quantity=int(quantities[i]),
                    )
                transfers=Transfer.objects.filter(document=document)
                for transfer in transfers:
                    remainder_sender=Remainder.objects.get(imei=transfer.imei, shop=transfer.shop_sender)
                    remainder_sender.quantity_remainder -= transfer.quantity
                    remainder_sender.sub_total -= transfer.quantity*remainder_sender.av_price
                    remainder_sender.save()
                    if remainder_sender.quantity_remainder == 0:
                        remainder_sender.delete()
                    else:
                        remainder_sender.av_price=remainder_sender.sub_total/remainder_sender.quantity_remainder
                        remainder_sender.save()
                    if Remainder.objects.filter(imei=transfer.imei, shop=transfer.shop_receiver).exists():
                        remainder_receiver=Remainder.objects.get(imei=transfer.imei, shop=transfer.shop_receiver)
                        remainder_receiver.quantity_remainder += transfer.quantity
                        remainder_receiver.retail_price=transfer.price
                        remainder_receiver.sub_total += transfer.quantity*remainder_sender.av_price
                        remainder_receiver.save()
                        remainder_receiver.av_price=remainder_receiver.sub_total/remainder_receiver.quantity_remainder
                        remainder_receiver.save()
                    else:
                        remainder_new = Remainder.objects.create(
                            category=remainder_sender.category,
                            shop=transfer.shop_receiver,
                            name=transfer.name,
                            imei=transfer.imei,
                            quantity_remainder=transfer.quantity,
                            retail_price=transfer.price,
                            av_price=remainder_sender.av_price,
                            sub_total=transfer.quantity*remainder_sender.av_price
                        )
                for register in registers:
                    register.delete()
                identifier.delete()      
                return redirect ('index')      
    return redirect('transfer', identifier.id)    

def cashback (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        phone=request.POST['phone']
        if Client.objects.filter(phone=phone).exists():
            client=Client.objects.get(phone=phone)
            return redirect ('payment', identifier.id, client.id)
        else:
            messages.error(request, 'Клиент не зарегистрирован в системе. Введите данные клиента.')
            return redirect ('sale', identifier.id)
    else:
        return redirect ('sale', identifier_id)

def payment (request, identifier_id, client_id):
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        registers=Register.objects.filter(identifier=identifier)
        sum=0
        for register in registers:
            sum+=register.sub_total
        client=Client.objects.get(id=client_id)
        if client.accum_cashback <= sum/100*20:
            max_cashback_off=client.accum_cashback
            max_cashback_off=int(max_cashback_off)
        else:
            max_cashback_off=sum/100*20
            max_cashback_off=int(max_cashback_off)
        if request.method=="POST":
            if registers:
                check_point = []
                cash_in=0
                for register in registers:
                    remainder = Remainder.objects.get(imei=register.product.imei, shop=register.shop)
                    if remainder.quantity_remainder < register.quantity:
                        check_point.append(False)
                    else:
                        check_point.append(True)
                    if False in check_point:
                        messages.error(request, 'Количество, необходимое для продажи отсутствует на данном складе')
                        return redirect ('sale', identifier.id)
                    else:
                        remainder.quantity_remainder -= register.quantity
                        remainder.sub_total -= register.quantity*remainder.av_price
                        remainder.save()
                        if remainder.quantity_remainder == 0:
                            remainder.delete()
                        else:
                            remainder.av_price= remainder.sub_total/remainder.quantity_remainder
                            remainder.save()

                        document=Document.objects.create(
                            title= 'Продажа ТМЦ',
                            user= request.user
                        )

                        sale=Sale.objects.create(
                            document=document,
                            imei=register.product.imei,
                            name=register.product.name,
                            category=register.product.category,
                            quantity=register.quantity,
                            price=register.price,
                            sub_total=register.sub_total,
                            shop=register.shop,
                            user=request.user,
                            staff_bonus=register.sub_total*register.product.category.bonus_percent

                        )
                        cash_in+=register.sub_total#total sum of the sale document
                        client.accum_cashback+=register.sub_total*register.product.category.cashback_percent/100
                        client.save()
                        register.delete()
                        
                identifier.delete()
                sales=Sale.objects.filter(document=document)
                current_cash_remainder=CashRemainder.objects.get(shop=sales[0].shop.id)
                current_cash_remainder.remainder+=cash_in#adding total sum of the sale document to cash remainder
                current_cash_remainder.save()
                cash=Cash.objects.create(
                    document=document,
                    shop=sales[0].shop,
                    cash_in=cash_in,
                    user=request.user,
                    cash_remainder=current_cash_remainder
                    )   
                return redirect ('index')
            else:
                messages.error(request, 'Отсутствуют товары для продажи')
                return redirect ('sale', identifier.id)
        else:
            context={
                'identifier': identifier,
                'registers': registers,
                'client': client,
                'sum': sum,
                'max_cashback_off': max_cashback_off
            }
            return render (request, 'payment/payment.html', context)
    else:
        return redirect ('login')

def cashback_off (request, identifier_id, client_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    sum=0
    for register in registers:
        sum+=register.sub_total
    client=Client.objects.get(id=client_id)
    if request.method=="POST":
        cashback_off=request.POST['cashback_off']
        cashback_off=int(cashback_off)
        if registers:
            check_point = []
            cash_in=0
            for register in registers:
                cash_in+=register.sub_total#total sum of the sale document
                remainder = Remainder.objects.get(imei=register.product.imei, shop=register.shop)
                if remainder.quantity_remainder < register.quantity:
                    check_point.append(False)
                else:
                    check_point.append(True)
                if False in check_point:
                    messages.error(request, 'Количество, необходимое для продажи отсутствует на данном складе')
                    return redirect ('sale', identifier.id)
                else:
                    if cashback_off > cash_in/100*20:
                        messages.error(request, 'Сумма кэшбэка не может составлять более 20% от суммы покупки')
                        return redirect ('payment', identifier.id, client.id)
                    elif cashback_off > client.accum_cashback:
                        messages.error(request, 'Введенная сумма превышает кэшбэк клиента.')
                        return redirect ('payment', identifier.id, client.id)
                    else:
                        client.accum_cashback = client.accum_cashback-cashback_off 
                        client.save()
                        remainder.quantity_remainder -= register.quantity
                        remainder.sub_total -= register.quantity*remainder.av_price
                        remainder.save()
                        if remainder.quantity_remainder == 0:
                            remainder.delete()
                        else:
                            remainder.av_price= remainder.sub_total/remainder.quantity_remainder
                            remainder.save()
                        document=Document.objects.create(
                                title= 'Продажа ТМЦ',
                                user= request.user
                            )
                        sale=Sale.objects.create(
                            document=document,
                            imei=register.product.imei,
                            name=register.product.name,
                            category=register.product.category,
                            quantity=register.quantity,
                            price=register.price,
                            sub_total=register.sub_total,
                            shop=register.shop
                        )
                        register.delete()
            identifier.delete()
            sales=Sale.objects.filter(document=document)
            current_cash_remainder=CashRemainder.objects.get(shop=sales[0].shop.id)
            #adding total sum of the sale document to cash remainder minus cashback
            current_cash_remainder.remainder+=(cash_in-cashback_off)
            current_cash_remainder.save()
            cash=Cash.objects.create(
                document=document,
                shop=sales[0].shop,
                cash_in=cash_in-cashback_off,
                user=request.user,
                cash_remainder=current_cash_remainder
                )   
            return redirect ('index')
    return redirect ('index')


def log(request):
    documents=Document.objects.all()
    context={
        'documents': documents
    }
    return render (request, 'documents/log.html', context)


def open_document(request, document_id):
    document=Document.objects.get(id=document_id)
    if document.title=="Продажа ТМЦ":
        sales=document.sale_set.all()
        sales=sales.filter(document=document)
        documents=sales
    elif document.title=="Поступление ТМЦ":
        deliveries=document.delivery_set.all()
        deliveries=deliveries.filter(document=document)
        documents=deliveries
    else:
        transfers=document.transfer_set.all()
        transfer=transfers.filter(document=document)
        documents=transfers
    context={
        'document': document,
        'documents':documents
    }
    return render(request, 'documents/open_document.html', context)