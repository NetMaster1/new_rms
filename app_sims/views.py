#from winreg import REG_WHOLE_HIVE_VOLATILE
from django.forms import NullBooleanField
from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory
from app_reports.models import ReportTempId, Sim_report
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


#creates a register of sim forms which has been returned to operator
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

#takes a list of forms to be returned to operator & checks them against sim_return_record, sim_register_record & rhos
#returns an excel file with statuses of forms to be found & returned to operator 
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
<<<<<<< HEAD

        context = {
            'srrs': sim_ret_recs,
            'document': document
        }
        return render (request, 'sims/change_sim_return_posted.html', context )
    else:
        auth.logout(request)
        return redirect("login")

def change_sim_register_posted (request, document_id):
    if request.user.is_authenticated:
        document=Document.objects.get(id=document_id)
        sim_reg_recs=SimRegisterRecord.objects.filter(document=document)
        numbers = sim_reg_recs.count()
        for srr, i in zip(sim_reg_recs, range(numbers)):
            srr.enumerator = i + 1
            srr.save()

        context = {
            'srrs': sim_reg_recs,
            'document': document
        }

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
    

def sim_initial_input_report(request):
    if request.user.is_authenticated:
        category=ProductCategory.objects.get(name="Ввод остатков ТМЦ")
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




def sim_return_report (request):
    category=ProductCategory.objects.get(name='Сим_карты')
    if request.method == "POST":
        pass

    else:
        return render(request, "sims/sim_return_report.html")

=======

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




def sim_return_report (request):
    category=ProductCategory.objects.get(name='Сим_карты')
    if request.method == "POST":
        pass

    else:
        return render(request, "sims/sim_return_report.html")

>>>>>>> 10a853c8045bc3e041d050830f2fadad4e792413
def delete_sim_reports (request):
    reports=Sim_report.objects.all()
    for i in reports:
        i.delete()
    return redirect ('activation_list')

def sim_dispatch (request):
    pass