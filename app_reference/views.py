from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from . models import Product, ProductCategory, SKU
from app_product.models import RemainderHistory, AvPrice
from app_clients.models import Customer
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


# Create your views here.
def reference (request):
    return render(request, 'reference.html')

def products (request):
    categories=ProductCategory.objects.all()
    context ={
        'categories': categories
    }
    return render (request, 'reference/products.html', context )

def product_list (request):
    products=Product.objects.all()
    categories=ProductCategory.objects.all()
    if request.method == "POST":
        #category = request.POST["category"]
        imei = request.POST["imei"]
        imei=imei.replace(" ","")#getting rid of spaces.
        if imei:
            try:
                product=Product.objects.get(imei=imei)
                return redirect ('product_card', product.id )
            except:
                messages.error(request, "Наименование с данным IMEI отсутствует в базе данных")
                return redirect ('products')
        # else:
        #     if category:
           
        #         category=ProductCategory.objects.get(id=category)
        #         queryset_list=Product.objects.filter(category=category)
        #         numbers = queryset_list.count()
        #         for item, i in zip(queryset_list, range(numbers)):
        #             item.enumerator = i + 1
        #             item.save()

        #         #============paginator module=================
        #         paginator = Paginator(queryset_list, 50)
        #         page = request.GET.get('page')
        #         paged_queryset_list = paginator.get_page(page)
        #         #=============end of paginator module===============
        #         context = {
        #             'queryset_list':  paged_queryset_list,
        #             'categories': categories,
        #             'products': products, 
        #         }
        #         return render (request, 'reference/products.html', context )
    context={
        "products": products,
        'categories': categories
    }
    return render (request, 'reference/products.html', context )

def update_product (request, id):
    if request.method == "POST":
        product=Product.objects.get(id=id)
        #name = request.POST["name"]
        #new_imei = request.POST["imei"]
        #category = request.POST["category"]
        ean = request.POST["ean"]
        if SKU.objects.filter(ean=ean).exists():
            sku=SKU.objects.get(ean=ean)
            #category=ProductCategory.objects.get(id=category)
            imei=product.imei
            product.name=sku.name
            #product.category=sku.category
            #product.imei=new_imei
            product.ean=ean
            product.save()
            if RemainderHistory.objects.filter(imei=imei).exists():
                remainders=RemainderHistory.objects.filter(imei=imei)
                for item in remainders:
                    #item.category=category
                    item.name=sku.name
                    item.ean=ean
                    item.save()
                    
            if AvPrice.objects.filter(imei=imei).exists():
                item=AvPrice.objects.get(imei=imei)
                item.name=sku.name
                item.save()
        else:
            messages.error(request, "Данный SKU/EAN отсутствует в БД")
            return redirect ('product_card', product.id)

    return redirect ('products')

def product_card (request, id):
    categories=ProductCategory.objects.all()
    product=Product.objects.get(id=id)
    if request.method == "POST":
        name = request.POST["name"]
        imei = request.POST["imei"]
        category = request.POST["category"]
        category=ProductCategory.objects.get(id=category)
        product.name=name
        product.category=category
        product.imei=imei
        product.save()
        return redirect ('products')

    context = {
        'categories': categories,
        'product': product
    }
    return render(request, 'reference/product_card.html', context)

def clients (request):
    clients=Customer.objects.all()
    context = {
        'clients': clients
    }
    return render (request, 'reference/clients.html', context)
#===================================================================================
def eans (request):
    # categories=ProductCategory.objects.all()
    # context ={
    #     'categories': categories
    # }
    #return render (request, 'reference/eans.html', context )
    return render (request, 'reference/eans.html')

def ean_search(request):
    #skus=SKU.objects.all()
    categories=ProductCategory.objects.all()
    if request.method == "POST":
        #category = request.POST["category"]
        ean = request.POST["EAN"]
        ean=ean.replace(" ","")#getting rid of spaces.
        if ean:
            try:
                sku=SKU.objects.get(ean=ean)
                return redirect ('ean_card', sku.id )
            except:
                messages.error(request, "SKU с данным EAN отсутствуеут в БД")
                return redirect ('eans')
        else:
            pass
            # if category:
            #     category=ProductCategory.objects.get(id=category)
            #     queryset_list=Product.objects.filter(category=category)
            #     numbers = queryset_list.count()
            #     for item, i in zip(queryset_list, range(numbers)):
            #         item.enumerator = i + 1
            #         item.save()

            #     #============paginator module=================
            #     paginator = Paginator(queryset_list, 50)
            #     page = request.GET.get('page')
            #     paged_queryset_list = paginator.get_page(page)
            #     #=============end of paginator module===============
            #     context = {
            #         'queryset_list':  paged_queryset_list,
            #         'categories': categories,
            #         'products': products, 
            #     }
            #     return render (request, 'reference/products.html', context )

def ean_card(request, sku_id):
    categories=ProductCategory.objects.all()
    sku=SKU.objects.get(id=sku_id)
    context = {
        'categories': categories,
        'sku': sku
    }
    return render(request, 'reference/ean_card.html', context)

def update_sku (request, sku_id):
    if request.method == "POST":
        sku=SKU.objects.get(id=sku_id)
        name = request.POST["name"]
        ean = request.POST["ean"]
        category = request.POST["category"]
        category=ProductCategory.objects.get(id=category)
        sku.name=name
        sku.category=category
        sku.save()
        #there is a lot of products with the same ean but differen imeis
        if Product.objects.filter(ean=ean).exists():
            products=Product.objects.filter(ean=ean)
            for product in products:
                #changing name in av_price model
                if product.name != name:
                    if AvPrice.objects.filter(imei=product.imei).exists():
                        item=AvPrice.objects.get(imei=product.imei)
                        item.name=name
                        item.save()
                product.category=category
                product.name=name
                product.save()
        if RemainderHistory.objects.filter(ean=ean).exists():
            remainders=RemainderHistory.objects.filter(ean=ean)
            for item in remainders:
                item.category=category
                item.name=name
                item.save()
    return redirect ('eans')

def delete_sku (request, sku_id):
    pass
    return redirect ('log')