from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'Username',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'modal-input',
                'placeholder': 'Email',
            }),
        }


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Current password',
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'modal-input',
            'placeholder': 'New password',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Confirm new password',
        })
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if pw and confirm and pw != confirm:
            raise forms.ValidationError('Passwords do not match.')
        if pw:
            validate_password(pw)
        return cleaned
