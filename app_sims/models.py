from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from app_product.models import Document
from app_reference.models import DocumentType
# Create your models here.

class SimReturnRecord(models.Model):
    enumerator = models.IntegerField(default=0, null=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    srr_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __int__(self):
        return self.id

class SimRegisterRecord(models.Model):
    enumerator = models.IntegerField(default=0, null=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    sim_reg_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __int__(self):
        return self.id
    
class SimSupplierReturnRecord(models.Model):
    enumerator = models.IntegerField(default=0, null=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    doc_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __int__(self):
        return self.id
    
class SimSigningOffRecord(models.Model):
    enumerator = models.IntegerField(default=0, null=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    doc_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __int__(self):
        return self.id
