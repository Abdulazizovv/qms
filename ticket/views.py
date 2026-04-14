from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def operator_panel(request):
    return render(request, 'operator/panel.html')
