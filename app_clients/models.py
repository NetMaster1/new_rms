from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer (models.Model):
    f_name = models.CharField(max_length=50)
    l_name = models.CharField(max_length=50)
    phone=models.CharField(max_length=50)
    created = models.DateField(auto_now_add=True)
    bar_code = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    accum_cashback= models.IntegerField(default=0)
    
    
    def __int__(self):
        return self.id