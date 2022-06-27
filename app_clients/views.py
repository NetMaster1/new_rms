from django.shortcuts import render, redirect
from . models import Customer
from app_product.models import Identifier

# Create your views here.
def new_client_sale (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method=="POST":
        f_name=request.POST['f_name']
        l_name=request.POST['l_name']
        phone=request.POST['phone']
        new_client=Customer.objects.create(
            f_name=f_name,
            l_name=l_name,
            phone=phone,
            user=request.user
        )
        return redirect('sale', identifier.id)

def new_client(request):
    pass


def calculate_discount (request):
    bar_code=request.POST['bar_code']
    if Customer.objects.filter(bar_code=bar_code).exists():
        client=Customer.objects.get(bar_code=bar_code)

    else:
        pass