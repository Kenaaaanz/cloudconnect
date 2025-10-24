from django import forms
from .models import Router

# router_manager/forms.py (updated)
from django import forms
from .models import Router, GuestNetwork

class RouterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm WiFi password'}),
        required=False
    )
    
    class Meta:
        model = Router
        fields = ['mac_address', 'model', 'ssid', 'password', 'security_type', 
                 'hide_ssid', 'band', 'channel_width', 'firewall_enabled', 
                 'remote_access', 'upnp_enabled']
        widgets = {
            'mac_address': forms.TextInput(attrs={'placeholder': 'AA:BB:CC:DD:EE:FF'}),
            'model': forms.TextInput(attrs={'placeholder': 'Router Model'}),
            'ssid': forms.TextInput(attrs={'placeholder': 'Network Name'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'WiFi Password', 'render_value': True}),
            'security_type': forms.Select(attrs={'class': 'form-control'}),
            'band': forms.Select(attrs={'class': 'form-control'}),
            'channel_width': forms.Select(attrs={'class': 'form-control'}),
            'hide_ssid': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'firewall_enabled': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'remote_access': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'upnp_enabled': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

class GuestNetworkForm(forms.ModelForm):
    class Meta:
        model = GuestNetwork
        fields = ['ssid', 'password', 'enabled', 'bandwidth_limit', 'access_duration']
        widgets = {
            'ssid': forms.TextInput(attrs={'placeholder': 'Guest Network Name'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Guest Password', 'render_value': True}),
            'enabled': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'bandwidth_limit': forms.NumberInput(attrs={'min': 1, 'max': 100}),
            'access_duration': forms.NumberInput(attrs={'min': 1, 'max': 168}),
        }

class AdvancedSettingsForm(forms.ModelForm):
    class Meta:
        model = Router
        fields = ['hide_ssid', 'channel_width', 'band']
        widgets = {
            'hide_ssid': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }

class WiFiPasswordForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm WiFi password'}),
        required=True
    )
    
    class Meta:
        model = Router
        fields = ['password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'New WiFi Password'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data