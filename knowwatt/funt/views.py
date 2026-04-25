from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date
from house.models import House, HouseMember
from device.models import SmartPlug
from energy.models import EnergyReading
from alert.models import AlertEvent


def index(request):
    if request.user.is_authenticated:
        return redirect('page-home')
    return render(request, 'index.html')


@login_required(login_url='/login/')
def dashboard_page(request):
    return redirect('page-home')


@login_required(login_url='/login/')
def home_page(request):
    return redirect('page-house-detail-main')


def custom_404(request, exception):
    return render(request, '404.html', status=404)
