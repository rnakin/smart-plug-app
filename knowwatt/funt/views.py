from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

def dashboard_page(request):
    # Redirect to home SPA
    from django.shortcuts import redirect
    return redirect('/home/')

def home_page(request):
    return render(request, 'home/app.html')

def verify_email_page(request):
    return render(request, 'verify_email.html')

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def reset_password_page(request):
    return render(request, 'reset_password.html')