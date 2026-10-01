from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import GuestProfile


class AccountLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}))

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email and password:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                user = None
            self.user_cache = authenticate(self.request, username=user.username if user else email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class AccountRegisterForm(UserCreationForm):
    full_name = forms.CharField(label='Nama lengkap', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}))
    phone_number = forms.CharField(label='Nomor telepon', max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}))

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone_number', 'password1', 'password2')

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists() or GuestProfile.objects.filter(user__email__iexact=email).exists():
            raise forms.ValidationError('Email tersebut sudah terdaftar.')
        return email

    def save(self, commit=True):
        full_name = self.cleaned_data['full_name'].strip()
        first_name, _, last_name = full_name.partition(' ')
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = first_name
        user.last_name = last_name
        if commit:
            user.save()
            GuestProfile.objects.create(user=user, phone_number=self.cleaned_data['phone_number'])
        return user