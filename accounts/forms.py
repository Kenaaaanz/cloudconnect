from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import password_validation
from django.utils import timezone
from .models import CustomUser, UserSession
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser

CustomUser = get_user_model()

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': ' ',
            'id': 'login-username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': ' ',
            'id': 'login-password'
        })

class RegistrationForm(UserCreationForm):
    ACCOUNT_TYPE_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('prepaid', 'Prepaid'),
        ('corporate', 'Corporate'),
    ]
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'signup-email'
        })
    )
    company_account_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter company account number',
            'id': 'signup-account'
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
            'id': 'signup-firstname'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
            'id': 'signup-lastname'
        })
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number',
            'id': 'signup-phone'
        })
    )
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'signup-accounttype'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'company_account_number', 'first_name', 'last_name', 
                  'phone', 'account_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['password1', 'password2']:
                label = field.label if field.label else ''
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Enter {label.lower()}'
                })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'signup-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'signup-confirm'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'id': 'signup-username'
        })
        self.fields['account_type'].widget.attrs.update({
            'class': 'form-control',
            'id': 'signup-accounttype'
        })

    def clean_company_account_number(self):
        account_number = self.cleaned_data.get('company_account_number')
        if CustomUser.objects.filter(company_account_number=account_number).exists():
            raise forms.ValidationError("This company account number is already registered.")
        return account_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.company_account_number = self.cleaned_data['company_account_number']
        user.phone = self.cleaned_data['phone']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.account_type = self.cleaned_data['account_type']
        if commit:
            user.save()
        return user
    
class UserUpdateForm(UserChangeForm):
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password to confirm changes'
        }),
        help_text="Required to save changes to sensitive information"
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 
                 'city', 'state', 'country', 'zip_code')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if self.has_changed() and not self.instance.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password

class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        }),
        validators=[password_validation.validate_password]
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Current password is incorrect.")
        return old_password
    
    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Passwords don't match.")
        
        # Validate the password using Django's built-in validators
        password_validation.validate_password(new_password2, self.user)
        return new_password2
    
    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.last_password_change = timezone.now()
        self.user.save()
        return self.user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'city', 'state', 'country', 'zip_code',
            'email_notifications', 'sms_notifications', 'billing_reminders',
            'service_updates', 'promotional_offers', 'language', 
            'timezone', 'date_format', 'dark_mode'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'phone': forms.TextInput(attrs={'placeholder': '+254...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True

# This can be removed since we have CustomPasswordChangeForm above
# class CustomPasswordChangeForm(PasswordChangeForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Add CSS classes to form fields
#         for field in self.fields:
#             self.fields[field].widget.attrs.update({'class': 'form-control'})

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email_notifications', 'sms_notifications', 'billing_reminders', 
                 'service_updates', 'promotional_offers')
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'billing_reminders': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'service_updates': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
            'promotional_offers': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }

class AccountPreferencesForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('language', 'timezone', 'date_format', 'dark_mode')
        widgets = {
            'language': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'date_format': forms.Select(attrs={'class': 'form-control'}),
            'dark_mode': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }

class BillingAddressForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('address', 'city', 'state', 'country', 'zip_code')
        widgets = {
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
        }