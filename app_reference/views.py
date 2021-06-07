from django.shortcuts import render

# Create your views here.
def reference (request):
    return render(request, 'reference.html')