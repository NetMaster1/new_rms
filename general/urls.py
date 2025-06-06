"""general URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include ('app_personnel.urls')),
    path('app_product', include ('app_product.urls')),
    path('reference', include ('app_reference.urls')),
    path('clients', include ('app_clients.urls')),
    path('cash', include ('app_cash.urls')),
    path('cashback', include ('app_cashback.urls')),
    path('reports', include ('app_reports.urls')),
    path('finance', include ('app_finance.urls')),
    path('error', include ('app_error.urls')),
    path('wholesale', include ('app_wholesale.urls')),
    path('tutorial', include ('app_tutorial.urls')),
    path('sims', include ('app_sims.urls')),
    path('fiscal', include ('app_fiscal.urls')),
    path('kpi', include ('app_kpi.urls')),
    path('service', include ('app_service.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
