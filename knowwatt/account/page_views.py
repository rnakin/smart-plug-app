from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import ProfileForm


@login_required
def profile_view(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    return render(request, 'account/profile.html', {
        'user_obj': request.user,
        'profile_form': profile_form,
        'password_form': password_form
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('page-profile')
        else:
            # Re-render profile page with errors in modal
            password_form = PasswordChangeForm(request.user)
            return render(request, 'account/profile.html', {
                'user_obj': request.user,
                'profile_form': form,
                'password_form': password_form,
                'open_modal': 'edit-profile-modal'
            })
    return redirect('page-profile')


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
            # Re-render profile page with errors in modal
            profile_form = ProfileForm(instance=request.user)
            return render(request, 'account/profile.html', {
                'user_obj': request.user,
                'profile_form': profile_form,
                'password_form': form,
                'open_modal': 'change-password-modal'
            })
    return redirect('page-profile')
