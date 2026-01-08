#from winreg import REG_WHOLE_HIVE_VOLATILE
from django.forms import NullBooleanField
from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory
from app_reports.models import ReportTempId, Sim_report, DailyActivation
from .models import SimReturnRecord, SimRegisterRecord
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import datetime
from datetime import date, timedelta
import pytz
import pandas
import xlwt
from django.http import HttpResponse, JsonResponse
#from requests.auth import HTTPBasicAuth
from django.contrib import messages, auth

#Работа с субдилером
#Перемещаем сим карты на склад субдилера (Перемещение ТМЦ). Склад создан в программе.
#После активации, продажи получаем реестр от субдилера или с нашей точки.
#Вводим данный реестр в e-rms. "Ввод реестра на сдачу РФА". Формируется SimReturnRecord
#Затем снимаем отчет из WD и вводим его в erms "Ввод реестра номеров, зарегистрированных в WD". Формируется SimRegisterRecord
#Затем жмем Ввод реестра долгов по РФА. Вводим файл реестра, полученного от субдилера и формируем отчет по не сданным

#creates a register of sim forms which has been returned to operator
#Ввод реестра РФА на сдачу
#данная функция создаёт RHO 'Сдача РФА' и затрагивает только субдилерские склады
#и формирует таблицу SimReturnRecord
def sim_return_list (request):
    if request.user.is_authenticated:
        category=ProductCategory.objects.get(name='Сим_карты')
        doc_type=DocumentType.objects.get(name='Сдача РФА')
        tdelta=datetime.timedelta(hours=3)
        dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
        dateTime=dT_utcnow+tdelta
        #forms a list of subdealer shops
        shops=Shop.objects.filter(subdealer=True)
        if request.method == "POST":
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            document = Document.objects.create(
                created=dateTime,
                user=request.user, 
                title=doc_type,
                posted=True,
                sum=0
            )
            for i in range(cycle):
                row = df1.iloc[i]#reads each row of the df1 one by one
                #creates rhos only for subdealer shops making corrents remainder for subdealers
                for shop in shops:
                    if RemainderHistory.objects.filter(shop=shop, imei=row.Imei,created__lt=dateTime).exists():
                        rho_latest_before= RemainderHistory.objects.filter(shop=shop, imei=row.Imei, created__lt=dateTime).latest('created')
                        # creating remainder_history
                        rho = RemainderHistory.objects.create(
                            document=document,
                            created=document.created,
                            rho_type=doc_type,
                            user=request.user,
                            shop=rho_latest_before.shop,
                            #product_id=product,
                            category=rho_latest_before.category,
                            imei=row.Imei,
                            name=row.Name,
                            retail_price=rho_latest_before.retail_price,
                            #av_price=rho_latest_before.av_price,
                            pre_remainder=rho_latest_before.current_remainder,
                            incoming_quantity=0,
                            outgoing_quantity=1,
                            current_remainder=0,
                            sub_total=rho_latest_before.retail_price,
                        )
                #if SimReturnRecord.objects.filter(imei=row.Imei).exists():
                #     if SimReturnRecord.objects.filter(document=document).exists():
                #         srr_error=SimReturnRecord.objects.filter(document=document)
                #         for item in srr_error:
                #             item.delete()
                #         document.delete()
                #     string=f'Реестр не сформирован. РФА {row.Name} c IMEI: {row.Imei} уже сдана.'
                #     messages.error(request, string)
                #     return redirect("sim_return_list")
                # else: 
                    
                        
                #creates a register of sims returned to operator including sims from monobrand shops
                SimRetRec = SimReturnRecord.objects.create(
                    document=document,
                    srr_type=document.title,
                    imei=row.Imei,
                    name=row.Name,
                    user=request.user
                )
                #=======================================================
                    
            return redirect("log")
        else:
            return render(request, "sims/sim_return_list.html")
    else:
        auth.logout(request)
        return redirect("login")

#creates a register of sim forms which has been registered in WebDealer
#Ввод реестра номеров, зарегистрированнх в WD
#реестр выгружается из WD
#функция формирует таблицу SimRegisterRecord
def sim_register_list(request):
    if request.user.is_authenticated:
        category=ProductCategory.objects.get(name='Сим_карты')
        doc_type=DocumentType.objects.get(name='Регистрация РФА')
        tdelta=datetime.timedelta(hours=3)
        dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
        dateTime=dT_utcnow+tdelta
        if request.method == "POST":
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            document = Document.objects.create(
                created=dateTime,
                user=request.user, 
                title=doc_type,
                posted=True,
                sum=0
            )
            for i in range(cycle):
                row = df1.iloc[i]#reads each row of the df1 one by one
                   
                #creates a register of sims registered in WebDealer
                SimRegRec = SimRegisterRecord.objects.create(
                    document=document,
                    sim_reg_type=document.title,
                    imei=row.Imei,
                    name=row.Name,
                    user=request.user
                )
                #=======================================================
                    
            return redirect("log")
        else:
            return render(request, "sims/sim_register_list.html")
    else:
        auth.logout(request)
        return redirect("login")

#takes SimReturnRecord и сверяет его с SimRegisterRecord. Выявляет РФА, которые были зарегистрированы, но не былил сданы.
#returns an excel file with statuses of forms to be found & returned to operator 
#Ввод реестра долгов по РФА
def activation_list (request):
    report_id=ReportTempId.objects.create()
    category=ProductCategory.objects.get(name='Сим_карты')
    reports=Sim_report.objects.all()
    doc_type=DocumentType.objects.get(name='Перемещение ТМЦ')
    tdelta=datetime.timedelta(hours=3)
    dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
    dateTime=dT_utcnow+tdelta
    for i in reports:
        i.delete()
    if request.method == 'POST':
        reports=Sim_report.objects.all()
        for i in reports:
            i.delete()
        #соответсвующий SimReturnReсord
        file = request.FILES["file_name"]
        df1 = pandas.read_excel(file)
        cycle = len(df1)#number of rows
        #this is done to exclude transfer_sender rhos
        rhos=RemainderHistory.objects.exclude(rho_type=doc_type, status=False)
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            if rhos.filter(imei=row.Imei,created__lt=dateTime).exists():
                rho_latest=rhos.filter(imei=row.Imei).latest('created')
                sim_report=Sim_report.objects.create(
                    report_id=report_id,
                    name=row.Name,
                    shop=rho_latest.shop.name,
                    date=rho_latest.created,
                    document=rho_latest.document.id,
                    imei=row.Imei,
                    status=rho_latest.rho_type.name,
                    price=rho_latest.retail_price
                )
                if rho_latest.user is None:
                    sim_report.user is None
                else:
                    sim_report.user=rho_latest.user.last_name
                if SimReturnRecord.objects.filter(imei=row.Imei).exists():
                    sim_report.return_mark="РФА сдана"
                if SimRegisterRecord.objects.filter(imei=row.Imei).exists():
                    sim_report.WD_status="РФА зарегистрирована"
                sim_report.save()
            else:
                sim_report=Sim_report.objects.create(
                    report_id=report_id,
                    name=row.Name,
                    imei=row.Imei,
                    return_mark='Информация отсутствует'
                )
                # string=f'Отчет не сформирован. Товар {row.Name} с IMEI {row.Imei} отсутствует в базе данных.'
                # messages.error(request,  string)
                # if Sim_report.objects.filter(report_id=report_id).exists():
                #     sim_report=Sim_report.objects.filter(report_id=report_id)
                #     for sim in sim_report:
                #         sim.delete()
                #     report_id.delete()
                # return redirect("activation_list")

#=======================Uploading to Excel Module===================================
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = (
            "attachment; filename=Remainder_" + str(datetime.date.today()) + ".xls"
        )

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Activation")

        # sheet header in the first row (column titles)
        row_num = 0
        font_style = xlwt.XFStyle()
        columns = ["Name", "IMEI", "Status", "Price", "Shop", "Date", "User", "Document", "Return", "WebDealer"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)


        # sheet body, remaining rows
        font_style = xlwt.XFStyle()
        report_query = Sim_reports=Sim_report.objects.filter(report_id=report_id)
        query = report_query.values_list("name", "imei", "status", "price", "shop", "date", "user", "document", "return_mark", "WD_status")

        for row in query:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response
#=======================End of Excel Upload Module================================
    else:
        return render(request, 'sims/activation_list.html')

def change_sim_return_posted(request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        sim_ret_recs=SimReturnRecord.objects.filter(document=document)
        numbers = sim_ret_recs.count()
        for srr, i in zip(sim_ret_recs, range(numbers)):
            srr.enumerator = i + 1
            srr.save()

        context = {
            'srrs': sim_ret_recs,
            'document': document
        }
        return render (request, 'sims/change_sim_return_posted.html', context )
    else:
        auth.logout(request)
        return redirect("login")

def change_sim_register_posted (request, document_id):
    pass

def delete_sim_return_posted(request, document_id):
    pass

def delete_sim_register_posted (request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        srrs=SimRegisterRecord.objects.filter(document=document)
        for i in srrs:
            i.delete()
        document.delete() 
        return redirect("log")
    else:
        auth.logout(request)
        return redirect("login")

def sim_delivery_MB(request):
    if request.user.is_authenticated:
        category=ProductCategory.objects.get(name="Сим_карты")
        doc_type=DocumentType.objects.get(name="Поступление ТМЦ")
        rhos=RemainderHistory.objects.filter(category=category, rho_type=doc_type)

        #=======================Uploading to Excel Module===================================
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = (
            "attachment; filename=Remainder_" + str(datetime.date.today()) + ".xls"
        )

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Activation")

        # sheet header in the first row (column titles)
        row_num = 0
        font_style = xlwt.XFStyle()
        columns = ["Date", "IMEI", "Name"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)


        # sheet body, remaining rows
        font_style = xlwt.XFStyle()
       
        query = rhos.values_list("created", "imei", "name")

        for row in query:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response
#=======================End of Excel Upload Module================================

    else:
        auth.logout(request)
        return redirect("login")

def sim_sales_MB(request):
    pass

def sim_sign_off_MB(request):
    pass

#Отчет по сдаче РФА по субдилерам
def sim_return_report (request):
    category=ProductCategory.objects.get(name='Сим_карты')
    if request.method == "POST":
        pass
    else:
        return render(request, "sims/sim_return_report.html")

def delete_sim_reports (request):
    reports=Sim_report.objects.all()
    for i in reports:
        i.delete()
    return redirect ('activation_list')

def activation_check(request):
    return render (request, 'sims/activation_check.html')

def sale_against_activation_rep (request):
    if request.user.is_authenticated:
        if request.method == "POST":
            category=ProductCategory.objects.get(name="Сим_карты")
            rho_type=DocumentType.objects.get(name='Продажа ТМЦ')
            start_date = request.POST['start_date']
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = request.POST['end_date']
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            end_date = end_date + timedelta(days=1)
            #===================Date when the report is taken======================
            dateTime = datetime.date.today()
            dateTime = dateTime.strftime("%Y-%m-%d")
            #===========================================
            report_id = ReportTempId.objects.create()
            file = request.FILES["file_name"]
            df1 = pandas.read_excel(file)
            cycle = len(df1)
            for i in range(cycle):
                row = df1.iloc[i]#reads each row of the df1 one by one
                if RemainderHistory.objects.filter(created__gt=start_date, created__lt=end_date, rho_type=rho_type, category=category, imei=row.ICC, retail_price=row.FIRST_PAY).exists():
                    pass
                else:
                    if RemainderHistory.objects.filter(imei=row.ICC).exists():
                        sim_card=RemainderHistory.objects.filter(imei=row.ICC).latest('-created')
               
                        item=DailyActivation.objects.create(
                            report_id=report_id,
                            activation_date=str(row.ACTIVATION_DATE),
                            icc=row.ICC,
                            phone=row.MSISDN,
                            shop=sim_card.shop.name,
                            report_price=row.FIRST_PAY,
                            shop_price=sim_card.retail_price,
                            rho_type=sim_card.rho_type.name,
                            tarif_name=row.TRPL_NAME
                        )
                        
                    else:
                        item=DailyActivation.objects.create(
                            report_id=report_id,
                            activation_date=str(row.ACTIVATION_DATE),
                            icc=row.ICC,
                            phone=row.MSISDN,
                            report_price=row.FIRST_PAY,
                            rho_type="Отсутствует в БД",
                            tarif_name=row.TRPL_NAME
                        )
                        
            sim_daily_rep=DailyActivation.objects.filter(report_id=report_id)
            #==========================Convert to Excel module=========================================
            response = HttpResponse(content_type="application/ms-excel")
            response["Content-Disposition"] = (
                "attachment; filename=ActivationReport_" + str(dateTime) + ".xls"
            )
            # str(datetime.date.today())+'.xls'

            wb = xlwt.Workbook(encoding="utf-8")
            ws = wb.add_sheet('Sheet_1')

            # sheet header in the first row
            row_num = 0
            font_style = xlwt.XFStyle()

            columns = ['Дата активации', 'ICC', 'Номер', "Точка", "Цена из отчета", "Цена из Erms", 'Документ', 'Тариф']
            for col_num in range(len(columns)):
                ws.write(row_num, col_num + 1, columns[col_num], font_style)
            # sheet body, remaining rows
            font_style = xlwt.XFStyle()

            row_num = 1
            for item in sim_daily_rep:
                col_num = 1
                ws.write(row_num, col_num, item.activation_date, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.icc, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.phone, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.shop, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.report_price, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.shop_price, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.rho_type, font_style)
                col_num +=1
                ws.write(row_num, col_num, item.tarif_name, font_style)
                row_num +=1

            wb.save(response)
            return response

def sim_dispatch (request):
    pass