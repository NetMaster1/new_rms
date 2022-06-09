from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ErrorLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    definition = models.CharField(max_length=100)#def where the error occured
    
    def __int__(self):
        return self.id