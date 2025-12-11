from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth import authenticate

# ✅ Signup form
class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ('name', 'email', 'phone', 'password1', 'password2')

# ✅ Login form with email/phone
class CustomAuthenticationForm(forms.Form):
    email_or_phone = forms.CharField(label='Email or Phone', max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')
        password = self.cleaned_data.get('password')

        try:
            user = CustomUser.objects.get(email=email_or_phone)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(phone=email_or_phone)
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("User not found")

        self.user = authenticate(self.request, username=user.email, password=password)
        if self.user is None:
            raise forms.ValidationError("Invalid credentials")
        return self.cleaned_data

    def get_user(self):
        return self.user

# ✅ Profile update form (FIXED)
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'monthly_budget']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }
