from django.db import models
from app_reference.models import ProductCategory

# Create your models here.

class Cashback (models.Model):
    size = models.IntegerField()
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    

    def __int__(self):
        return self.id