from django.shortcuts import render, redirect, get_object_or_404
from . models import Document, Delivery, Sale, Transfer, Remainder
import datetime
from datetime import datetime, date
from app_reference.models import Shop, Supplier, Product, ProductCategory
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages


# Create your views here.

def index (request):
    return render(request, 'index.html')


def sale_document (request):
    document=Document.objects.create(
            title='Продажа ТМЦ',
            user=request.user
            )
    return redirect ('sale' , document.id)

def check_sale(request, document_id):
    shops = Shop.objects.all()
    document=Document.objects.get(id=document_id)
    if 'imei' in request.GET:
        imei = request.GET['imei']
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            context= {
                'shops': shops,
                'product': product,
                'document': document
            }
            return render (request, 'documents/sale.html', context)
        else:
            messages.error(request, 'Данное наименование отсутствует в Базе Данных')
            context= {
                'shops': shops,
                'document': document
            }
            return render (request, 'documents/sale.html', context)

    else:
       return redirect ( 'sale' , document.id) 



def sale(request, document_id):
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    document=Document.objects.get(id=document_id)
    if request.method == 'POST':
        # imeis= request.POST.getlist ('imei', None)
        shop = request.POST['shop']
        name = request.POST['name']
        imei = request.POST['imei']
        quantity_minus = request.POST['quantity_minus']
        quantity_minus=int(quantity_minus)
        price = request.POST['price']
        shop=Shop.objects.get(id=shop)
        if Remainder.objects.filter(imei=imei, shop=shop).exists():
            remainder=Remainder.objects.get(imei=imei, shop=shop)
            if remainder.quantity_remainder >= quantity_minus:
                item = Sale.objects.create(
                # date=date,
                shop=shop,
                document=document,
                name=name,
                imei=imei,
                quantity_minus=quantity_minus,
                price=price,
                )
                remainder.quantity_remainder -= item.quantity_minus
                remainder.save()
                return redirect ('sale', document.id)
            else:
                messages.error(request, 'Документ не проведен. Необходимое кол-во:  item.quantity_minus . Остаток на складе: remainder.quantity_remainder .')
                return redirect('sale', document_id)
        else:
            messages.error(request, 'Документ не проведен. Данное наименование остутствует на складе')
            return redirect('sale', document_id)
    else:
        shops = Shop.objects.all()
        document=Document.objects.get(id=document_id)
        context= {
                'shops': shops,
                'document': document
        }
        return render (request, 'documents/sale.html', context)


def delivery_document (request):
    document=Document.objects.create(
            title='Поступление ТМЦ',
            user=request.user
            )
    return redirect ('delivery' , document.id)


def check_delivery(request, document_id):
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    document=Document.objects.get(id=document_id)
    if 'imei' in request.GET:
        imei = request.GET['imei']
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            products=Delivery.objects.filter(document=document)
            context= {
                'suppliers': suppliers,
                'shops': shops,
                'categories': categories,
                'product': product,
                'document': document,
                'products': products
            }
            return render (request, 'documents/delivery.html', context)
        else:
            products=Delivery.objects.filter(document=document)
            context= {
                'suppliers': suppliers,
                'shops': shops,
                'categories': categories,
                'document': document,
                'products':products
            }
            return render (request, 'documents/delivery.html', context)

    else:
       return redirect ( 'delivery' , document.id) 


def delivery (request, document_id):
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    categories = ProductCategory.objects.all()
    document=Document.objects.get(id=document_id)
    if request.method == 'POST':
        # imeis= request.POST.getlist ('imei', None)
        date = request.POST['date']
        shop = request.POST['shop']
        supplier = request.POST['supplier']
        category = request.POST['category']
        name = request.POST['name']
        imei = request.POST['imei']
        quantity_plus = request.POST['quantity_plus']
        quantity_plus=int(quantity_plus)
        price = request.POST['price']
        shop=Shop.objects.get(id=shop)
        category=ProductCategory.objects.get(id=category)
        if Product.objects.filter(imei=imei).exists():
            item = Delivery.objects.create(
                    # date=date,
                    shop=shop,
                    category=category,
                    document=document,
                    name=name,
                    imei=imei,
                    quantity_plus=quantity_plus,
                    price=price,
                )
            if Remainder.objects.filter(imei=imei, shop=shop).exists():
                remainder=Remainder.objects.get(imei=imei, shop=shop)
                remainder.quantity_remainder += item.quantity_plus
                remainder.save()
                return redirect ('delivery', document.id)
            else:
                remainder=Remainder.objects.create(
                    shop=shop,
                    category=category,
                    name=name,
                    imei=imei,
                    quantity_remainder=quantity_plus,
                )
                return redirect ('delivery', document.id)
        else:
            Product.objects.create(
                category=category,
                name=name,
                imei=imei
            )
            item = Delivery.objects.create(
                    # date=date,
                    shop=shop,
                    category=category,
                    document=document,
                    name=name,
                    imei=imei,
                    quantity_plus=quantity_plus,
                    price=price,
                )
            if Remainder.objects.filter(imei=imei, shop=shop).exists():
                remainder=Remainder.objects.get(imei=imei, shop=shop)
                remainder.quantity_remainder =+ item.quantity_plus
                remainder.save()
                return redirect ('delivery', document.id)
            else:
                remainder=Remainder.objects.create(
                    shop=shop,
                    category=category,
                    name=name,
                    imei=imei,
                    quantity_remainder=quantity_plus,
                )
                return redirect ('delivery', document.id)
    else:
        products=Delivery.objects.filter(document=document)
        context = {
           'suppliers': suppliers,
           'shops': shops,
           'categories': categories,
           'document': document,
           'products': products
       }
        return render (request, 'documents/delivery.html', context)

def transfer_document (request):
    document=Document.objects.create(
            title='Перемещение ТМЦ',
            user=request.user
            )
    return redirect ('transfer' , document.id)

def transfer (request, document_id):
    document=Document.objects.get(id=document_id)
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
                    return redirect ('delivery', document.id)
            else:
                messages.error(request, 'Документ не проведен. Количество, необходимое для перемещения отсутствует на данном складе')
                return redirect ('transfer', document.id)
        else:
            messages.error(request, 'Документ не проведен. Количество, необходимое для перемещения отсутствует на данном складе')
            return redirect ('transfer', document.id)
    else:

        context = {
           'document': document,
           'shops': shops
        }
    return render (request, 'documents/transfer.html', context)

def check_transfer (request, document_id):
    suppliers = Supplier.objects.all()
    shops = Shop.objects.all()
    document=Document.objects.get(id=document_id)
    if 'imei' in request.GET:
        imei = request.GET['imei']
        if Product.objects.filter(imei=imei).exists():
            product=Product.objects.get(imei=imei)
            products=Delivery.objects.filter(document=document)
            context= {
                'suppliers': suppliers,
                'shops': shops,
                'product': product,
                'document': document,
                'products': products
            }
            return render (request, 'documents/transfer.html', context)
        else:
            messages.error(request, 'Данное наименование отсутствует в Базе Данных')
            products=Delivery.objects.filter(document=document)
            context= {
                'suppliers': suppliers,
                'shops': shops,
                'document': document,
                'products':products
            }
            return render (request, 'documents/transfer.html', context)

    else:
       return redirect ( 'transfer' , document.id) 