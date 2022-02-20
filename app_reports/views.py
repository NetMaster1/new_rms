from shutil import move
from ssl import create_default_context
from app_personnel.models import BonusAccount, Salary
from django.db.models import query
from app_reference.models import DocumentType, ProductCategory, Shop, Supplier, Product
from app_cash.models import Cash, Credit, Card
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.models import User, Group
from app_product.models import (
    Product,
    RemainderHistory,
    RemainderCurrent,
    Document,
)
from .models import ReportTemp, ReportTempId, DailySaleRep, MonthlyBonus, SaleReport
from app_clients.models import Customer
from .models import ProductHistory
from django.contrib import messages
import pandas as pd
import xlwt
from datetime import datetime, date
from openpyxl.workbook import Workbook
from django.http import HttpResponse, JsonResponse
import datetime

# Create your views here.

def save_in_excel_daily_rep(request):
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all().order_by('name')
    # length=shops.count()
    doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
    if request.method == "POST":
        date=request.POST.get('date', False)
        if date:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        else:
            date = datetime.date.today()
        dateTime=date.strftime('%Y-%m-%d')
        # tdelta=datetime.timedelta(days=1)
        # previous_date=date-tdelta

        shop_titles=[]#list for displaying shop names (columns)
        for i in shops:
            shop_titles.append(i.name)
     #====================================================
        titles=['Shop', 'opeining_balance']#list for displaying categories (rows)
        for category in categories:
            titles.append(category.name)
        titles.append('sub_totals')
        titles.append('final_balance')

        report_id=ReportTempId.objects.create()
        for shop in shops:
            #dict=[new_key]=new_value #adding new pair (key, value) to python dictionnary
            shop_row=[]
            shop_row.append(shop.name)
            shop_row.append('opening_balance')

            for category in categories:
                rhos=RemainderHistory.objects.filter(shop=shop, category=category, created__date=date, rho_type=doc_type)
                sum=0
                for rho in rhos:
                    sum+=rho.retail_price
                shop_row.append(sum)
            #====================================================================
            expenses_type=DocumentType.objects.get(name='РКО (хоз.расходы)')
            if Cash.objects.filter(cho_type=expenses_type, shop=shop, created__date=date).exists():
                chos=Cash.objects.filter(cho_type=expenses_type, shop=shop, created__date=date)
                expenses_sum=0
                for cho in chos:
                    expenses_sum+=cho.cash_out
            else:
                expenses_sum=0
            salary_type=DocumentType.objects.get(name='РКО (зарплата)')
            if Cash.objects.filter(cho_type=salary_type, shop=shop, created__date=date).exists():
                chos=Cash.objects.filter(cho_type=salary_type, created__date=date)
                salary_sum=0
                for cho in chos:
                    salary_sum+=cho.cash_out
            else:
                salary_sum=0
            cash_move_type=DocumentType.objects.get(name='Перемещение денег')
            if Cash.objects.filter(cho_type=cash_move_type, shop=shop, sender=True, created__date=date).exists():
                chos=Cash.objects.filter(cho_type=cash_move_type, sender=True, created__date=date)
                cash_move_sum=0
                for cho in chos:
                    cash_move_sum+=cho.cash_out
            else:
                cash_move_sum=0
            return_type=DocumentType.objects.get(name='Возврат ТМЦ') 
            if Cash.objects.filter(cho_type=return_type, shop=shop, created__date=date).exists():
                chos=Cash.objects.filter(cho_type=return_type, created__date=date)
                return_sum=0
                for cho in chos:
                    return_sum+=cho.cash_out  
            else:
                return_sum=0  
            if Card.objects.filter(shop=shop, created__date=date).exists():
                cards=Card.objects.filter(shop=shop,created__date=date)
                card_sum=0
                for card in cards:
                    card_sum+=card.sum
            else:
                card_sum=0
            if Credit.objects.filter(shop=shop, created__date=date).exists():
                credits=Credit.objects.filter(shop=shop, created__date=date )
                credit_sum=0
                for credit in credits:
                    credit_sum+=credit.sum
            else:
                credit_sum=0
            #=======================Calculating opening balance for each shop======================
            if Cash.objects.filter(created__lt=date, shop=shop).exists():
                prev_day_cho=Cash.objects.filter(created__lt=date, shop=shop).latest('created')
                prev_day_cash_remainder=prev_day_cho.current_remainder
            else:
                prev_day_cash_remainder=0
            #================================================

            
            daily_rep=DailySaleRep.objects.create(
                report_id=report_id,
                created=dateTime,
                shop = shop.name,
                opening_balance=prev_day_cash_remainder,
                smartphones = shop_row[2],
                accessories = shop_row[3],
                sim_cards = shop_row[4],
                phones = shop_row[5],
                iphone = shop_row[6],
                insuranсе = shop_row[7],
                wink = shop_row[8],
                services = shop_row[9],
                pay_cards = shop_row[10],
                credit=credit_sum,
                card=card_sum,
                salary=salary_sum,
                expenses=expenses_sum,
                return_sum=return_sum,
                cash_move=cash_move_sum,
            )
            daily_rep.net_sales = daily_rep.smartphones + daily_rep.accessories + daily_rep.sim_cards + daily_rep.phones + daily_rep.iphone + daily_rep.insuranсе + daily_rep.wink + daily_rep.services + daily_rep.pay_cards

            daily_rep.final_balance= daily_rep.opening_balance + daily_rep.net_sales - daily_rep.credit - daily_rep.salary - daily_rep.card - daily_rep.expenses - daily_rep.return_sum - daily_rep.cash_move

            

            daily_rep.save()


          
        qs=DailySaleRep.objects.filter(report_id=report_id).exclude(shop='ООС').values()
        # n=qs.count()
        # print(n)
        data=pd.DataFrame(qs)
        data=data.drop('report_id_id', 1)#deleting 'report_id' column
        data=data.drop('category_id', 1)#deleting 'report_id' column
        data=data.drop('sum', 1)#deleting 'report_id' column
       
        # print(data)
        #data=pd.read_csv('data.txt')
        #data_1=data.read_csv('data.txt', header = None)
        #data.columns =['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13']
        
        data.set_index('id', inplace=True)
        data.set_index('shop', inplace=True)
        #data.set_index('shop', inplace=True, drop=False)
        print(data)
        data_2=data.loc['Дзержинск': 'Городец', 'accessories': 'iphone']
        # print(data_2)
        data_3=data.loc['Правдинск', 'accessories']
        # print(data_3)
        data_4=data.loc[:,'accessories']
        # print(data_4)
        # print(list(data_4))
        data=data.T #transposing the dataframe
        # print(data)
        #data=data_t.T #transposing backwards
        #data=data_t
        #print(data_t)
        #data_t['totals']=[]

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
        context = {
            'data': data.to_html(),
        }
        return render (request, 'reports/sample.html', context)
        #return HttpResponse(title)

def reports(request):
    return render(request, "reports/reports.html")

def close_report(request):
    users = Group.objects.get(name='sales').user_set.all()
    if ReportTempId.objects.filter(existance_check=True).exists():
        report_ids_temp=ReportTempId.objects.all()
        for obj in report_ids_temp:
            obj.delete()
    if ReportTemp.objects.filter(existance_check=True).exists():
        reports_temp=ReportTemp.objects.all()
        for obj in reports_temp:
            obj.delete()
    if request.user in users:
        return redirect ('sale_interface')
    else:
        return redirect("log")

def close_remainder_report(request):
    users = Group.objects.get(name='sales').user_set.all()
    if request.user in users:
        return redirect ('sale_interface')
    else:
        return redirect("log")

def sale_report(request):
    categories = ProductCategory.objects.all()
    products=Product.objects.all()
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
        
        if category:
            queryset_list = queryset_list.filter(category=category)
        if shop:
            queryset_list = queryset_list.filter(shop=shop)
        # if supplier:
        #     queryset_list = queryset_list.filter(supplier=supplier)
        if user:
            queryset_list = queryset_list.filter(user=user)
            user=user
        # if Q(start_date) | Q(end_date):
        #     queryset_list = queryset_list.filter(created__range=(start_date, end_date))
        if start_date:
            queryset_list = queryset_list.filter(created__gte=start_date)
        if end_date:
            queryset_list = queryset_list.filter(created__lte=end_date)

        report_id=ReportTempId.objects.create()
        products=Product.objects.filter(category=category)
        for product in products:
            av_sum=0
            quantity=0
            sum=0
            margin=0
            rhos=queryset_list.filter(imei=product.imei)
            for rho in rhos:
                av_sum+=rho.av_price
                quantity+=rho.outgoing_quantity
                sum += rho.sub_total
            if quantity!=0:
                sale_rep_row=SaleReport.objects.create(
                    report_id=report_id,
                    product = product.name,
                    av_sum = av_sum,
                    quantity = quantity,
                    retail_sum = sum,
                    margin=sum-av_sum
                )
        sale_report=SaleReport.objects.filter(report_id=report_id)
        for item in sale_report:
            sum+=item.retail_sum
            av_sum+=item.av_sum
            margin+=item.margin

        query = sale_report.values(
            "product", "av_sum", "quantity", "retail_sum", "margin"
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
            "sum": sum,
            'av_sum': av_sum,
            'sale_report': sale_report,
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
    if request.method == "POST":
        date=request.POST.get('date', False)
        if date:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        else:
            date = datetime.date.today()
        rhos=RemainderHistory.objects.filter(rho_type=doc_type, created__date=date)
        # shops_dict={}
        # for shop in shops:
        #     rhos=rhos.filter(shop=shop)
        #     categories_dict={}
        #     for category in categories:
        #         sum=0
        #         rhos_1=rhos.filter(category=category)
        #         for rho in rhos_1:
        #             sum+=rho.retail_price
        #         categories_dict[category]=sum
        #     shops_dict[shop]=categories_dict
        # context = {
        #     'shops_dict': shops_dict,
        # }
        # return render (request, 'reports/daily_sales.html', context)

        temp_id=ReportTempId.objects.create()
        for category in categories:
            for shop in shops:
                rhos_1=rhos.filter(category=category, shop=shop)
                accumulated_sum=0
                for rho in rhos_1:
                    accumulated_sum+= rho.retail_price
                item=DailySaleRep.objects.create(
                    report_id=temp_id,
                    shop=shop,
                    category=category,
                    sum=accumulated_sum
                )
        #daily_rep=DailySaleRep.objects.filter(report_id=temp_id)
        #daily_rep=DailySaleRep.objects.filter(report_id=temp_id).values_list()
        #=============================================
        # daily_rep=DailySaleRep.objects.filter(report_id=temp_id).values()
        # data=pd.DataFrame(daily_rep)
        #=============================================
        # daily_rep=DailySaleRep.objects.filter(report_id=temp_id)
        # query = daily_rep.values("shop", "category", "sum")
        # data=pd.DataFrame.from_records(query)
        #==============================================
        #print(data.shape)
        #print(data)
        #data.to_excel("C:/Users/NetUser/Daily_report.xlsx", index=False)

        #df1=pd.read_excel("C:/Users/NetUser/Feb_17.xlsx")
        #print(df1)
        context = {
            # 'items': items,
            'df': data.to_html(),
            'describe': data.describe().to_html(),
            'shops': shops,
            'categories': categories,
            'rhos': rhos
        }
        return render (request, 'reports/daily_sales.html', context)
    else:
        return render (request, 'reports/daily_sales.html')

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
    if request.user.is_authenticated:
        users=Group.objects.get(name="sales").user_set.all()
        group=Group.objects.get(name="admin").user_set.all()
        categories = ProductCategory.objects.all()
        shops = Shop.objects.all()
        if request.method == "POST":
            category = request.POST["category"]
            category=ProductCategory.objects.get(id=category)
            if request.user in group:
                shop=request.POST["shop"]
                shop=Shop.objects.get(id=shop)
            #     date=request.POST.get('date', False)
            #     if date:
            #         # converting HTML date format (2021-07-08) to django format (2021-07-10 01:05:00)
            #         date = datetime.datetime.strptime(date, "%Y-%m-%d")
            #     else:
            #         date = datetime.date.today()
            #     #date is given as 2022-01-28 00:00:00 (start of the day). To make it the end of the day
            #     #we add 1 day to 2022-01-28 00:00:00. By doing so we include all the documents issued during the current date
            #     # tdelta=datetime.timedelta(seconds=86399)
            #     tdelta_1=datetime.timedelta(days=1)
            #     date= (date+tdelta_1)
            # else:
            #     session_shop=request.session['session_shop']
            #     #session_shop=request.session.get['session_shop']
            #     shop=Shop.objects.get(id=session_shop)
            #     date=datetime.date.today()
            #     tdelta_1=datetime.timedelta(days=1)
            #     date= (date+tdelta_1)

            # array=[]
            # #products=Product.objects.filter(category=category)
            # products=Product.objects.filter(category=category)
            # for product in products:
            #     imei=product.imei
            #     if RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).exists():
            #         rho=RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).latest('created')
            #         if rho.current_remainder > 0:
            #             array.append(rho)
            # context = {
            #     'date': date,
            #     'shop': shop,
            #     'array': array,
            #     "category": category,
            #     'categories': categories,
            #     'shops': shops
            # }
            return redirect ('remainder_report_output', shop.id, category.id)   
            #return render (request, 'reports/remainder_report.html', context)   
        else:
            context = {
                "shops": shops,
                "categories": categories,
            }
            return render(request, "reports/remainder_report.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def remainder_report_output(request, shop_id, category_id):
    if request.user.is_authenticated:
        date=datetime.date.today()
        tdelta_1=datetime.timedelta(days=1)
        date= (date+tdelta_1)
        shop=Shop.objects.get(id=shop_id)
        category=ProductCategory.objects.get(id=category_id)
        array=[]
        #products=Product.objects.filter(category=category)
        products=Product.objects.filter(category=category)
        for product in products:
            imei=product.imei
            if RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).exists():
                rho=RemainderHistory.objects.filter(shop=shop, imei=imei, created__lte=date).latest('created')
                if rho.current_remainder > 0:
                    array.append(rho)
        context = {
            'date': date,
            'shop': shop,
            'array': array,
            "category": category
        }
        return render(request, "reports/remainder_report_output.html", context)
    else:
        auth.logout(request)
        return redirect("login")

def update_retail_price (request):
    group=Group.objects.get(name="admin").user_set.all()
    doc_type = DocumentType.objects.get(name="Переоценка ТМЦ")
    dateTime=datetime.datetime.now()
    if request.user in group:
        if request.method == "POST":
            imei=request.POST['imei']
            retail_price=request.POST['retail_price']
            shop=request.POST['shop']
            shop=Shop.objects.get(name=shop)

            category=request.POST['category']
            category=ProductCategory.objects.get(name=category)

            product=Product.objects.get(imei=imei)
            # remainder_current=RemainderCurrent.objects.get(imei=imei, shop=shop)
            # remainder_current.retail_price=retail_price
            # remainder_current.save()
            document=Document.objects.create(
                created=dateTime,
                title=doc_type,
                user=request.user,
                posted=True,
            )
            rho_latest_before=RemainderHistory.objects.filter(shop=shop, imei=imei, created__lt=dateTime).latest('created')
            rho=RemainderHistory.objects.create (
                document=document,
                created=document.created,
                rho_type=doc_type,
                user=request.user,
                shop=shop,
                product_id=product,
                category=product.category,
                imei=imei,
                name=product.name,
                retail_price=retail_price,
                pre_remainder=rho_latest_before.pre_remainder,
                incoming_quantity=0,
                outgoing_quantity=0,
                current_remainder=rho_latest_before.current_remainder
            )
            #rho.sub_total=rho.current_remainder*rho.retail_price
            #return redirect ('remainder_list', shop.id , category.id )
            return redirect ('remainder_report_output', shop.id, category.id)
    else:
        auth.logout(request)
        return redirect("login")
#==========================================================
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
    if request.user.is_authenticated:
        if request.method == "POST":
            imei = request.POST["imei"]
            start_date = request.POST["start_date"]
            end_date = request.POST["end_date"]
            imei=request.POST['imei']
            queryset_list = RemainderHistory.objects.filter(imei=imei).order_by('created')
            if start_date:
                queryset_list = queryset_list.filter(created__gte=start_date)
            if end_date:
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                #adding time delta to cover docs created after year:month:day:00:00 till the end of the day 23:59
                tdelta=datetime.timedelta(days=1)
                end_date=end_date+tdelta
                queryset_list = queryset_list.filter(created__lte=end_date)

            context = {
                "queryset_list": queryset_list, 
            }
            return render(request, "reports/item_report.html", context)
        else:
            return render(request, "reports/item_report.html")
    else:
        return redirect ('login')

def bonus_report(request):
    users = User.objects.all()
    categories=ProductCategory.objects.all()
    shops=Shop.objects.all()
    doc_type=DocumentType.objects.get(name='Продажа ТМЦ')
    if request.method == "POST":
        start_date = request.POST["start_date"]
        # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        end_date = request.POST["end_date"]
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        rhos=RemainderHistory.objects.filter(rho_type=doc_type, created__gte=start_date, created__lte=end_date)
    
        for user in users:
            user_row=[user.username]
            for category in categories:
                sum=0
                for shop in shops:
                    rhos_new=rhos.filter(category=category, user=user, shop=shop)
                    for rho in rhos_new:
                        sum+=int(rho.retail_price*category.bonus_percent*shop.sale_k)
                user_row.append(sum)

            if Credit.objects.filter(user=user).exists():
                credits=Credit.objects.filter(user=user)
                credit_sum=0
                for credit in credits:
                    credit_sum+-credit.sum
            else:
                credit_sum=0
            n=len(user_row)
            monthly_bonus=MonthlyBonus.objects.create(
                user_name=user_row[0],
                smarphones = user_row[1],
                accessories = user_row[2],
                sim_cards = user_row[3],
                phones = user_row[4],
                insuranсе = user_row[5],
                wink = user_row[6],
                services = user_row[7],
                credit=credit_sum*0.03,
                sub_total = 0,
            )
        query_set=MonthlyBonus.objects.filter().values()
        #print(qs)
        #n=qs.count()
        data=pd.DataFrame(query_set)
        data=data.drop('id', 1)
        #data=data.drop('1', 0)
        #data.set_index('user_name', inplace=True)
        #data.set_index('Name', inplace=True, drop=False)

        data=data.set_index('user_name')
        #data=data.T #transposing the dataframe
        data.to_excel('D:/Аналитика/Фин_отчет/Текущие/2021/data.xlsx')

        monthly_bonus_reports=MonthlyBonus.objects.all()
        for i in  monthly_bonus_reports:
            i.delete()

        context = {
            'data': data.to_html(),
        }
        return render (request, 'reports/bonus_report.html', context)

#===================================Array Version==========================================
        # gen_arr=[]
        # for user in users:
        #     arr=[]
        #     for category in categories:
        #         if rhos.filter(user=user, category=category).exists():
        #             rhos=rhos.filter(user=user, category=category)
        #             sales=0
        #             for rho in rhos:
        #                sales+=rho.retail_price*rho.outgoing_quantity*category.bonus_percent
        #         else:
        #             sales=0
        #         dict={category: sales}
        #         arr.append(dict)
        #     user_arr = {user: arr}
        #     gen_arr.append(user_arr)
        # context = {
        #     'gen_arr': gen_arr,
        #     'categories': categories
        # }
        # return render(request, "reports/bonus_report.html", context)

#=============End of Array Version=====================================================

    context = {
        'categories': categories,
        #'users': users
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
    context = {
        "queryset_list": queryset_list, 
        "shops": shops}

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

def salary_report (request):
    if request.user.is_authenticated:
        if request.method == "POST":
            start_date = request.POST["start_date"]
            print(start_date)
            end_date = request.POST["end_date"]
            print(end_date)
            # converting HTML date format (2021-07-08T01:05) to django format (2021-07-10 01:05:00)
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            tdelta=datetime.timedelta(days=1)
            end_date=end_date+tdelta
            print(start_date)
            print(end_date)
            arr=[]
            users=User.objects.all()
            for user in users:
                dict={}
                sum=0
                qs=user.cash_receiver.filter(created__gte=start_date, created__lte=end_date)
                for item in qs:
                    sum+=int(item.cash_out)
                dict[user]=sum
                arr.append(dict)
            context = {
                'arr': arr
            }
            return render (request, 'reports/salary_report.html', context)
        else:
            return render (request, 'reports/salary_report.html')
    else:
        return redirect ('login')


