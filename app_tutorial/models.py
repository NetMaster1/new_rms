from django.db import models

# Create your models here.

class Tutorial(models.Model):
    title = models.CharField(max_length=100)
    video_file = models.FileField(upload_to='uploads', null=True)
    thumbnail_file = models.FileField(upload_to='uploads', null=True)

    #length = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    #size_mb = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # def get_absolute_file_upload_url(self):
    #     return MEDIA_URL + self.file_upload.url

    def __int__(self):
        return self.id