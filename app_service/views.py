from django.shortcuts import render, redirect
from app_product.models import Product, RemainderHistory, RemainderCurrent
from app_reference.models import Shop
from django.contrib import messages

# Create your views here.
def current_qnt_correct(request):
    if request.user.is_authenticated:
        products=Product.objects.all()
        if request.method == "POST":
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
        for product in products:
            if RemainderHistory.objects.filter(imei=product.imei, shop=shop).exists():
                rho_latest = RemainderHistory.objects.filter(imei=product.imei, shop=shop).latest('created')
                if RemainderCurrent.objects.filter(imei=product.imei, shop=shop).exists():
                    rco=RemainderCurrent.objects.get(imei=product.imei, shop=shop)
                    rco.current_remainder=rho_latest.current_remainder
                    rco.save()
                else:
                    rco=RemainderCurrent.objects.create(
                        shop=shop,
                        imei=product.imei,
                        name=product.name,
                        current_remainder=rho_latest.current_remainder
                    )
        messages.success(request, 'RemainderCurrent table changed')   
        return redirect("log")   