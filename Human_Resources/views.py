from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def Human_Resources(request):
    if not request.user.is_staff:  # Restrict to HR (is_staff for now)
        return redirect('employeesLogin')
    return render(request, 'Human_Resource/human_resource.html', {'user': request.user})