from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Usuario

class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        error_messages={
            'required': 'Ingresa tu correo electrónico.',
            'invalid': 'El correo no es válido.',
        },
    )
    password = forms.CharField(
        strip=False,
        error_messages={'required': 'Ingresa tu contraseña.'},
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

class RegistroForm(forms.Form):
    nombre = forms.CharField(
        max_length=150,
        error_messages={'required': 'Ingresa tu nombre completo.'},
    )
    email = forms.EmailField(
        max_length=254,
        error_messages={
            'required': 'Ingresa tu correo electrónico.',
            'invalid': 'El correo no es válido.',
        },
    )
    password = forms.CharField(
        strip=False,
        error_messages={'required': 'Ingresa una contraseña.'},
    )
    confirm_password = forms.CharField(
        strip=False,
        error_messages={'required': 'Confirma tu contraseña.'},
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este correo ya está registrado.')

        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')

        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')
        elif password:
            usuario_temporal = Usuario(
                nombre=cleaned.get('nombre', ''),
                email=cleaned.get('email', ''),
            )
            try:
                validate_password(password, user=usuario_temporal)
            except ValidationError as error:
                self.add_error('password', error)

        return cleaned

    def guardar(self):
        return Usuario.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            nombre=self.cleaned_data['nombre'].strip(),
        )

class ReenviarVerificacionForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        error_messages={
            'required': 'Ingresa tu correo electrónico.',
            'invalid': 'Ingresa un correo válido.',
        },
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
