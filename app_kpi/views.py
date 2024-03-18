from django.shortcuts import render, redirect, get_object_or_404
from app_product.models import RemainderHistory, Document
from app_reference.models import Shop, Product, DocumentType, ProductCategory
from app_reports.models import ReportTempId, Sim_report
from django.contrib import messages
import datetime
from datetime import date, timedelta
from django.contrib import messages, auth


#creates a register of sim forms which has been returned to operator
def monthly_kpi (request):
    if request.user.is_authenticated:
        date = datetime.date.today()
        if request.method == "POST":
            file = request.FILES["file_name"]
      
            return redirect("log")
        else:
            context = {
                'date': date,
            }
            return render(request, "kpi/kpi_per_shop.html", context)
    else:
        auth.logout(request)
        return redirect("login")
    

def kpi_excel_input (request):
    pass

def kpi_adjustment (request):
    pass

def kpi_execution (request):
    pass