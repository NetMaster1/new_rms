from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory
from app_reports.models import ReportTempId, Sim_report
from .models import SimReturnRecord
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import datetime
from datetime import date, timedelta
import pytz
import pandas
import xlwt
from django.http import HttpResponse, JsonResponse


# Create your views here.
def sim_return_list (request):
    category=ProductCategory.objects.get(name='Сим_карты')
    doc_type=DocumentType.objects.get(name='Сдача РФА')
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
            if SimReturnRecord.objects.filter(imei=row.Imei).exists():
                pass
            else:
                srr = SimReturnRecord.objects.create(
                    document=document,
                    srr_type=document.title,
                    imei=row.Imei,
                    name=row.Name,
                    user=request.user
                )
            # if SimReturnRecord.objects.filter(imei=row.Imei).exists():
            #     if SimReturnRecord.objects.filter(document=document).exists():
            #         srr_error=SimReturnRecord.objects.filter(document=document)
            #         for item in srr_error:
            #             item.delete()
            #         document.delete()
            #     string=f'Реестр не сформирован. РФА {row.Name} c IMEI: {row.Imei} уже сдана.'
            #     messages.error(request, string)
            #     return redirect("sim_return_list")
            # else: 
                
        return redirect("log")
    else:
        return render(request, "sims/sim_return_list.html")

def change_sim_return_posted (request, document_id):
    document=Document.objects.get(id=document_id)
    srrs=SimReturnRecord.objects.filter(document=document)
    numbers = srrs.count()
    for srr, i in zip(srrs, range(numbers)):
        srr.enumerator = i + 1
        srr.save()

    context = {
        'srrs': srrs,
        'document': document
    }
    return render (request, 'sims/change_sim_return_posted.html', context )

def sim_return_report (request):
    category=ProductCategory.objects.get(name='Сим_карты')
    if request.method == "POST":
        pass

    else:
        return render(request, "sims/sim_return_report.html")

def activation_list (request):
    report_id=ReportTempId.objects.create()
    category=ProductCategory.objects.get(name='Сим_карты')
    if request.method == 'POST':
        file = request.FILES["file_name"]
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            if RemainderHistory.objects.filter(imei=row.Imei).exists():
                rho_latest=RemainderHistory.objects.filter(imei=row.Imei).latest('created')
                sim_report=Sim_report.objects.create(
                    report_id=report_id,
                    name=row.Name,
                    shop=rho_latest.shop.name,
                    date=rho_latest.created,
                    user=rho_latest.user.last_name,
                    document=rho_latest.document.id,
                    imei=row.Imei,
                    status=rho_latest.rho_type.name,
                    price=rho_latest.retail_price
                )
                if SimReturnRecord.objects.filter(imei=row.Imei).exists():
                    sim_report.return_mark="РФА сдана"
                    sim_report.save()
            else:
                string=f'Отчет не сформирован. Товар {row.Name} с IMEI {row.Imei} отсутствует в базе данных.'
                messages.error(request,  string)
                if Sim_report.objects.filter(report_id=report_id).exists():
                    sim_report=Sim_report.objects.filter(report_id=report_id)
                    for sim in sim_report:
                        sim.delete()
                    report_id.delete()
                return redirect("activation_list")

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
        columns = ["Name", "IMEI", "Status", "Price", "Shop", "Date", "User", "Document", "Return"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)


        # sheet body, remaining rows
        font_style = xlwt.XFStyle()
        report_query = Sim_reports=Sim_report.objects.filter(report_id=report_id)
        query = report_query.values_list("name", "imei", "status", "price", "shop", "date", "user", "document", "return_mark")

        for row in query:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response
#=======================End of Excel Upload Module================================

    else:
        return render(request, 'sims/activation_list.html')


    
