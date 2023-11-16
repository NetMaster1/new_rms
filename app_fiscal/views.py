from django.shortcuts import render, redirect
from app_reference.models import Shop
from django.contrib import messages, auth
from requests.auth import HTTPBasicAuth
import uuid
import requests


# Create your views here.

def get_shift_status (request):
    if request.method == "POST":
        user_name = request.POST['user_name']
        user_password = request.POST['user_password']

        auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
        uuid_number=uuid.uuid4()

        task = {
        "uuid": str(uuid_number),
        "request": 
            {"type": "getShiftStatus"}
        }




    else:
        auth.logout(request)
        return redirect ('login')


def fiscal_day_open (request):
    if request.method == "POST":
        auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
        uuid_number=uuid.uuid4()

        task = {
        "uuid": str(uuid_number),
        "request": 
        [{
            "type": "openShift",
            "operator": 
            {
                "name": "Иванов",
                "vatin": "123654789507"
            }
        }]
        }

        try:
            response=requests.post('http://127.0.0.1:16732/api/v2/requests', json=task, auth=auth)

            messages.error(request, "Смена открыта. Можете начинать работать.")
            return redirect ('sale_interface')

        except:
            messages.error(request, "Не удалось открыть смену. Сообщите администратору.")
            auth.logout(request)
            return redirect ('login')

    else:
        auth.logout(request)
        return redirect("login")


def fiscal_day_close (request):
    if request.method == "POST":
        auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
        uuid_number=uuid.uuid4()

        task = {
        "uuid": str(uuid_number),
        "request": 
        [{
            "type": "closeShift",
            "operator": 
            {
                "name": "Иванов",
                "vatin": "123654789507"
            }
        }]
        }

        try:
            response=requests.post('http://127.0.0.1:16732/api/v2/requests', json=task, auth=auth)

            messages.error(request, "Смена закрыта.")
            return redirect ('sale_interface')

        except:
            messages.error(request, "Не удалось закрыть смену. Сообщите администратору.")
            return redirect ('sale_interface')

    else:
        auth.logout(request)
        return redirect("login")
    
def sell (request):
    pass



def x_report (request):
    pass

def z_report (request):
    pass