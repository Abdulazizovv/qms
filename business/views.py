from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_index(request):
    return render(request, 'dashboard/index.html')


@login_required
def business_list(request):
    return render(request, 'dashboard/business_list.html')
