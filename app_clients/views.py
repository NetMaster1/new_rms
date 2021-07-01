from django.shortcuts import render, redirect
from . models import Client
from app_product.models import Identifier

# Create your views here.
def new_client_sale (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method=="POST":
        f_name=request.POST['f_name']
        l_name=request.POST['f_name']
        phone=request.POST['phone']
        new_client=Client.objects.create(
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
    if Client.objects.filter(bar_code=bar_code).exists():
        client=Client.objects.get(bar_code=bar_code)

    else:
        pass