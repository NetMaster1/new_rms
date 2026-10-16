from django.shortcuts import render, redirect
from app_product.models import Product, RemainderHistory, RemainderCurrent
from app_reference.models import Shop, ProductCategory
from django.contrib import messages

# Create your views here.
def synchronize_rho_latest_with_rco(request):
    if request.user.is_authenticated:
        if request.method=="POST":
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
            products=Product.objects.filter(category=category)
            n=0
            for product in products:
                if RemainderHistory.objects.filter(imei=product.imei, shop=shop).exists():
                    rho_latest = RemainderHistory.objects.filter(imei=product.imei, shop=shop).latest('created')
                    if rho_latest.current_remainder != 0:
                        n+=1
                        if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                            rco=RemainderCurrent.objects.get(imei=product.imei, shop=shop)
                            rco.current_remainder=rho_latest.current_remainder
                            rco.category=category
                            if shop.retail==True:
                                rco.retail_price=rho_latest.retail_price
                            else:
                                rco.wholesale_price=rho_latest.wholesale_price
                            rco.save()
                        else:
                            rco=RemainderCurrent.objects.create(
                                shop=shop,
                                category=category,
                                imei=product.imei,
                                name=product.name,
                                current_remainder=rho_latest.current_remainder,
                                category=product.category
                            )
                            if shop.retail==True:
                                rco.retail_price=rho_latest.retail_price
                            else:
                                rco.wholesale_price=rho_latest.wholesale_price
                            rco.save()
                        print(f'{n} {rco.name} {rco.imei} {rco.current_remainder}')
                    else:
                        if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                            rcos=RemainderCurrent.objects.filter(imei=product.imei, shop=shop)
                            for rco in rcos:
                                rco.delete()
                else:
                    if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                        rcos=RemainderCurrent.objects.filter(imei=product.imei, shop=shop)
                        for rco in rcos:
                            rco.delete()
                                
            messages.success(request, 'RemainderCurrent table changed')   
            return redirect("log")
        else:
            shops=Shop.objects.filter(subdealer=False, active=True)
            categories=ProductCategory.objects.all()

            context = {
                "shops": shops, 
                "categories": categories
                }
            return render(request, "service/rho_rco_sync_page.html", context)

def delete_zero_rco (request):
    if request.user.is_authenticated:
        if request.method=="POST":
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
            rcos=RemainderCurrent.objects.filter(shop=shop, category=category)
            for rco in rcos:
                if rco.current_remainder == 0:
                    rco.delete()
                                      
            messages.success(request, 'Zero rcos deleted')   
            return redirect("log")
        else:
            shops=Shop.objects.filter(subdealer=False, active=True)
            categories=ProductCategory.objects.all()

            context = {
                "shops": shops, 
                "categories": categories
                }
            return render(request, "service/delete_zero_rco_page.html", context)
    
def excel_list_rco(request):
    if request.user.is_authenticated:
        #category=ProductCategory.objects.get(name="Сим_карты")
        category=ProductCategory.objects.get(name="Смартфоны")
        products=Product.objects.filter(category=category)
        #if request.method == "POST":
        #shop = request.POST["shop"]

        if request.method=="POST":
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
            products=Product.objects.filter(category=category)
            n=0
            for product in products:
                if RemainderHistory.objects.filter(imei=product.imei, shop=shop).exists():
                    rho_latest = RemainderHistory.objects.filter(imei=product.imei, shop=shop).latest('created')
                    if rho_latest.current_remainder != 0:
                        n+=1
                        if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                            rco=RemainderCurrent.objects.get(imei=product.imei, shop=shop)
                            rco.current_remainder=rho_latest.current_remainder
                            rco.retail_price=rho_latest.retail_price
                            rco.save()
                        else:
                            rco=RemainderCurrent.objects.create(
                                shop=shop,
                                imei=product.imei,
                                name=product.name,
                                current_remainder=rho_latest.current_remainder,
                                retail_price=rho_latest.retail_price,
                                category=product.category
                            )
                        print(f'{n} {rco.name} {rco.imei} {rco.current_remainder}')
                    else:
                        if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                            rcos=RemainderObjects.filter(imei=product.imei, shop=shop)
                            for rco in rcos:
                                rco.delete()
                                
            messages.success(request, 'RemainderCurrent table changed')   
            return redirect("log")
        else:
            shops=Shop.objects.filter(subdealer=False, active=True)
            categories=ProductCategory.objects.all()

            context = {
                "shops": shops, 
                "categories": categories
                }
            return render(request, "service/rho_rco_sync_page.html", context)