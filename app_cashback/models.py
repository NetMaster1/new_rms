from django.db import models
from django.db.models.fields import DecimalField
from app_reference.models import ProductCategory

# Create your models here.

class Cashback (models.Model):
    size = models.DecimalField(default=0, max_digits=3, decimal_places=2)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    
    def __int__(self):
        return self.id