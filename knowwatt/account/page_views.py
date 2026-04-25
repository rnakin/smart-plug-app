from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import ProfileForm


@login_required
def profile_view(request):
    return render(request, 'account/profile.html', {'user_obj': request.user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('page-profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'account/profile_edit.html', {'form': form})


@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed.')
            return redirect('page-profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/password_change.html', {'form': form})
