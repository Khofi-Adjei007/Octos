from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from employees.models import Employee



@login_required
def Human_Resources(request):
    if not request.user.is_staff:  # Restrict to HR users
        return redirect('employeesLogin')
    # Get pending employees
    pending_employees = Employee.objects.filter(is_active=False)
    return render(request, 'human_resource.html', {'user': request.user, 'pending_employees': pending_employees})