from django.shortcuts import render, redirect
from app_reference.models import Shop
from django.contrib import messages, auth
from requests.auth import HTTPBasicAuth
from django.contrib.auth.models import User, Group
import uuid
import requests


# Create your views here.

def fiscal_day_open (request):
    if request.user.is_authenticated:
        auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
        uuid_number=uuid.uuid4()

        task = {
        "uuid": str(uuid_number),
        "request": 
        [{
            "type": "openShift",
            "operator": 
            {
                "name": request.user.last_name,
                "vatin": "5257173237"
            }
        }]
        }

        try:
            response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)

            messages.error(request, "Смена открыта. Можете начинать работать.")
            return redirect ('sale_interface')

        except:
            messages.error(request, "Не удалось открыть смену. Сообщите администратору.")
            return redirect ('sale_interface')

    else:
        auth.logout(request)
        return redirect("login")


def fiscal_day_close (request):
    if request.user.is_authenticated:
        users_sales=Group.objects.get(name="sales").user_set.all()
        #users_admin=Group.objects.get(name="admin").user_set.all()
        if request.user in users_sales:
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)

            if shop.shift_status == False:#False means the shift is open
                try:
                    auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
                    uuid_number=uuid.uuid4()

                    task = {
                    "uuid": str(uuid_number),
                    "request": 
                    [{
                        "type": "closeShift",
                        "operator": 
                        {
                            "name": request.user.last_name,
                            "vatin": "5257173237"
                        }
                    }]
                    }
               
                    response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)

                except:
                    messages.error(request, "Не удалось закрыть смену. Сообщите администратору.")
                    return redirect ('sale_interface')
                
                session_shop=request.session['session_shop']
                shop=Shop.objects.get(id=session_shop)
                shop.shift_status=True
                shop.save()

                messages.error(request, "Смена закрыта.")
                return redirect ('sale_interface')
            else:
                messages.error(request, "Невозможно закрыть смену, так как смена уже закрыта.")
                return redirect ('sale_interface')
        else:
            return redirect ('sale_interface')

    else:
        auth.logout(request)
        return redirect("login")

def reportX (request):
    if request.user.is_authenticated:
        users_sales=Group.objects.get(name="sales").user_set.all()
        #users_admin=Group.objects.get(name="admin").user_set.all()
        if request.user in users_sales:
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            auth=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
            uuid_number=uuid.uuid4()

            task = {
            "uuid": str(uuid_number),
            "request": 
            [{
                "type": "reportX",
                "operator": 
                {
                    "name": request.user.last_name,
                    "vatin": "5257173237"
                }
            }]
            }

            try:
                response=requests.post('http://93.157.253.248:16732/api/v2/requests', auth=auth, json=task)

                messages.error(request, "Отчет сфорирован.")
                return redirect ('sale_interface')

            except:
                messages.error(request, "Не удалось сформировать отчет. Возможная причина: смена закрыта. Сообщите администратору")
                return redirect ('sale_interface')

    else:
        auth.logout(request)
        return redirect ('login')

def get_shift_status (request):
    if request.user.is_authenticated:
        auth_register=HTTPBasicAuth('NetMaster', 'Ylhio65v39aZifol_01')
        uuid_number=uuid.uuid4()

        task = {
        "uuid": str(uuid_number),
        "request": 
            {"type": "getShiftStatus"}
        }

        try:
            response=requests.post('http://127.0.0.1:16732/api/v2/requests', json=task, auth=auth_register)
            status_code=response.status_code
            print(status_code)
            text=response.text
            print(text)
            url=response.url
            json=response.json()
            print(json)
            print(response.content)
            messages.error(request, "Посмотрите на чеке статус смены.")
            return redirect ('sale_interface')

        except:
            messages.error(request, "Не удалось определить стстус смены. Сообщите администратору.")
            return redirect ('sale_interface')

    else:
        auth.logout(request)
        return redirect ('login')

def z_report (request):
    pass