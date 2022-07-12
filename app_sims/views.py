from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory
from app_reports.models import ReportTempId, Sim_report
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from datetime import datetime, date, timedelta
import pandas
import xlwt
from django.http import HttpResponse, JsonResponse


# Create your views here.
def sim_return_list (request):
    shops = Shop.objects.all()
    category=ProductCategory.objects.get(name='Сим_карты')
    doc_type=DocumentType.objects.get(name='Сдача РФА')
    if request.method == "POST":
        dateTime=request.POST.get('dateTime', False)
        if dateTime:
            # converting dateTime in str format (2021-07-08T01:05) to django format ()
            dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")
            #adding seconds & microseconds to 'dateTime' since it comes as '2021-07-10 01:05:03:00' and we need it real value of seconds & microseconds
            current_dt=datetime.datetime.now()
            mics=current_dt.microsecond
            tdelta_1=datetime.timedelta(microseconds=mics)
            secs=current_dt.second
            tdelta_2=datetime.timedelta(seconds=secs)
            tdelta_3=tdelta_1+tdelta_2
            dateTime=dateTime+tdelta_3
        else:
            tdelta=datetime.timedelta(hours=3)
            dT_utcnow=datetime.datetime.now(tz=pytz.UTC)#Greenwich time aware of timezones
            dateTime=dT_utcnow+tdelta
        shop = request.POST["shop"]
        shop = Shop.objects.get(id=shop)
        file = request.FILES["file_name"]
        df1 = pandas.read_excel(file)
        cycle = len(df1)
        document = Document.objects.create(
            created=dateTime,
            shop_receiver=shop,
            user=request.user, 
            title=doc_type,
            posted=True,
            sum=0
        )
        for i in range(cycle):
            row = df1.iloc[i]#reads each row of the df1 one by one
            if RemainderHistory.objects.filter(imei=row.Imei).exists():
                rho_latest=RemainderHistory.objects.filer(imei=row.Imei).latest('created')
                pre_remainder=rho_latest.current_remainder
            else:
                if RemainderHistory.objects.filter(document=document).exists():
                    rhos=RemainderHistory.objects.filter(document=document)
                    for rho in rhos:
                        rho.delete()
                document.delete()
                string=f'Документ не проведен. Товар {row.Imei} отсутствует в базе данных'
                messages.error(request, string)
                return redirect("sim_return_list")
            rho = RemainderHistory.objects.create(
                document=document,
                rho_type=document.title,
                created=dateTime,
                shop=shop,
                category=category,
                imei=row.Imei,
                name=row.Name,
                pre_remainder=pre_remainder,
                incoming_quantity=0,
                outgoing_quantity=0,
                retail_price=rho_latest.retail_price,
                current_remainder=pre_remainder,
                sub_total= rho_latest.sub_total,
            )

        return redirect("log")
    else:
        context = {
           'shops': shops
            }
        return render(request, "sims/sim_return_list.html", context)

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
                rho_latest=RemainderHistory.objects.filer(imei=row.Imei).latest('created')
                sim_report=Sim_report.objects.create(
                    report_id=report_id,
                    name=row.Name,
                    imei=row.IMEI,
                    status=rho_latest.rho_type,
                    price=rho_latest.retail_price
                )
            else:
                string=f'Отчет не сформирован. Товар с IMEI {row.IMEI} отсутствует в базе данных.'
                messages.error(request,  string)
                if Sim_report.objects.filter(report_id=report_id).exists():
                    sim_report=Sim_report.objects.filter(report_id=report_id)
                    for sim in sim_report:
                        sim.delete()
                    report_id.delete()
                return redirect("activation_list")
            sim_report=Sim_report.objects.filter(report_id=report_id)

        #=======================Uploading to Excel Module===================================
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = (
            "attachment; filename=Remainder_" + str(datetime.date.today()) + ".xls"
        )

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Activation")

        # sheet header in the first row
        row_num = 0
        font_style = xlwt.XFStyle()

        columns = ["Name", "IMEI", "Status", "Price"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # sheet body, remaining rows
        font_style = xlwt.XFStyle()
        report_query = Sim_reports=Sim_report.objects.filter(report_id=report_id)
        query = report_query.values_list("name", "imei", "status", "price")

        for row in query:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response
#=======================End of Excel Upload Module================================



    else:
        return render(request, 'sims/activation_list.html')


    
