from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory, Month, Year
from app_reports.models import ReportTempId, Sim_report
from .models import KPIMonthlyPlan, KPI_performance
from django.contrib import messages, auth
from django.contrib.auth.models import User, Group
import datetime
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
                    if KPIMonthlyPlan.objects.filter(month_reported=row.Month, year_reported=row.Year).exists():
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
                            RT_active_cam=row.RT_equip_items
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

def kpi_adjustment (request):
    pass

#================Quering data & comparing it with plans==================
def kpi_performance(request):
    if request.user.is_authenticated:
        shops=Shop.objects.all()
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
                messages.error(request,"Планов для этого периода не существует. Введите сначала план",)
                return redirect('sale_interface')
        else:
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
                return redirect('log')
        doc_type = DocumentType.objects.get(name="Продажа ТМЦ")
        queryset = RemainderHistory.objects.filter(shop=shop, created__year=year.name, created__month=month.id, rho_type=doc_type)
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
            if item.retail_price>=650:
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
                camera_couner=+1
        
        if KPI_performance.objects.filter(month_reported=month, year_reported=year).exists():
            item=KPI_performance.objects.get(month_reported=month, year_reported=year)
        else:
            item=KPI_performance.objects.create(
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

        context = {
            'month': month,
            'year': year,
            'shop':shop,
            'item': item,
            'plan_item': plan_item,

        }
        return render(request, "kpi/kpi_per_shop.html", context)
        
    else:
        auth.logout(request)
        return redirect("login")
    
def close_kpi_report (request, item_id):
    if request.user.is_authenticated:
        users = Group.objects.get(name='sales').user_set.all()
        item=KPI_performance.objects.get(id=item_id)
        item.delete()
        if request.user in users:
            return redirect ('sale_interface')
        else:
            return redirect ('log')
    else:
        auth.logout(request)
        return redirect("login")