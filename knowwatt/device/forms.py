from django import forms
from .models import SmartPlug, ElectricalDevice, NFCTag


class SmartPlugForm(forms.ModelForm):
    class Meta:
        model = SmartPlug
        fields = ['plug_code', 'name', 'location']
        widgets = {
            'plug_code': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. KW-001',
            }),
            'name': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. Kitchen Plug A1',
            }),
            'location': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. Kitchen, Bedroom',
            }),
        }


class SmartPlugEditForm(forms.ModelForm):
    class Meta:
        model = SmartPlug
        fields = ['name', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'modal-input'}),
            'location': forms.TextInput(attrs={'class': 'modal-input'}),
        }


class ElectricalDeviceForm(forms.ModelForm):
    class Meta:
        model = ElectricalDevice
        fields = ['name', 'device_type', 'rated_power_watts', 'risk_level', 'auto_cutoff_minutes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'modal-input',
                'placeholder': 'e.g. Refrigerator',
            }),
            'device_type': forms.Select(attrs={'class': 'modal-input'}),
            'rated_power_watts': forms.NumberInput(attrs={
                'class': 'modal-input',
                'placeholder': 'Watts',
            }),
            'risk_level': forms.Select(attrs={'class': 'modal-input'}),
            'auto_cutoff_minutes': forms.NumberInput(attrs={
                'class': 'modal-input',
                'placeholder': 'Minutes (blank = disabled)',
            }),
        }


class NFCTagForm(forms.Form):
    tag_uid = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={
            'class': 'modal-input',
            'placeholder': 'NFC Tag UID',
        }),
    )
    device = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput(),
    )
    label = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Optional label',
        }),
    )


class NFCTagEditForm(forms.ModelForm):
    class Meta:
        model = NFCTag
        fields = ['label', 'device']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'modal-input'}),
            'device': forms.Select(attrs={'class': 'modal-input'}),
        }
