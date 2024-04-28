from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import Identifier, RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory, Month, Year
from app_reports.models import ReportTempId, Sim_report
from app_personnel.models import BulkSimMotivation
from .models import KPIMonthlyPlan, KPI_performance, GI_report, Focus_report
from django.contrib import messages, auth
from django.contrib.auth.models import User, Group
import datetime, calendar
from datetime import date, timedelta
import pandas

  
#================Entering Monthly Plans=====================
def kpi_excel_input (request):
    if request.user.is_authenticated:
        if request.method == "POST":
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            try:
                for i in range(cycle):
                    row = df1.iloc[i]#reads each row of the df1 one by one
                    if KPIMonthlyPlan.objects.filter(shop=row.Shop, month_reported=row.Month, year_reported=row.Year).exists():
                        messages.error(request,"План уже введён. Удалите предыдущую версию, чтобы загрузить новый.",)
                        return redirect ('log')
                    else:
                        item=KPIMonthlyPlan.objects.create(
                            shop=row.Shop,
                            month_reported=row.Month,
                            year_reported=row.Year,
                            GI=row.GI,
                            MNP=row.MNP,
                            HighBundle=row.HighBundle,
                            smartphones_sum=row.Smartphones,
                            insurance_charge=row.Insurance,
                            wink_roubles=row.Wink,
                            HomeInternet=row.HI,
                            RT_equip_roubles=row.RT_equip_roubles,
                            RT_active_cam=row.RT_equip_items,
                            upsale=row.Upsale,
                        )
                messages.error(request,"План успешно введён.",)
                return redirect ('kpi_excel_input')
            except:
                messages.error(request,"План не введён. Выберите нужный формат файла",)
                return redirect ('kpi_excel_input')
        else:
            #return render(request, "kpi/kpi_auto_input.html")
            return render(request, "kpi/inputPage.html")
    else:
        auth.logout(request)
        return redirect("login")

def kpi_performance_update (request):
    if request.user.is_authenticated:
        shops=Shop.objects.filter(retail=True, active=True, offline=True)
        monthes=Month.objects.all()
        years=Year.objects.all()
        if request.method == "POST":
            shop = request.POST["shop"]
            #shop=Shop.objects.get(id=shop)
            month = request.POST["month"]
            #month=Month.objects.get(id=month)
            year = request.POST["year"]
            #year=Year.objects.get(id=year)
            upsale=request.POST.get('upsale')
            MNP=request.POST.get('MNP')
            VMR=request.POST.get('VMR')
            HI_T2=request.POST.get('HI_T2')
            HI_RT=request.POST.get('HI_RT')
            if KPI_performance.objects.filter(shop=shop, month_reported=month, year_reported=year).exists():
                item=KPI_performance.objects.get(shop=shop, month_reported=month, year_reported=year)
                counter=0
                if upsale:
                    item.upsale=upsale
                    counter+=1
                if VMR:
                    item.VMR=VMR
                    counter+=1
                if MNP:
                    item.MNP=MNP
                    counter+=1
                if HI_T2:
                    item.HomeInternet_T2=HI_T2
                    counter+=1
                if HI_RT:
                    item.HomeInternet_RT=HI_RT
                    counter+=1
                if counter==0:
                    context = {
                        'shops': shops,
                        'monthes': monthes,
                        'years': years
                        }
                    messages.error(request,"Вы не ввели ни одного показателя.",)    
                    return render (request, "kpi/kpi_performance_update.html", context)
                else:
                    item.save()
                    return redirect ('kpi_performance')
            else:
                # context = {
                #     'shops': shops,
                #     'monthes': monthes,
                #     'years': years
                # }
                messages.error(request,"Измения не внесены, так как планов для этого периода или точке не существует. Введите сначала план.",)
                return redirect('kpi_excel_input')
                #return render (request, "kpi/kpi_performance_update.html", context)

        else:
            
            context = {
               'shops': shops,
               'monthes': monthes,
               'years': years
            }
            return render (request, "kpi/kpi_performance_update.html", context)


    else:
        auth.logout(request)
        return redirect("login")

#================Quering data & comparing it with plans==================
def kpi_performance(request):
    if request.user.is_authenticated:
        shops=Shop.objects.filter(retail=True, active=True, offline=True)
        monthes=Month.objects.all()
        years=Year.objects.all()
      
        context = {
            'shops': shops,
            'monthes': monthes,
            'years': years,
        }
        return render(request, "kpi/kpi_performance.html", context)
    else:
        auth.logout(request)
        return redirect("login")
    
def kpi_monthly_report_per_shop (request):
    if request.user.is_authenticated:
        sim_price=BulkSimMotivation.objects.get(id=1)
        users = Group.objects.get(name='sales').user_set.all()
        #group = Group.objects.get(name='admin').user_set.all()
        if request.user in users:
            session_shop=request.session['session_shop']
            shop=Shop.objects.get(id=session_shop)
            month=datetime.datetime.now().month
            month=Month.objects.get(id=month)
            year=datetime.datetime.now().year
            year=Year.objects.get(name=year)
            if KPIMonthlyPlan.objects.filter(shop=shop, month_reported=month, year_reported=year.name).exists():
                plan_item=KPIMonthlyPlan.objects.get(shop=shop, month_reported=month, year_reported=year.name )
            else:
                messages.error(request,"Планов для этого периода или точки не существуе. Обратитесь к администратору.",)
                return redirect('sale_interface')
        else:
            if request.method == "POST":
                shop = request.POST["shop"]
                month = request.POST["month"]
                month=Month.objects.get(id=month)
                year = request.POST["year"]
                year=Year.objects.get(id=year)
                shop=Shop.objects.get(id=shop)

            if KPIMonthlyPlan.objects.filter(shop=shop, month_reported=month.name, year_reported=year.name).exists():
                plan_item=KPIMonthlyPlan.objects.get(shop=shop, month_reported=month.name, year_reported=year.name )
            else:
                messages.error(request,"Планов для этого периода не существует. Введите сначала план",)
                return redirect('kpi_excel_input')
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        current_date=datetime.datetime.now().day
        queryset = RemainderHistory.objects.filter(shop=shop, created__year=year.name, created__month=month.id, rho_type=doc_type).exclude(created__day=current_date)
        category_sim=ProductCategory.objects.get(name='Сим_карты')
        category_smartphones=ProductCategory.objects.get(name='Смартфоны')
        category_insurance=ProductCategory.objects.get(name='Страховки')
        category_wink=ProductCategory.objects.get(name='Подписки')
        category_RT_equipment=ProductCategory.objects.get(name='Оборудование РТК')
        # if request.method == "POST":
            
        #==========================================
        query=queryset.filter(category=category_smartphones)
        smartphones_sum=0
        for item in query:
            smartphones_sum+=item.retail_price
        #==========================================
        query=queryset.filter(category=category_sim)
        number_of_sims=0
        number_of_focus_sims=0
        for item in query:
            number_of_sims+=1
            if item.retail_price>=sim_price.sim_price and item.retail_price<=1550:
                number_of_focus_sims+=1
        #==========================================
        query=queryset.filter(category=category_RT_equipment)
        RT_equipment_sum=0
        for item in query:
            RT_equipment_sum+=item.retail_price
        #==========================================
        query=queryset.filter(category=category_insurance)
        insurance_sum=0
        for item in query:
            insurance_sum+=item.retail_price
        #==========================================
        query=queryset.filter(category=category_wink)
        wink_sum=0
        wink_items=0
        for item in query:
            wink_sum+=item.retail_price
            wink_items+=1
        #=================================================
        camera_counter=0
        for item in query:
            if 'Видеокамера' in item.name:
                camera_counter=+1

        if KPI_performance.objects.filter(shop=shop, month_reported=month, year_reported=year).exists():
            item=KPI_performance.objects.get(shop=shop, month_reported=month, year_reported=year)
            item.smartphones_sum=smartphones_sum
            item.GI=number_of_sims
            item.HighBundle=number_of_focus_sims
            item.insurance_charge=insurance_sum
            item.wink_roubles=wink_sum
            item.wink_item=wink_items
            item.RT_equip_roubles=RT_equipment_sum
            item.RT_active_cam=camera_counter
            item.save()
        else:
            #identifier = Identifier.objects.create()
            item=KPI_performance.objects.create(
                #identifier=identifier,
                month_reported=month,
                year_reported=year,
                shop=shop,
                smartphones_sum=smartphones_sum,
                GI=number_of_sims,
                HighBundle=number_of_focus_sims,
                insurance_charge=insurance_sum,
                wink_roubles=wink_sum,
                wink_item=wink_items,
                RT_equip_roubles=RT_equipment_sum,
                RT_active_cam=camera_counter,

                )
        day_before=datetime.datetime.today().day -1
        year=int(year.name)
        month=int(month.id)
        num_days = calendar.monthrange(year, month)[1]
        context = {
            'month': month,
            'year': year,
            'shop':shop,
            'item': item,
            'plan_item': plan_item,
            'day_before': day_before,
            'num_days': num_days,

        }
        return render(request, "kpi/kpi_per_shop.html", context)
        
    else:
        auth.logout(request)
        return redirect("login")

def GI_report_input (request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        monthes=Month.objects.all()
        years=Year.objects.all()
        context = {
            'monthes': monthes,
            'years': years,
            'identifier': identifier,
        }
        return render(request, "kpi/GI_report_input.html", context)

    else:
        auth.logout(request)
        return redirect("login")

def GI_report_output(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    if request.method == "POST":
        GI=ProductCategory.objects.get(name='Сим_карты')
        month= request.POST["month"]
        month=Month.objects.get(id=month)
        year = request.POST["year"]
        year=Year.objects.get(id=year)
        shops=Shop.objects.filter(retail=True, active=True, offline=True)
        #shops=Shop.objects.all()
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        current_date=datetime.datetime.now().day
        counter=0#the counter shows if all plan_itme.GIs are equal to zero. If so it redirects to 'kpi_excel_input'
        for shop in shops:
            if KPIMonthlyPlan.objects.filter(shop=shop, month_reported=month.name, year_reported=year.name).exists():
                plan_item=KPIMonthlyPlan.objects.get(shop=shop, month_reported=month.name, year_reported=year.name )
                plan_GI=plan_item.GI
                counter+=1
            else:
                plan_GI=0
            queryset = RemainderHistory.objects.filter(shop=shop, created__year=year.name, created__month=month.id, rho_type=doc_type, category=GI).exclude(created__day=current_date)
            year_edited=int(year.name)
            month_edited=int(month.id)
            num_days = calendar.monthrange(year_edited, month_edited)[1]
            if datetime.datetime.now().month != month.id:
                day_before=num_days
            else:
                day_before=datetime.datetime.today().day -1
            GI_counter=0
            for item in queryset:
                GI_counter+=1
            # if GI_report.objects.filter(identifier=identifier).exists():
            #     query=GI_report.objects.filter(identifier=identifier)

            # else:
            item=GI_report.objects.create(
                identifier = identifier,
                shop=shop,
                year_reported=year,
                month_reported=month,
                GI=GI_counter,
                GI_plan=plan_GI,
                date_before_current=day_before,
                days_of_the_month=num_days
            )
            # if KPIMonthlyPlan.objects.filter(shop=shop, month_reported=month.name, year_reported=year.name).exists():
        #     plan_item=KPIMonthlyPlan.objects.get(shop=shop, month_reported=month.name, year_reported=year.name )
        # else:
        #     messages.error(request,"Планов для этого периода не существует. Введите сначала план",)
        #     return redirect('kpi_excel_input')
        if counter==0:
            items=GI_report.objects.filter(identifier=identifier)
            for item in items:
                item.delete()
            messages.error(request, f'Планов для {month} {year} не существует. Введите сначала план',)
            return redirect('kpi_excel_input')
        query=GI_report.objects.filter(identifier=identifier)

        context = {
            'query': query,
            'identifier': identifier,
            'month': month,
            'year': year,
        
        }
        return render (request, 'kpi/GI_report_output.html', context)



    context = {
        'identifier': identifier,
        'query': query
    }
    return render(request, "kpi/GI_report_output.html", context)

def close_GI_report(request, identifier_id):
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        items=GI_report.objects.filter(identifier=identifier)
        for item in items:
            item.delete()
        return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")

#==================================================================
def focus_report_input(request):
    if request.user.is_authenticated:
        identifier = Identifier.objects.create()
        monthes=Month.objects.all()
        years=Year.objects.all()
        context = {
            'monthes': monthes,
            'years': years,
            'identifier': identifier,
        }
        return render(request, "kpi/focus_report_input.html", context)

    else:
        auth.logout(request)
        return redirect("login")
    
def focus_report_output(request, identifier_id):
    identifier=Identifier.objects.get(id=identifier_id)
    sim_price=BulkSimMotivation.objects.get(id=1)
    if request.method == "POST":
        focus=ProductCategory.objects.get(name='Сим_карты')
        month= request.POST["month"]
        month=Month.objects.get(id=month)
        year = request.POST["year"]
        year=Year.objects.get(id=year)
        shops=Shop.objects.filter(retail=True, active=True, offline=True)
        #shops=Shop.objects.all()
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        current_date=datetime.datetime.now().day
        counter=0#the counter shows if all plan_item.HighBundles are equal to zero. If so it redirects to 'kpi_excel_input'
        for shop in shops:
            if KPIMonthlyPlan.objects.filter(shop=shop, month_reported=month.name, year_reported=year.name).exists():
                plan_item=KPIMonthlyPlan.objects.get(shop=shop, month_reported=month.name, year_reported=year.name )
                plan_focus=plan_item.HighBundle
                counter+=1
            else:
                plan_focus=0
            queryset = RemainderHistory.objects.filter(shop=shop, created__year=year.name, created__month=month.id, rho_type=doc_type, category=focus, retail_price__gte=sim_price.sim_price, retail_price__lt=1550).exclude(created__day=current_date)
            year_edited=int(year.name)
            month_edited=int(month.id)
            num_days = calendar.monthrange(year_edited, month_edited)[1]
            if datetime.datetime.now().month != month.id:
                day_before=num_days
            else:
                day_before=datetime.datetime.today().day -1
            focus_counter=0
            for item in queryset:
                focus_counter+=1
            item=Focus_report.objects.create(
                identifier = identifier,
                shop=shop,
                year_reported=year,
                month_reported=month,
                focus=focus_counter,
                focus_plan=plan_focus,
                date_before_current=day_before,
                days_of_the_month=num_days
            )
        if counter==0:
            items=Focus_report.objects.filter(identifier=identifier)
            for item in items:
                item.delete()
            messages.error(request, f'Планов для {month} {year} не существует. Введите сначала план',)
            return redirect('kpi_excel_input')
        query=Focus_report.objects.filter(identifier=identifier)

        context = {
            'query': query,
            'identifier': identifier,
            'month': month,
            'year': year,
        
        }
        return render (request, 'kpi/focus_report_output.html', context)


def close_focus_report(request, identifier_id):
    if request.user.is_authenticated:
        identifier=Identifier.objects.get(id=identifier_id)
        items=Focus_report.objects.filter(identifier=identifier)
        for item in items:
            item.delete()
        return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")



def close_kpi_report(request):
    if request.user.is_authenticated:
        #identifier=Identifier.objects.get(id=identifier)
        users = Group.objects.get(name='sales').user_set.all()
        #item=KPI_performance.objects.get(identifier=identifier)
        #item.delete()
        if request.user in users:
            return redirect ('sale_interface')
        else:
            return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")
    

