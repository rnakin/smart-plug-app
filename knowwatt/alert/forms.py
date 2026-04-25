from django import forms
from .models import AlertRule


class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ['plug', 'device', 'trigger', 'threshold_value', 'action', 'is_active']
        widgets = {
            'plug': forms.Select(attrs={'class': 'modal-input'}),
            'device': forms.Select(attrs={'class': 'modal-input'}),
            'trigger': forms.Select(attrs={'class': 'modal-input'}),
            'threshold_value': forms.NumberInput(attrs={
                'class': 'modal-input',
                'placeholder': 'Threshold (W or minutes)',
            }),
            'action': forms.Select(attrs={'class': 'modal-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
