from django.shortcuts import render
from .models import Tutorial

# Create your views here.


def tutorials (request):
    videos=Tutorial.objects.all()
    context = {
        "videos": videos
    }
    return render (request, 'tutorials/video_list.html', context)

def video (request, video_id):
    video=Tutorial.objects.get(id=video_id)
    context = {
        'video': video,
        }
    return render(request, 'tutorials/video.html', context)

