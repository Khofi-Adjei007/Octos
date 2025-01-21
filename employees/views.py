from django.shortcuts import render
from django.http import HttpRequest
# Create your views here.


def employeesHomepage(request):
    return render(request, 'employeesHomepage.html')