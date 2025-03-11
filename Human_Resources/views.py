from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required



@login_required
def Human_Resources(request):
    if not request.user.is_staff:  # Restrict to HR users
        return redirect('employeesLogin')
    return render(request, 'human_resource.html', {'user': request.user})