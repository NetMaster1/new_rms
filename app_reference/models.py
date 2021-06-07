from django.db import models

# Create your models here.


class Supplier (models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Shop (models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class ProductCategory (models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

class Product (models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name