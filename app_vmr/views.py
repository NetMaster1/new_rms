from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
import datetime
from datetime import date, timedelta
import pytz
from django.contrib import messages, auth
from . models import VMR_check
from app_reference.models import Shop



# Create your views here.

def open_vmr_check_form(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        shops=Shop.objects.all()
        users = User.objects.all().order_by('last_name')
        context = {
            'shops': shops,
            'users': users,
        }

        return render(request, "vmr/vmr_check.html", context)
    auth.logout(request)
    return redirect("login")


def save_vmr_daily_check_rep(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        tdelta=datetime.timedelta(hours=3)
        dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
        dateTime=dT_utcnow+tdelta
        #dateTime=dT_utcnow.astimezone(pytz.timezone('Europe/Moscow'))#Mocow time
        if request.method == "POST":
            shop = request.POST["shop"]
            user = request.POST["user"]
            mnp_offer = request.POST["mnp_offer"]
            rtc_offer = request.POST["rtc_offer"]
            sim_offer = request.POST["sim_offer"]
            mixx_offer = request.POST["mixx_offer"]
            # phone_offer = request.POST["phone_offer"]
            # client_problem_res = request.POST["client_problem_res"]

            user=User.objects.get(id=user)
            shop=Shop.objects.get(id=shop)
        
            vmr_check = VMR_check.objects.create(
                created=dateTime,
                user=user,
                shop=shop.name,
                mnp_offer = mnp_offer,
                rtc_offer = rtc_offer,
                sim_offer = sim_offer,
                mixx_offer = mixx_offer,
                # phone_offer = phone_offer,
                # client_problem_res = client_problem_res,
            )

        return redirect("log")
    auth.logout(request)
    return redirect("login")

def edit_vmr_daily_check_rep(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        if request.method == "POST":
            rep_id=request.POST['id']
            shop = request.POST["shop"]
            user = request.POST["user"]
            mnp_offer = request.POST["mnp_offer"]
            rtc_offer = request.POST["rtc_offer"]
            sim_offer = request.POST["sim_offer"]
            mixx_offer = request.POST["mixx_offer"]
            # phone_offer = request.POST["phone_offer"]
            # client_problem_res = request.POST["client_problem_res"]
            
            user=User.objects.get(id=user)
            # shop=Shop.objects.get(id=shop)

            report=VMR_check.objects.get(id=rep_id)
            report.shop=shop
            report.user=user
            report.mnp_offer=mnp_offer
            report.rtc_offer=rtc_offer
            report.sim_offer=sim_offer
            report.mixx_ofer=mixx_offer
            report.save()


        return redirect("vmr_today_reps")
    auth.logout(request)
    return redirect("login")

def vmr_today_reps(request):
    group=Group.objects.get(name="admin").user_set.all()
    if request.user in group:
        tday=datetime.date.today()
        print(tday)
        users=User.objects.all()
        shops=Shop.objects.all()
        vmr_today_reps=VMR_check.objects.filter(created__date=tday)
   
        context = {
            'vmr_today_reps': vmr_today_reps,
            'shops': shops,
            'users': users,
            }
        return render(request, "vmr/vmr_today_reps.html", context)
        return redirect("log")
    auth.logout(request)
    return redirect("login")
