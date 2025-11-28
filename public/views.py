from django.shortcuts import render, redirect
from .public_apply_forms import PublicApplyForm
from django.contrib import messages

def index(request):
    return render(request, 'public/index.html')

def about(request):
    return render(request, 'public/about.html')

def services(request):
    return render(request, 'public/services.html')

def contact(request):
    return render(request, 'public/contact.html')

def careers(request):
    # placeholder page listing open roles; link to apply
    return render(request, 'public/careers.html')


# public/views.py
def public_apply(request):
    """
    Website 'Apply' view — saves to Human_Resources.PublicApplication via PublicApplyForm.
    """
    if request.method == "POST":
        form = PublicApplyForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.created_by = None
            app.status = "pending"
            app.save()
            messages.success(request, "Application received — thank you! We'll contact you if shortlisted.")
            return redirect("public:apply")
        else:
            messages.error(request, "Please fix the errors below and resubmit.")
    else:
        form = PublicApplyForm()

    return render(request, "public/apply.html", {"form": form})

