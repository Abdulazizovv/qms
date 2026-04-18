from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request,'advert/base_home.html')