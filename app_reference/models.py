from django.db import models

# Create your models here.


class Contributor (models.Model):
    name = models.CharField(max_length=250)

    def __int__(self):
        return self.id

class Supplier (models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Shop (models.Model):
    name = models.CharField(max_length=50)
    sale_k=models.IntegerField(default=1)
    retail = models.BooleanField(default=True)#mark for retail shops

    class Meta:
        ordering = ('name',)  # sorting by name

    def __str__(self):
        return self.name

class ProductCategory (models.Model):
    name = models.CharField(max_length=250)
    bonus_percent=models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.name

class Services (models.Model):
    name = models.CharField(max_length=250)
    retail_price = models.IntegerField(default=0, null=True)
    bonus_percent=models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.name

class DocumentType (models.Model):
    name = models.CharField(max_length=250)

    class Meta:
        verbose_name='documentType'
    def __str__(self):
        return self.name

class Product (models.Model):
    created = models.DateTimeField(auto_now=True)
    emumerator = models.IntegerField( null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50, unique=True)
    img = models.ImageField(upload_to='images', blank=True)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name

class Expense (models.Model):
    name = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return self.name

class Voucher (models.Model):
    name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name