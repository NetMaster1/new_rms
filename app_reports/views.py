from app_personnel.models import BonusAccount
from django.db.models import query
from app_reference.models import DocumentType, ProductCategory, Shop, Supplier, Product
from app_cash.models import Cash, Credit, Card
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from app_product.models import (
    Product,
    RemainderHistory,
    RemainderCurrent,
    Sale,
    Transfer,
    Delivery,
    Document,
)
from .models import ReportTemp, ReportTempId, DailySaleRep
from app_clients.models import Customer
from .models import ProductHistory
from django.contrib import messages
import pandas as pd
import xlwt
from datetime import datetime, date
from openpyxl.workbook import Workbook
from django.http import HttpResponse, JsonResponse
import datetime
from datetime import datetime, date

# Create your views here.

def save_in_excel(request):
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    length=shops.count()
    print('=============')
    print('number of shops')
    print(length)
    titles=['Shop']
    for category in categories:
        titles.append(category.name)
    titles.append('sub_totals')
    print('======================')
    print(titles)
    print('======================')
    
    for shop in shops:
        #dict=[new_key]=new_value #adding new pair (key, value) to python dictionnary
        shop_row=[]
        shop_row.append(shop.name)

        for category in categories:
            rhos=RemainderHistory.objects.filter(shop=shop, category=category)
            sum=0
            for rho in rhos:
                sum+=rho.retail_price
            shop_row.append(sum)
        a=len(shop_row)
        print(a)    
        print(shop_row)
        print(shop_row[0])
        daily_rep=DailySaleRep.objects.create(
            shop = shop,
            smarphones = shop_row[1],
            accessories = shop_row[2],
            sim_cards = shop_row[3],
            phones = shop_row[4],
            insuranсе = shop_row[5],
            wink = shop_row[6],
            services = shop_row[7],
            sub_total = 0
        )
    
    qs=DailySaleRep.objects.filter().exclude(shop='ООС').values()
    n=qs.count()
    print(n)

    data=pd.DataFrame(qs)
    print(data)
    data.to_excel('D:/Аналитика/Фин_отчет/Текущие/2021/data.xlsx')

    registers=DailySaleRep.objects.all()
    for register in registers:
        register.delete()
        
    # response=HttpResponse(content_type='application/ms-excel')
    # response['Content-Disposition'] = 'attachment; filename=Expenses' +  str(datetime.datetime.now())+'.xls'
    # wb = xlwt.Workbook(encoding ='uft-8')
    # ws=wb.add_sheet('Expenses')
    # row_num = 0
    # font_style=xlwt.XFStyle()
    # font_style.font.bold=True

    # columns = ['Amount', 'Description', 'Category', 'Date']
    # for col_num in range(len(columns)):
    #     ws.write(row_num, col_num, columns[col_num], font_style)
    
    # font_style = xlwt.XFStyle()

    # rows = Expenses.objects.filter(owner=request.user).values_list('amount','description','category','date')

    # for row in rows:
    #     row_num+=1

    #     for col_num in range(len(row)):
    #         ws.write(row_num, col_num, row[col_num], font_style)

    # wb.save(response)
    return HttpResponse(titles)


def reports(request):
    return render(request, "reports/reports.html")

def close_report(request):
    users = Group.objects.get(name='sales').user_set.all()
    if ReportTemp.objects.filter(existance_check=True).exists():
        reports_temp=ReportTemp.objects.all()
        for obj in reports_temp:
            obj.delete()
    if ReportTempId.objects.filter(existance_check=True).exists():
        report_ids_temp=ReportTempId.objects.all()
        for obj in report_ids_temp:
            obj.delete()
    if request.user in users:
        return redirect ('sale_interface')
    else:
        return redirect("log")

def sale_report(request):
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    suppliers=Supplier.objects.all()
    users = User.objects.all()
    if request.method == "POST":
        doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
        queryset_list = RemainderHistory.objects.filter(rho_type=doc_type)
        sum = 0
        category = request.POST["category"]
        shop = request.POST["shop"]
        if shop:
            shop=Shop.objects.get(id=shop)
        supplier = request.POST["supplier"]
        if supplier:
            supplier=Supplier.objects.get(id=supplier)
        user = request.POST["user"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
            # if imei:
            #     queryset_list = queryset_list.filter(imei__icontains=imei)
        if category:
            queryset_list = queryset_list.filter(category=category)
        if shop:
            queryset_list = queryset_list.filter(shop=shop)
        if supplier:
            queryset_list = queryset_list.filter(supplier=supplier)
        if user:
            queryset_list = queryset_list.filter(user=user)
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        for item in queryset_list:
            sum += item.sub_total
       
        query = queryset_list.values(
            "category", "supplier", "imei", "name", "outgoing_quantity", "retail_price"
        )
        data=pd.DataFrame.from_records(query)
       # data = pd.DataFrame(query)
        #indicate the directory where the file will be uploaded to
        data.to_excel("C:/Users/NetUser/Sale_report.xlsx", index=False)
        #content=myfile.read()
        context = {
            "categories": categories,
            "shops": shops,
            'suppliers': suppliers,
            "users": users,
            "queryset_list": queryset_list,
            "sum": sum,
        }
        return render(request, "reports/sale_report.html", context)
    else:
        context = {
            "categories": categories,
            "shops": shops,
            'suppliers': suppliers,
            "users": users,
        }
        return render(request, "reports/sale_report.html", context)

def daily_sales (request):
    categories = ProductCategory.objects.all()
    shops = Shop.objects.all()
    doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
    documents=Document.objects.filter(title=doc_type)
    date=datetime.datetime.now()
    rhos=RemainderHistory.objects.filter(rho_type=doc_type, created__date=date)
    # for shop in shops:
    #     rhos=rhos.filter(shop=shop)
    #     categories_dict={}
    #     for category in categories:
    #         rhos=rhos.filter(category=category)
    #         sum=0
    #         for rho in rhos:
    #             sum+=rho.retail_price
    #         categories_dict[category]=sum
    #     a=len(categories)
    #     for i in range(a):
    #         item=DailySaleTemp.objects.create(
    #         shop=shop,

    #     )
           



    # temp_id=ReportTempId.objects.create()
    # for category in categories:
    #     for shop in shops:
    #         rhos=rhos.filter(category=category, shop=shop)
    #         accumulated_sum=0
    #         for rho in rhos:
    #             accumulated_sum+= rho.retail_price
    #     item=DailySaleTemp.objects.create(
    #         report_id=temp_id,
    #         shop=shop,
    #         category=category,
    #         sum=accumulated_sum
    #     )
    # items=DailySaleTemp.objects.filter(report_id=temp_id)


    context = {
        'items': items,
        'shops': shops,
        'categories': categories
    }
    return render (request, 'reports/daily_sales.html', context)

def delivery_report(request):
    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    #deliveries = Delivery.objects.all()
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    queryset_list=RemainderHistory.objects.filter(rho_type=doc_type.id)
    if request.method == "POST":
        #shop = request.POST["shop"]
        category = request.POST["category"]
        supplier = request.POST["supplier"]
        #user = request.POST["user"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        if supplier:
            queryset_list=queryset_list.filter(supplier=supplier)
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        if category:
            queryset_list=queryset_list.filter(category=category)
        context = {
            "categories": categories,
            "suppliers": suppliers,
            "queryset_list": queryset_list,
            "sum": sum,
        }
        return render(request, "reports/delivery_report.html", context)
    else:
        context = {
            "categories": categories,
            "suppliers": suppliers,
            "queryset_list": queryset_list,
        }
    return render(request, "reports/delivery_report.html", context)
#=======================================================
def remainder_report(request):
    categories = ProductCategory.objects.all()
    products=Product.objects.all()
    shops = Shop.objects.all()
    if request.method == "POST":
        date = request.POST["date"]
        category = request.POST["category"]
        category=ProductCategory.objects.get(id=category)
        try:
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
        except:
            messages.error(request, "Выберите категорию товара")
            return redirect("remainder_report")
        try:
            shop = request.POST["shop"]
            shop=Shop.objects.get(id=shop)
        except:
            messages.error(request, "Выберите торговую точку")
            return redirect("remainder_report")
        if date:
            array=[]
            queryset_list=RemainderHistory.objects.filter(shop=shop, category=category, created__lte=date)
            for product in products:
                if queryset_list.filter(imei=product.imei, shop=shop).exists():
                    queryset=queryset_list.filter(imei=product.imei, shop=shop)
                    rho = queryset.latest("created")
                    array.append(rho)
            context = {
                'date': date,
                'shop': shop,
                'array': array,
                "shops": shops,
                "categories": categories,
                "category": category
            }
            return render(request, "reports/remainder_report.html", context)
        else:
            qs = RemainderCurrent.objects.filter(shop=shop, category=category)
            context = {
                "qs": qs,
                'shop': shop,
                "shops": shops,
                "categories": categories,
                "category": category
            }
            #return render(request, "reports/remainder_report.html", context)
            return redirect ('remainder_list', shop.id, category.id)
    else:
        context = {
            "shops": shops,
            "categories": categories,
        }
        return render(request, "reports/remainder_report.html", context)

def remainder_list (request, shop_id, category_id):
    shop=Shop.objects.get(id=shop_id)
    category=ProductCategory.objects.get(id=category_id)
    #remainders=RemainderCurrent.objects.filter(shop=shop, category=category).order_by('name').values_list()
    #remainders=RemainderCurrent.objects.filter(shop=shop, category=category).order_by('name')
    remainders=RemainderCurrent.objects.filter(shop=shop, category=category).order_by('name').values()
    print('##########################')
    print(remainders)
    print('##########################')


    df=pd.DataFrame(remainders)
    print(df.shape)#displays the number of rows & columns
    print('##########################')
    print(df)
    print('##########################')
    #df.to_excel('data.xlsx')
    context ={
        #'remainders':remainders,
        'df': df.to_html(),
        'category': category
    }
    return render (request, 'reports/remainder_report_output.html', context)

def update_retail_price (request, imei, shop, category):
    shop=Shop.objects.get(id=shop)
    category=ProductCategory.objects.get(id=category)
    if request.method == "POST":
        product=Product.objects.get(imei=imei)
        #shop = request.POST["shop"]
        #imei = request.POST["imei"]
        #category = request.POST["category"]
        #category=ProductCategory.objects.get(id=category)
        #product.name=name
        #product.category=category
        #product.imei=imei
        retail_price=request.POST['retail_price']
        remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
        remainder_current.retail_price=retail_price
        remainder_current.save()
        return redirect ('remainder_list', shop.id, category.id)

#======================================================================

def remainder_report_dynamic(request):
    products=Product.objects.all()
    categories = ProductCategory.objects.all()
    products=Product.objects.all()
    shops = Shop.objects.all()
    if request.method == "POST":
        report_id=ReportTempId.objects.create()
        date_start = request.POST["date_start"]
        date_end = request.POST["date_end"]
        category = request.POST["category"]
        shop = request.POST["shop"]
        shop=Shop.objects.get(id=shop)
        queryset=RemainderHistory.objects.filter(shop=shop, category=category, created__gte=date_start, created__lte=date_end)
        for product in products:
            if queryset.filter(imei=product.imei).exists():
                queryset_list=queryset.filter(imei=product.imei)
                q_in=0
                q_out=0
                for qs in queryset_list:
                    q_in+=qs.incoming_quantity
                    q_out+=qs.outgoing_quantity
                rho_end = queryset_list.latest("created")
                rho_start = queryset_list.earliest("created")
                report=ReportTemp.objects.create(
                    report_id=report_id,
                    name=product.name,
                    imei=product.imei,
                    quantity_in=q_in,
                    quantity_out=q_out,
                    initial_remainder=rho_start.pre_remainder,
                    end_remainder=rho_end.current_remainder
                )
            else:
                if RemainderHistory.objects.filter(imei=product.imei, shop=shop, category=category, created__lt=date_start).exists():
                    rhos=RemainderHistory.objects.filter(imei=product.imei, shop=shop, created__lt=date_start)
                    rho_latest=rhos.latest('created')
                    report=ReportTemp.objects.create(
                        report_id=report_id,
                        name=rho_latest.name,
                        imei=rho_latest.imei,
                        #quantity_in=0,
                        #quantity_out=0,
                        initial_remainder=rho_latest.current_remainder,
                        end_remainder=rho_latest.current_remainder
                    )
        reports=ReportTemp.objects.filter(report_id=report_id)
        context = {
            'reports': reports,
            'shops': shops,
            'categories': categories,
            'date_start': date_start,
            'date_end': date_end,
            'shop': shop,
        }
        return render (request, 'reports/remainder_report_dynamic.html', context)
    context = {
        'shops': shops,
        'categories': categories,
    }
    return render (request, 'reports/remainder_report_dynamic.html', context)

def item_report(request):
    if request.method == "POST":
        imei = request.POST["imei"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        imei=request.POST['imei']
        queryset_list = RemainderHistory.objects.filter(imei=imei).order_by('created')
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)
        context = {
            "queryset_list": queryset_list, 
        }
        return render(request, "reports/item_report.html", context)
    else:
        return render(request, "reports/item_report.html")

def bonus_report(request):
    users = User.objects.all()
    categories=ProductCategory.objects.all()
    doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
    if request.method == "POST":
        start_date = request.POST["start_date"]
        # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
        start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        end_date = request.POST["end_date"]
        end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        rhos=RemainderHistory.objects.filter(rho_type=doc_type)
    #===================================Array Version==========================================
        gen_arr=[]
        for user in users:
            arr=[]
            for category in categories:
                if rhos.filter(user=user, category=category).exists():
                    rhos=rhos.filter(user=user, category=category)
                    sales=0
                    for rho in rhos:
                       sales+=rho.retail_price*rho.outgoing_quantity*category.bonus_percent
                else:
                    sales=0
                dict={category: sales}
                arr.append(dict)
            user_arr = {user: arr}
            gen_arr.append(user_arr)
    #================================End of array version===============================
                # phones_sum=0
                # phones=sales.filter(category=2)#Трубки
                # for phone in phones:
                #     phones_sum+=phone.sub_total
                # category_phones=categories.get(id=2)
                # bonus_phones=phones_sum*category_phones.bonus_percent

                # arr=[user, category, sales]
                # arr_category=[]
                # arr_category.append(arr)
                # user_arr.append(arr_category)
        context = {
            'gen_arr': gen_arr,
            'categories': categories
        }
        return render(request, "reports/bonus_report.html", context)

    context = {
        'categories': categories
    }
    return render(request, "reports/bonus_report.html", context)

def bonus_report_excel (request):
    users = User.objects.all()
    categories=ProductCategory.objects.all()
    doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
   
    #start_date = request.POST["start_date"]
    # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
    #start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
    #end_date = request.POST["end_date"]
    #end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
    rhos=RemainderHistory.objects.filter(rho_type=doc_type)

    #=======================Saving in Excel==============================================
    wb=Workbook()
    ws=wb.active
    ws.title="Bonus"
   
    #====================================End of Saving in Excel==========================

    #=====================================Array Version==========================================
    starting_row=2
    for user in users:
        ws.cell(row=starting_row, column=1).value = user.last_name
        
        starting_column=2
        for category in categories:
            ws.cell(column=starting_column, row=1).value = category.name
            
            if rhos.filter(user=user, category=category).exists():
                rhos=rhos.filter(user=user, category=category)
                sales=0
                for rho in rhos:
                    sales+=rho.retail_price*rho.outgoing_quantity*category.bonus_percent
            else:
                sales=0

            ws.cell(column=starting_column, row=starting_row).value = sales
            starting_column+=1
        starting_row+=1
                
    wb.save('names.xlsx')

    return redirect ('log')

def cash_report(request):
    shops = Shop.objects.all()
    queryset_list = Cash.objects.all()
    context = {"queryset_list": queryset_list, "shops": shops}

    return render(request, "reports/cash_report.html", context)

def card_report(request):
    shops=Shop.objects.all()
    cards=Card.objects.all()
    users=User.objects.all()
    if request.method == "POST":
        date_start = request.POST["date_start"]
        date_end = request.POST["date_end"]
        shop = request.POST["shop"]
        user = request.POST["user"]
        
    
    context = {
        'shops': shops,
        'users': users
    }
    return render(request, 'reports/card_report.html', context)

def credit_report(request):
    shops=Shop.objects.all()
    credits=Credit.objects.all()
    users=User.objects.all()
    if request.method == "POST":
        date_start = request.POST["date_start"]
        date_end = request.POST["date_end"]
        shop = request.POST["shop"]
        user = request.POST["user"]
    
    context = {
        'shops': shops,
        'users': users
    }
    return render(request, 'reports/credit_report.html', context)

