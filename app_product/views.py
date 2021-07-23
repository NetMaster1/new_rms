from django.db.models.fields import NullBooleanField
from app_product.admin import RemainderHistoryAdmin
from app_clients.models import Client
from app_personnel.models import BonusAccount
from django.shortcuts import render, redirect, get_object_or_404
from . models import Document, Delivery, Sale, Transfer, RemainderHistory, Register, Identifier, RemainderCurrent
import datetime
import pytz
from datetime import datetime, date
from app_reference.models import Shop, Supplier, Product, ProductCategory, DocumentType
from app_cash.models import Cash, CashRemainder, Credit, Card
from app_clients.models import Client
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.utils import timezone
from django.contrib import messages


# Create your views here.


def index (request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    else:
        # auth.logout(request)
        return redirect ('login')

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

def close_edited_document(request):
    return redirect ('log')

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

def clear_recognition(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    registers=Register.objects.filter(identifier=identifier)
    for register in registers:
        register.delete()
    return redirect ('recognition', identifier.id)

def identifier_sale (request):
    if request.user.is_authenticated:
        identifier=Identifier.objects.create()
        return redirect ('sale', identifier.id)
    else:
        return redirect ('login')

def check_sale(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    shops=Shop.objects.all()
    # if imei in request.GET:
    #     imei=request.GET['imei']
    #     if imei:
    if request.method == 'POST':
        try:
            shop=request.POST['shop']
        except:
            messages.error(request, 'Введите ТТ, откуда осуществляется продажа')            
            return redirect ('sale', identifier.id)
        imei=request.POST['imei']
        quantity=request.POST['quantity']
        quantity=int(quantity)
        shop=Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
                remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
                if remainder_current.current_remainder < quantity:
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
                            price=remainder_current.retail_price,
                            sub_total=quantity*remainder_current.retail_price
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
        register=Register.objects.last()
        context={
            'identifier': identifier,
            'registers': registers,
            'shops': shops,
            'sum': sum,
            'register': register
        }
        # if request.session.expires():
        #     identifier.delete()
        #     for register in registers:
        #         register.delete()
        #     return redirect ('login')
        # else:
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
    # shops = Shop.objects.all()
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
            return redirect ('delivery', identifier.id)
            
            # context= {
            #     'suppliers': suppliers,
            #     # 'shops': shops,
            #     'categories': categories,
            #     'identifier': identifier,
            #     'registers': registers
            # }
            # return render (request, 'documents/delivery.html', context)

def delivery(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    # categories=ProductCategory.objects.all()
    suppliers=Supplier.objects.all()
    shops=Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    context={
        'identifier': identifier,
        # 'categories': categories,
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

def delete_line_change_delivery (request, document_id, imei, shop_id):
    document=Document.objects.get(id=document_id)
    delivery=Delivery.objects.get(document=document, imei=imei)
    rho=RemainderHistory.objects.get(document=document, imei=imei)
    shop=Shop.objects.get(id=shop_id)
    remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imei)

    if RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=rho.created).exists():
        rho_sequence_before=RemainderHistory.objects.filter(imei=imei, shop=shop, created__lt=rho.created)
        rho_before=rho_sequence_before.latest('created')
        remainder_current.current_remainder=rho_before.current_remainder
        remainder_current.total_av_price=rho_before.sub_total
        remainder_current.av_price=rho_before.av_price
        remainder_current.save()
    else:
        remainder_current.current_remainder=0
        remainder_current.total_av_price=0
        remainder_current.av_price=0
        remainder_current.save()

    if RemainderHistory.objects.filter(imei=imei, shop=shop, created__gt=rho.created).exists():
        sequence_rhos_after=RemainderHistory.objects.filter(imei=imei, shop=shop, created__gt=rho.created)
        # remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
        # remainder_current.current_remainder=rho.current_remainder
        # remainder_current.total_av_price=rho.sub_total
        # remainder_current.av_price=rho.av_price
        # remainder_current.save()
        for obj in sequence_rhos_after:
            obj.pre_remainder=remainder_current.current_remainder
            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
            obj.av_price=obj.sub_total/obj.current_remainder
            obj.save()
            remainder_current.current_remainder=obj.current_remainder
            remainder_current.total_av_price=obj.sub_total
            remainder_current.av_price=obj.av_price
            remainder_current.save()

        delivery.delete()
        rho.delete()
        if Delivery.objects.filter(document=document).exists():
            document.sum-=delivery.sub_total
            document.save()
            return redirect ('change_delivery', document.id)
        else:
            document.delete()
            return redirect ('log')
    else:
        delivery.delete()
        rho.delete()
        if Delivery.objects.filter(document=document).exists():
            document.sum-=delivery.sub_total
            document.save()
            return redirect ('change_delivery', document.id)
        else:
            document.delete()
            return redirect ('log')

    
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
    doc_type=DocumentType.objects.get(name="Поступление ТМЦ")
    if request.method == 'POST':
        shop=request.POST['shop']
        dateTime=request.POST['dateTime']
        # category=request.POST['category']
        imeis=request.POST.getlist('imei', None )
        names=request.POST.getlist('name', None )
        quantities=request.POST.getlist('quantity', None)
        prices=request.POST.getlist('price', None)
        try:
            supplier=request.POST['supplier']
        except:
            messages.error(request, 'Введите поставщика')            
            return redirect ('delivery', identifier.id)
        shop=Shop.objects.get(id=shop)
        # category=ProductCategory.objects.get(id=category)
        supplier=Supplier.objects.get(id=supplier)
        
        if imeis:
            if dateTime:
                document=Document.objects.create(
                    title= doc_type,
                    user= request.user,
                    created=dateTime
                )
            else:
                document=Document.objects.create(
                    title= doc_type,
                    user= request.user,
                )
            n=len(names)
            document_sum=0
            for i in range(n):
                # imei=imeis[i]
                if RemainderCurrent.objects.filter(shop=shop, imei=imeis[i]).exists():
                    remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                else:
                    RemainderCurrent.objects.create(
                        shop=shop,
                        imei=imeis[i],
                        current_remainder=0,
                        av_price=0,
                        total_av_price = 0,
                        name=names[i]
                    )
                    remainder_current=RemainderCurrent.objects.get(shop=shop, imei=imeis[i])
                delivery_item=Delivery.objects.create(
                    document=document,
                    # category=category,
                    created=document.created,
                    supplier=supplier,
                    shop=shop,
                    name=names[i],
                    imei=imeis[i],
                    price=prices[i],
                    quantity=quantities[i],
                    sub_total=int(quantities[i]) * int(prices[i])
                )
                document_sum+=delivery_item.sub_total
                remainder_history=RemainderHistory.objects.create(
                    document=document,
                    created=document.created,
                    shop=shop,
                    # category=category,
                    imei=imeis[i],
                    name=names[i],
                    pre_remainder=remainder_current.current_remainder,
                    incoming_quantity=quantities[i],
                    outgoing_quantity=0,
                    current_remainder=remainder_current.current_remainder+int(quantities[i]),
                    wholesale_price=int(prices[i]),
                    sub_total=int(int(quantities[i]) * int(prices[i]) + remainder_current.total_av_price),

                    av_price = (int(quantities[i]) * int(prices[i])+ remainder_current.total_av_price)/(remainder_current.current_remainder+int(quantities[i]))
                )
                remainder_current.current_remainder=remainder_history.current_remainder
                remainder_current.av_price=remainder_history.av_price
                remainder_current.total_av_price=remainder_history.sub_total
                remainder_current.save()
                document.sum=document_sum
                document.save()

                if document.created != datetime.now() and RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=document.created).exists():
                  
                    sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop)
                    if sequence_rhos.filter(created__lt=document.created).exists():
                        sequence_rhos_before=sequence_rhos.filter(created__lt=document.created)
                        rho_before=sequence_rhos_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price = rho_before.sub_total
                        print(remainder_current.total_av_price)
                        # remainder_current.av_price = rho_before.av_price
                        remainder_current.save()
                        remainder_history.pre_remainder = remainder_current.current_remainder
                        remainder_history.current_remainder = remainder_current.current_remainder + int(quantities[i])

                        remainder_history.sub_total = int(quantities[i]) * int(prices[i])+ remainder_current.total_av_price

                        remainder_history.av_price= int(remainder_history.sub_total/remainder_history.current_remainder)

                        remainder_history.save()

                        remainder_current.current_remainder=remainder_history.current_remainder
                        remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.av_price=remainder_history.av_price
                        remainder_current.save()

                    else:
                        remainder_current.current_remainder =0
                        remainder_current.total_av_price =0
                        # remainder_current.av_price =0
                        remainder_current.save()
                        remainder_history.pre_remainder = remainder_current.current_remainder
                        remainder_history.current_remainder=remainder_current.current_remainder+ int(quantities[i])
                        remainder_history.sub_total = int(quantities[i]) * int(prices[i]) + remainder_current.total_av_price

                        remainder_history.av_price= int(remainder_history.sub_total/remainder_history.current_remainder)

                        remainder_history.save()

                        remainder_current.current_remainder=remainder_history.current_remainder
                        remainder_current.total_av_price=remainder_history.sub_total
                        remainder_current.av_price=remainder_history.av_price
                        remainder_current.save()
                    sequence_rhos_after=sequence_rhos.filter(created__gt=document.created)
                    sequence_rhos_after=sequence_rhos_after.all().order_by('created')
                    for obj in sequence_rhos_after:
                        obj.pre_remainder=remainder_current.current_remainder
                        obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                        obj.sub_total=remainder_current.total_av_price + obj.incoming_quantity * obj.wholesale_price
                        obj.av_price=obj.sub_total/obj.current_remainder
                        obj.save()

                        remainder_current.current_remainder=obj.current_remainder
                        remainder_current.total_av_price=obj.sub_total
                        remainder_current.av_price=obj.av_price
                        
                        remainder_current.save()
            else:
                for register in registers:
                    register.delete()
                identifier.delete()
                return redirect ('log')
        else:
            messages.error(request, 'Вы не ввели ни одного наименования.')
            return redirect('delivery', identifier.id)

def change_delivery(request, document_id):
    document=Document.objects.get(id=document_id)
    deliveries=Delivery.objects.filter(document=document)
    suppliers=Supplier.objects.all()
    shops=Shop.objects.all()
    categories=ProductCategory.objects.all()
    rem_hist_objs=RemainderHistory.objects.filter(document=document)
    rem_hist_obj=rem_hist_objs[0]
    shop_current=rem_hist_obj.shop
    if request.method=="POST":
        shop=request.POST['shop']
        try:
            supplier=request.POST['supplier']
        except:
            messages.error(request, 'Введите поставщика')            
            return redirect ('change_delivery', document.id)
        supplier=Supplier.objects.get(id=supplier)
        dateTime=request.POST['dateTime']
        imeis=request.POST.getlist('imei', None )
        names=request.POST.getlist('name', None )
        quantities=request.POST.getlist('quantity', None)
        prices=request.POST.getlist('price', None)
        shop_changed=Shop.objects.get(id=shop)
        sum=0
        n=len(names)
        # for i in range(n)
        #date has been changed
        if dateTime:
            #converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime=datetime.strptime(dateTime, '%Y-%m-%dT%H:%M')
            for delivery, i , rho in zip (deliveries, range(n), rem_hist_objs):
                delivery.created=dateTime
                delivery.shop=shop_changed
                delivery.supplier=supplier
                delivery.quantity=quantities[i]
                delivery.price=prices[i]
                delivery.sub_total=int(quantities[i])*int(prices[i])
                delivery.save()
                sum+=delivery.sub_total
                shop_current=rho.shop
                # date has been chaned & shop has not been changed
                if shop_current==shop_changed:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created)
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()

                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()

                    rho.delete()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=dateTime).exists():
                        rho_hist_objs_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=dateTime)
                        rho_hist_before=rho_hist_objs_before.latest('created')
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        # remainder_current=RemainderCurrent(imei=imeis[i], shop=shop_current)#creates a new object which we don't need
                        remainder_current.current_remainder=rho_hist_before.current_remainder
                        remainder_current.total_av_price=rho_hist_before.sub_total
                        remainder_current.av_price=rho_hist_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()

                    rho_new=RemainderHistory.objects.create( 
                        shop=shop_current,
                        created=dateTime,
                        document=document,
                        name=names[i],
                        imei=imeis[i],
                        incoming_quantity=int(quantities[i]),
                        outgoing_quantity=0,
                        pre_remainder=remainder_current.current_remainder,
                        current_remainder=remainder_current.current_remainder+int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=remainder_current.total_av_price+(int(quantities[i])*int(prices[i])),
                        av_price= (remainder_current.total_av_price+(int(quantities[i])*int(prices[i])))/(remainder_current.current_remainder+int(quantities[i]))
                    )

                    remainder_current.current_remainder=rho_new.current_remainder
                    remainder_current.total_av_price=rho_new.sub_total
                    remainder_current.av_price=rho_new.av_price
                    remainder_current.save()

                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho_new.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho_new.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                #shop & date have been changed
                else:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created) 
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    rho.delete()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__lt=dateTime).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_changed)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__lt=dateTime) 
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop_changed).exists():
                            remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_changed)
                            remainder_current.av_price=0
                            remainder_current.total_av_price=0
                            remainder_current.current_remainder=0
                        else:
                            remainder_current=RemainderCurrent.objects.create(
                                imei=imeis[i],
                                shop=shop_changed,
                                current_remainder=0,
                                total_av_price=0,
                                av_price=0 
                            )
                    rho_new=RemainderHistory.objects.create(
                        created=dateTime,
                        document=document,
                        shop=shop_changed,
                        pre_remainder=remainder_current.current_remainder,
                        name=names[i],
                        imei=imeis[i],
                        incoming_quantity=int(quantities[i]),
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder+int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=remainder_current.total_av_price+(int(quantities[i])*int(prices[i])),
                        av_price= (remainder_current.total_av_price+(int(quantities[i])*int(prices[i])))/(remainder_current.current_remainder+int(quantities[i]))
                    )
                    remainder_current.current_remainder=rho_new.current_remainder
                    remainder_current.av_price=rho_new.av_price
                    remainder_current.total_av_price=rho_new.sub_total
                    remainder_current.save()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__gt=rho_new.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__gt=rho_new.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
            document.created=dateTime
            document.save()


        # date has not been changed
        else:
            for delivery, i , rho in zip (deliveries, range(n), rem_hist_objs):
                # delivery.created=dateTime
                delivery.shop=shop_changed
                delivery.supplier=supplier
                delivery.quantity=quantities[i]
                delivery.price=prices[i]
                delivery.sub_total=int(quantities[i])*int(prices[i])
                delivery.save()
                sum+=delivery.sub_total
                shop_current=rho.shop
                #date & shop has not been changed
                if shop_current==shop_changed:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created)
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current )
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    rho.incoming_quantity=int(quantities[i])
                    rho.wholesale_price=int(prices[i])
                    rho.sub_total=remainder_current.total_av_price+(int(quantities[i]) * int(prices[i]))
                    rho.current_remainder=rho.pre_remainder+int(quantities[i])
                    rho.av_price=rho.sub_total/rho.current_remainder
                    rho.save()

                    remainder_current.current_remainder=rho.current_remainder
                    remainder_current.av_price=rho.av_price
                    remainder_current.total_av_price=rho.sub_total
                    remainder_current.save()
                    
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created)
                        # remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        # remainder_current.current_remainder=rho.current_remainder
                        # remainder_current.total_av_price=rho.sub_total
                        # remainder_current.av_price=rho.av_price
                        # remainder_current.save()
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            if obj.current_remainder > 0:
                                obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                                obj.av_price=obj.sub_total/obj.current_remainder  
                            else:
                                obj.av_price=0
                                obj.sub_total=0
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current
                            remainder_current.save()
                #date has not been changed & shop has been changed
                else:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__lt=rho.created) 
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_current, created__gt=rho.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    dateTime=rho.created
                    rho.delete()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__lt=dateTime).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_changed)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__lt=dateTime) 
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop_changed).exists():
                            remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_changed)
                            remainder_current.av_price=0
                            remainder_current.total_av_price=0
                            remainder_current.current_remainder=0
                        else:
                            remainder_current=RemainderCurrent.objects.create(
                                imei=imeis[i],
                                shop=shop_changed,
                                current_remainder=0,
                                total_av_price=0,
                                av_price=0 
                            )
                    rho_new=RemainderHistory.objects.create(
                        created=dateTime,
                        document=document,
                        shop=shop_changed,
                        name=names[i],
                        imei=imeis[i],
                        incoming_quantity=int(quantities[i]),
                        outgoing_quantity=0,
                        current_remainder=remainder_current.current_remainder+int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=remainder_current.total_av_price+(int(quantities[i])*int(prices[i])),
                        av_price= (remainder_current.total_av_price+(int(quantities[i])*int(prices[i])))/(remainder_current.current_remainder+int(quantities[i]))
                    )
                    remainder_current.current_remainder=rho_new.current_remainder
                    remainder_current.av_price=rho_new.av_price
                    remainder_current.total_av_price=rho_new.sub_total
                    remainder_current.save()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__gt=rho_new.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_changed, created__gt=rho_new.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()

        
        document.sum = sum
        document.save()
        return redirect ('log')
         
    else:
        deliveries=Delivery.objects.filter(document=document)
        context={
            'deliveries': deliveries,
            'document': document,
            'shops': shops,
            'suppliers': suppliers,
            'categories': categories,
        }
        return render (request, 'documents/change_delivery.html', context)

def delete_delivery(request, document_id):
    document=Document.objects.get(id=document_id)
    deliveries=Delivery.objects.filter(document=document)
    remainder_history_objects=RemainderHistory.objects.filter(document=document)
    for rho in remainder_history_objects:
        rho_all=RemainderHistory.objects.filter(shop=rho.shop, imei=rho.imei)
        if rho_all.filter(created__lt=document.created).exists():
            rho_all_before=rho_all.filter(created__lt=document.created)
            rho_latest_before=rho_all_before.latest('created')

            remainder_current=RemainderCurrent.objects.get(shop=rho.shop, imei=rho.imei)
            remainder_current.current_remainder=rho_latest_before.current_remainder
            remainder_current.total_av_price=rho_latest_before.sub_total
            remainder_current.av_price=rho_latest_before.av_price
            remainder_current.save()
        else:
            if RemainderCurrent.objects.filter(shop=rho.shop, imei=rho.imei).exists():
                remainder_current=RemainderCurrent.objects.get(shop=rho.shop, imei=rho.imei)
                remainder_current.current_remainder=0
                remainder_current.total_av_price=0
                remainder_current.av_price=0
                remainder_current.save()
            else:
                remainder_current=RemainderCurrent.objets.create(
                    current_remainder=0,
                    av_total_price=0,
                    av_price=0,
                    imei=rho.imei,
                    shop=rho.shop
                )

        if rho_all.filter(created__gt=document.created).exists():
            rho_all_after=rho_all.filter(created__gt=document.created)
            rho_first_after=rho_all_after.earliest('created')
            rho_first_after.pre_remainder=remainder_current.current_remainder
            rho_first_after.current_remainder=rho_first_after.pre_remainder+rho_first_after.incoming_quantity-rho_first_after.outgoing_quantity

            rho_first_after.sub_total=remainder_current.total_av_price+(rho_first_after.incoming_quantity-rho_first_after.outgoing_quantity)*rho_first_after.wholesale_price
            rho_first_after.save()

            remainder_current.current_remainder=rho_first_after.current_remainder
            remainder_current.total_av_price=rho_first_after.sub_total
            remainder_current.av_price=rho_first_after.av_price
            remainder_current.save()
            
        
            remainder_after_loop=rho_all_after.filter(created__gt=rho_first_after.created)
            for obj in remainder_after_loop:
                obj.pre_remainder=remainder_current.current_remainder
                obj.current_remainder=obj.pre_remainder+obj.incoming_quantity-obj.outgoing_quantity
                obj.sub_total=remainder_current.av_total_price+(obj.incoming_quantity-obj.outgoing_quantity)*obj.wholesale_price
                obj.av_price=obj.sub_total/obj.current_remainder
                obj.save()
                remainder_current.current_remainder=obj.current_remainder
                remainder_current.total_av_price=obj.sub_total
                remainder_current.av_price=obj.av_price
                remainder_current.save()
            rho.delete()
        else:    
            rho.delete()
    
    for delivery in deliveries:
        delivery.delete()
    document.delete()
    return redirect ('log')

def identifier_transfer (request):
    identifier=Identifier.objects.create()
    return redirect ('transfer', identifier.id)

def transfer (request, identifier_id):
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        shops=Shop.objects.all()
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
    else:
        return redirect ('login')

def check_transfer (request, identifier_id):
    shops = Shop.objects.all()
    identifier=Identifier.objects.get(id=identifier_id)
    if 'imei' in request.GET:
        imei = request.GET['imei']
        shop = request.GET['shop']
        shop=Shop.objects.get(id=shop)
        if Product.objects.filter(imei=imei).exists():
            if RemainderCurrent.objects.filter(imei=imei, shop=shop).exists():
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
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        registers=Register.objects.filter(identifier=identifier)
        doc_type=DocumentType.objects.get(name='Перемещение ТМЦ')
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
            # date=request.POST['date']
            shop_sender=Shop.objects.get(id=shop_sender)
            shop_receiver=Shop.objects.get(id=shop_receiver)
            
            if shop_sender==shop_receiver:
                messages.error(request, 'Документ не проведен. Выберите фирму получателя отличную от отправителя')
                return redirect ('transfer', identifier.id)
            else:

                check_point = []
                n=len(names)
                for i in range(n):
                    if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop_sender).exists():
                        remainder_current_sender=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender)
                        if remainder_current_sender.current_remainder<int(quantities[i]):
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
                            title=doc_type,
                            user=request.user
                        )
                    for i in range(n):
                        remainder_current_sender=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender)
                        transfer=Transfer.objects.create(
                            document=document,
                            shop_sender=shop_sender,
                            shop_receiver=shop_receiver,
                            imei=imeis[i],
                            price=prices[i],
                            name=names[i],
                            quantity=int(quantities[i]),
                        )

                        remainder_history=RemainderHistory.objects.create(
                            document=document,
                            shop=shop_sender,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            av_price=remainder_current_sender.av_price,
                            retail_price=prices[i],
                            pre_remainder=remainder_current_sender.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity=quantities[i],
                            current_remainder=remainder_current_sender.current_remainder-int(quantities[i]),
                            sub_total=remainder_current_sender.av_price*(remainder_current_sender.current_remainder-int(quantities[i]))
                        )
                        remainder_current_sender.current_remainder=remainder_history.current_remainder
                        if remainder_current_sender.current_remainder==0:
                            remainder_current_sender.total_av_price=0
                            remainder_current_sender.av_price=0
                        else:
                            remainder_current_sender.total_av_price=remainder_current_sender.current_remainder*remainder_current_sender.av_price
                            remainder_current_sender.av_price=remainder_current_sender.total_av_price/remainder_current_sender.current_remainder
                        remainder_current_sender.save()

                        if RemainderCurrent.objects.filter(imei=imeis[i], shop=shop_receiver).exists():
                            remainder_current_receiver=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver)

                            remainder_history=RemainderHistory.objects.create(
                            document=document,
                            shop=shop_receiver,
                            # category=category,
                            imei=imeis[i],
                            name=names[i],
                            retail_price=prices[i],
                            pre_remainder=remainder_current_receiver.current_remainder,
                            incoming_quantity=quantities[i],
                            outgoing_quantity=0,
                            current_remainder=remainder_current_receiver.current_remainder+int(quantities[i]),
                            av_price=remainder_current_receiver.av_price,
                            sub_total=remainder_current_receiver.av_price *(remainder_current_receiver.current_remainder+int(quantities[i]))
                        )
                        else:
                            remainder_current_receiver=RemainderCurrent.objects.create(
                                imei=imeis[i],
                                name=names[i],
                                shop=shop_receiver,
                                current_remainder=0,
                                total_av_price=0,
                                av_price=0
                            )
                            remainder_history=RemainderHistory.objects.create(
                                document=document,
                                shop=shop_receiver,
                                # category=category,
                                imei=imeis[i],
                                name=names[i],
                                retail_price=prices[i],
                                pre_remainder=remainder_current_receiver.current_remainder,
                                incoming_quantity=quantities[i],
                                outgoing_quantity=0,
                                current_remainder=remainder_current_receiver.current_remainder+int(quantities[i]),
                                av_price=remainder_current_sender.av_price,
                                sub_total=remainder_current_sender.av_price *(remainder_current_receiver.current_remainder+int(quantities[i]))
                            )
                        remainder_history.save()
                        remainder_current_receiver.current_remainder=remainder_history.current_remainder
                        remainder_current_receiver.retail_price=remainder_history.retail_price
                        remainder_current_receiver.av_price=remainder_history.av_price
                        remainder_current_receiver.total_av_price=remainder_history.sub_total
                        remainder_current_receiver.save()


                    for register in registers:
                        register.delete()
                    identifier.delete()      
                    return redirect ('log')   
        else:
            return redirect('transfer', identifier.id)
    else:
        auth.logout(request)
        return redirect('login')  

def change_transfer(request, document_id):
    document=Document.objects.get(id=document_id)
    transfers=Transfer.objects.filter(document=document)
    transfer=transfers[0]
    shop_sender_current=transfer.shop_sender
    shop_receiver_current=transfer.shop_receiver
    # dateTime_current=document.created
    shops=Shop.objects.all()
    rem_hist_objs=RemainderHistory.objects.filter(document=document)
    if request.method == "POST":
        dateTime=request.POST['dateTime']
        shop_sender=request.POST['shop_sender']
        shop_sender_changed=Shop.objects.get(id=shop_sender)
        shop_receiver=request.POST['shop_receiver']
        shop_receiver_changed=Shop.objects.get(id=shop_receiver)
        imeis=request.POST.getlist('imei', None )
        names=request.POST.getlist('name', None )
        quantities=request.POST.getlist('quantity', None)
        prices=request.POST.getlist('price', None)
        sum=0
        n=len(names)
        # for i in range(n)
        #date has been changed
        if dateTime:
            #converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            dateTime=datetime.strptime(dateTime, '%Y-%m-%dT%H:%M')
        else:
            dateTime=document.created
        for transfer, i in zip (transfers, range(n)):
            transfer.created=dateTime
            transfer.shop_sender=shop_sender_changed
            transfer.shop_receiver=shop_receiver_changed
            transfer.quantity=quantities[i]
            transfer.price=prices[i]
            transfer.sub_total=int(quantities[i])*int(prices[i])
            transfer.save()
            sum+=transfer.sub_total
           
        for i in range(n):
            for rho in rem_hist_objs: 
            # date has been chaned & shops have not been changed
            # changing docs for shop_sender
                if rho.shop==shop_sender_current:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_current, created__lt=rho.created)
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()

                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_current, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_current, created__gt=rho.created)
                        
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    rho.delete()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_changed, created__lt=dateTime).exists():
                        rho_hist_objs_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_changed, created__lt=dateTime)
                        rho_hist_before=rho_hist_objs_before.latest('created')
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender_changed)
                        # remainder_current=RemainderCurrent(imei=imeis[i], shop=shop_current)#creates a new object which we don't need
                        remainder_current.current_remainder=rho_hist_before.current_remainder
                        remainder_current.total_av_price=rho_hist_before.sub_total
                        remainder_current.av_price=rho_hist_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_sender_changed)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    
                    rho_new=RemainderHistory.objects.create( 
                        shop=shop_sender_changed,
                        created=dateTime,
                        document=document,
                        name=names[i],
                        imei=imeis[i],
                        incoming_quantity=0,
                        outgoing_quantity=int(quantities[i]),
                        pre_remainder=remainder_current.current_remainder,
                        current_remainder=remainder_current.current_remainder-int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price),
                        av_price= (remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price))/(remainder_current.current_remainder+int(quantities[i]))
                    )
                    remainder_current.current_remainder=rho_new.current_remainder
                    remainder_current.total_av_price=rho_new.sub_total
                    remainder_current.av_price=rho_new.av_price
                    remainder_current.save()
                    
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_changed, created__gt=rho_new.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_sender_changed, created__gt=rho_new.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    
                if rho.shop==shop_receiver_current:
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_current, created__lt=rho.created).exists():
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver_current)
                        rho_sequence_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_current, created__lt=rho.created)
                        rho_before=rho_sequence_before.latest('created')
                        remainder_current.current_remainder=rho_before.current_remainder
                        remainder_current.total_av_price=rho_before.sub_total
                        remainder_current.av_price=rho_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver_current)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_current, created__gt=rho.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_current, created__gt=rho.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.av_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    rho.delete()
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_changed, created__lt=dateTime).exists():
                        rho_hist_objs_before=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_changed, created__lt=dateTime)
                        rho_hist_before=rho_hist_objs_before.latest('created')
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver_changed)
                        # remainder_current=RemainderCurrent(imei=imeis[i], shop=shop_current)#creates a new object which we don't need
                        remainder_current.current_remainder=rho_hist_before.current_remainder
                        remainder_current.total_av_price=rho_hist_before.sub_total
                        remainder_current.av_price=rho_hist_before.av_price
                        remainder_current.save()
                    else:
                        remainder_current=RemainderCurrent.objects.get(imei=imeis[i], shop=shop_receiver_changed)
                        remainder_current.current_remainder=0
                        remainder_current.total_av_price=0
                        remainder_current.av_price=0
                        remainder_current.save()
                    
                    rho_new=RemainderHistory.objects.create( 
                        shop=shop_receiver_changed,
                        created=dateTime,
                        document=document,
                        name=names[i],
                        imei=imeis[i],
                        incoming_quantity=int(quantities[i]),
                        outgoing_quantity=0,
                        pre_remainder=remainder_current.current_remainder,
                        current_remainder=remainder_current.current_remainder+int(quantities[i]),
                        wholesale_price=int(prices[i]),
                        sub_total=remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price),
                        av_price= (remainder_current.total_av_price+(int(quantities[i])*remainder_current.av_price))/(remainder_current.current_remainder+int(quantities[i]))
                    )
                    remainder_current.current_remainder=rho_new.current_remainder
                    remainder_current.total_av_price=rho_new.sub_total
                    remainder_current.av_price=rho_new.av_price
                    remainder_current.save()
                    
                    if RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_changed, created__gt=rho_new.created).exists():
                        sequence_rhos=RemainderHistory.objects.filter(imei=imeis[i], shop=shop_receiver_changed, created__gt=rho_new.created)
                        for obj in sequence_rhos:
                            obj.pre_remainder=remainder_current.current_remainder
                            obj.sub_total=remainder_current.total_av_price+obj.wholesale_price*(obj.incoming_quantity - obj.outgoing_quantity)
                            obj.current_remainder=remainder_current.current_remainder + obj.incoming_quantity - obj.outgoing_quantity
                            obj.av_price=obj.sub_total/obj.current_remainder
                            obj.save()
                            remainder_current.current_remainder=obj.current_remainder
                            remainder_current.total_av_price=obj.sub_total
                            remainder_current.av_price=obj.av_price
                            remainder_current.save()
                    
        return redirect ('log')
       

    else:
        context = {
            'document': document,
            'transfers': transfers,
            'shops': shops
        }
        return render (request, 'documents/change_transfer.html' , context)

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
        doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
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
                    remainder_current = RemainderCurrent.objects.get(imei=register.product.imei, shop=register.shop)
                    if remainder_current.current_remainder < register.quantity:
                        check_point.append(False)
                    else:
                        check_point.append(True)
                    if False in check_point:
                        messages.error(request, 'Количество, необходимое для продажи отсутствует на данном складе')
                        return redirect ('sale', identifier.id)
                    else:
                        document=Document.objects.create(
                            title= doc_type,
                            user= request.user
                        )
                        remainder_history=RemainderHistory.objects.create(
                            document=document,
                            shop=register.shop,
                            category=register.product.category,
                            imei=register.product.imei,
                            pre_remainder=remainder_current.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity =register.quantity,
                            current_remainder=remainder_current.current_remainder-register.quantity,
                            # av_price=prices[i],
                            # sub_total=int(quantities[i]) * int(prices[i])
                        )
                        remainder_current.current_remainder=remainder_history.current_remainder
                        remainder_current.save()

                        # remainder.sub_total -= register.quantity*remainder.av_price
                        # remainder.save()
                        # if remainder.quantity_remainder == 0:
                        #     remainder.delete()
                        # else:
                        #     remainder.av_price= remainder.sub_total/remainder.quantity_remainder
                        #     remainder.save()

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
                    current_remainder=current_cash_remainder
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
    doc_type=DocumentType.objects.get(name="Продажа ТМЦ")
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
                                title= doc_type,
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
            cash=Cash.objects.create(
                document=document,
                shop=sales[0].shop,
                pre_remainder=current_cash_remainder.remainder,
                cash_in=(cash_in-cashback_off),
                cash_out=0,
                current_remainder=current_cash_remainder.remainder+(cash_in-cashback_off),
                user=request.user,
            )
            #updating cash remainder value
            current_cash_remainder.remainder+=(cash_in-cashback_off)
            current_cash_remainder.save()
            return redirect ('index')
    return redirect ('index')

def identifier_recognition (request):
    if request.user.is_authenticated:
        identifier=Identifier.objects.create()
        return redirect ('recognition', identifier.id)
    else:
        return redirect ('login')

def recognition(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    registers = Register.objects.filter(identifier=identifier)
    context={
        'identifier': identifier,
        'categories': categories,
        'shops': shops,
        'registers': registers
    }
    return render(request, 'documents/recognition.html', context)

def log(request):
    queryset_list=Document.objects.all().order_by('-created')
    doc_types=DocumentType.objects.all()
    users=User.objects.all()
    suppliers=Supplier.objects.all()
    shops=Shop.objects.all()
    if request.method=="POST":
        # shop = request.POST['shop']
        # supplier = request.POST['supplier']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        user = request.POST['user']
        supplier = request.POST['supplier']
        doc_type = request.POST['doc_type']
        # if shop:
        #     queryset_list = queryset_list.filter(shop=shop)
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        if doc_type:
            doc_type=DocumentType.objects.get(id=doc_type)
            queryset_list = queryset_list.filter(title=doc_type)
        if user:
            queryset_list = queryset_list.filter(user=user)
        if supplier:
            doc_type=DocumentType.objects.get(name='Поступление ТМЦ')
            queryset_list=queryset_list.filter(title=doc_type)
            supplier=Supplier.objects.get(id=supplier)
            new_list=[]
            for item in queryset_list:
                if item.delivery.first().supplier == supplier:
                    new_list.append(item)
            queryset_list=new_list
            print(queryset_list)
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        context={
            'queryset_list': queryset_list,
            'doc_types': doc_types,
            'users': users,
            'suppliers': suppliers,
            'shops': shops
        }
        return render (request, 'documents/log.html', context)

    else:
        context={
            'queryset_list': queryset_list,
            'doc_types': doc_types,
            'users': users,
            'suppliers': suppliers,
            'shops': shops,
        }
        return render (request, 'documents/log.html', context)

def open_document(request, document_id):
    document=Document.objects.get(id=document_id)
    if document.title=="Продажа ТМЦ":
        sales=document.sale_set.all()
        sales=sales.filter(document=document)
        documents=sales
    elif document.title=="Поступление ТМЦ":
        deliveries=document.delivery.all()
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


 
def file_uploading(request):
    pass