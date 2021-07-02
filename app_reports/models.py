from django.db import models
from app_reference.models import ProductCategory, Supplier

# Create your models here.

class ProductHistory (models.Model):
    document = models.CharField(max_length=50, default=0)
    document_id = models.CharField(max_length=50, default=0)
    shop = models.CharField(max_length=50, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    quantity_in = models.IntegerField(null=True)
    quantity_out = models.IntegerField(null=True)

    # class Meta:
    #     ordering = ('created',)  # sorting by date
    def __str__(self):
        return self.name
