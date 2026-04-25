from django import forms
from .models import House, HouseMember


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['house_name', 'address', 'lat', 'long', 'emoji']
        widgets = {
            'house_name': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. My Home',
            }),
            'address': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. 123 Main St',
            }),
            'lat': forms.HiddenInput(),
            'long': forms.HiddenInput(),
            'emoji': forms.HiddenInput(attrs={'value': '🏠'}),
        }


class HouseMemberInviteForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'modal-input',
            'placeholder': 'user@example.com',
        })
    )
    role = forms.ChoiceField(
        choices=[('member', 'Member'), ('guest', 'Guest'), ('admin', 'Admin')],
        initial='member',
        widget=forms.Select(attrs={'class': 'modal-input'}),
    )


class HouseMemberRoleForm(forms.Form):
    role = forms.ChoiceField(
        choices=[('admin', 'Admin'), ('member', 'Member'), ('guest', 'Guest')],
        widget=forms.Select(attrs={'class': 'modal-input'}),
    )
