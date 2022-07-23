from django.shortcuts import render, redirect
from . models import Customer
from app_product.models import Identifier, Document
from django.contrib import messages

# Create your views here.
def new_client_sale (request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method=="POST":
        f_name=request.POST['f_name']
        l_name=request.POST['l_name']
        phone=request.POST['phone']
        if Customer.objects.filter(phone=phone).exists():
            messages.error(request, "Клиент с таким номером телефона уже существует")
            return redirect("sale", identifier.id)
        new_client=Customer.objects.create(
            f_name=f_name,
            l_name=l_name,
            phone=phone,
            user=request.user
        )
        return redirect('sale', identifier.id)

def client_history (request):
    if request.method == 'POST':
        phone=request.POST['phone']
        if Customer.objects.filter(phone=phone).exists():
            client=Customer.objects.get(phone=phone)
        else:
            messages.error(request, "Клиента с таким номером телефона не существует")
            return redirect("client_history")
        if Document.objects.filter(client=client).exists():
            documents=Document.objects.filter(client=client)
        else:
            messages.error(request, "Информация о покупках данного клиента в указанный период отсутствуе")
            return redirect("client_history")

        context = {
            'client': client,
            'documents': documents
        }
        return render (request, 'clients/client_history.html', context )


    else:
        return render (request, 'clients/client_history.html' )

def new_client(request):
    pass


def calculate_discount (request):
    bar_code=request.POST['bar_code']
    if Customer.objects.filter(bar_code=bar_code).exists():
        client=Customer.objects.get(bar_code=bar_code)

    else:
        pass