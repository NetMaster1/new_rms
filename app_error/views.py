from django.shortcuts import render, redirect
from app_product.models import RemainderHistory, Document
from app_reference.models import Supplier, DocumentType

# Create your views here.

def error(request, document_id):
    pass

def modify_supplier (rerquest):
    supplier_1=Supplier.objects.get(id=2)
    supplier_2=Supplier.objects.get(id=6)
    doc_type = DocumentType.objects.get(name="Поступление ТМЦ")
    queryset_rhos = RemainderHistory.objects.filter(rho_type=doc_type)
    queryset_docs = Document.objects.filter(title=doc_type)
   
    for item in queryset_rhos:
        if item.supplier == supplier_2:
            item.supplier = supplier_1
            item.save()
    for item in queryset_docs:
        if item.supplier == supplier_2:
            item.supplier = supplier_1
            item.save()

    return redirect ('log')
    
