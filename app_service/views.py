from django.shortcuts import render, redirect
from app_product.models import Product, RemainderHistory, RemainderCurrent
from app_reference.models import Shop, ProductCategory
from django.contrib import messages

# Create your views here.
def current_qnt_correct(request):
    if request.user.is_authenticated:
        #category=ProductCategory.objects.get(name="Сим_карты")
        category=ProductCategory.objects.get(name="Смартфоны")
        products=Product.objects.filter(category=category)
        #if request.method == "POST":
        #shop = request.POST["shop"]
        shops=Shop.objects.filter(retail=True, subdealer=False, active=True)
        for shop in shops:
            for product in products:
                if RemainderHistory.objects.filter(imei=product.imei, shop=shop).exists():
                    rho_latest = RemainderHistory.objects.filter(imei=product.imei, shop=shop).latest('created')
                    if rho_latest.current_remainder != 0:
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
        messages.success(request, 'RemainderCurrent table changed')   
        return redirect("log")
    
def delete_current_qnty_table(request):
    if request.user.is_authenticated:
        items=RemainderCurrent.objects.all()
        for item in items:
            item.delete()

        messages.success(request, 'Entries to RemainderCurrent Table successfully deleted')   
        return redirect("log")