from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request,'base_home/advert_home.html')