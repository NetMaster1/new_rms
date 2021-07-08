from django.db import models

# Create your models here.


class Supplier (models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Shop (models.Model):
    name = models.CharField(max_length=50)
    sale_k=models.IntegerField(default=1)

    def __str__(self):
        return self.name

class ProductCategory (models.Model):
    name = models.CharField(max_length=250)
    cashback_percent=models.IntegerField(default=0)
    bonus_percent=models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.name

class DocumentType (models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

class Product (models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50, unique=True)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name