from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    # Add email as default registration form only have username and password 
    email = forms.EmailField(required=True)
    enable_email_otp = forms.BooleanField(
        required=False,
        label="Enable one-time codes by email for future logins",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        # dont allow duplicate emails
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        # Save user cleaned email 
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginPasswordForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            self.user = authenticate(
                request=self.request,
                username=username,
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError("Invalid username or password.")

        return cleaned_data


class OTPCodeForm(forms.Form):
    otp_code = forms.CharField(max_length=6, min_length=6)

    def clean_otp_code(self):
        code = self.cleaned_data["otp_code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Enter a 6-digit code.")
        return code


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_first_name(self):
        # Remove spaces around the first name.
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        # Remove spaces around the last name.
        return self.cleaned_data["last_name"].strip()

    def clean_email(self):
        # Let the current user keep their email, but block duplicates.
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("An account with this email already exists.")
        return email


class SecuritySettingsForm(forms.Form):
    enable_email_otp = forms.BooleanField(
        required=False,
        label="Require a one-time code by email when I log in",
    )