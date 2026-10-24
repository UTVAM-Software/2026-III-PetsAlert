from django import forms
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from auth_app.catalogo import GRUPO_BASICO, GRUPOS_SISTEMA
from auth_app.models import Usuario
from chat.models import Chat, ChatMessage
from feed.models import PetReport


def permisos_ordenados():
    return Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename'
    )


class UsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Al editar, déjala vacía para conservar la actual.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )
    groups = forms.ModelMultipleChoiceField(
        label='Grupos',
        queryset=Group.objects.order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    user_permissions = forms.ModelMultipleChoiceField(
        label='Permisos directos',
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Usuario
        fields = [
            'nombre',
            'email',
            'telefono',
            'localidad',
            'is_active',
            'email_verificado',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        ]
        labels = {
            'nombre': 'Nombre',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'localidad': 'Localidad',
            'is_active': 'Cuenta activa',
            'email_verificado': 'Correo verificado',
            'is_staff': 'Acceso a /admin/',
            'is_superuser': 'Superusuario',
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['user_permissions'].queryset = permisos_ordenados()

        if self.instance.pk is None:
            self.initial['email_verificado'] = True
            self.initial['groups'] = list(Group.objects.filter(name=GRUPO_BASICO))

        if actor is None or not actor.is_superuser:
            self.fields.pop('is_superuser', None)
            self.fields.pop('is_staff', None)

        if actor is not None and self.instance.pk == actor.pk:
            for nombre in ('is_active', 'is_superuser', 'is_staff', 'groups', 'user_permissions'):
                self.fields.pop(nombre, None)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        repetidos = Usuario.objects.filter(email__iexact=email)

        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)

        if repetidos.exists():
            raise ValidationError('Este correo ya está registrado.')

        return email

    def clean(self):
        cleaned = super().clean()
        clave = cleaned.get('password1')
        confirmacion = cleaned.get('password2')

        if self.instance.pk is None and not clave:
            self.add_error('password1', 'Ingresa una contraseña.')
        elif clave or confirmacion:
            if clave != confirmacion:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            else:
                try:
                    validate_password(clave, user=self.instance)
                except ValidationError as error:
                    self.add_error('password1', error)

        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        clave = self.cleaned_data.get('password1')

        if clave:
            usuario.set_password(clave)

        if commit:
            usuario.save()
            self.save_m2m()

        return usuario


class GrupoForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        label='Permisos',
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {'name': 'Nombre del grupo'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = permisos_ordenados()

    def clean_name(self):
        nombre = self.cleaned_data['name'].strip()

        if self.instance.pk and self.instance.name in GRUPOS_SISTEMA and nombre != self.instance.name:
            raise ValidationError('Los grupos base del sistema no se pueden renombrar.')

        return nombre


class PermisoForm(forms.ModelForm):
    content_type = forms.ModelChoiceField(
        label='Modelo',
        queryset=ContentType.objects.order_by('app_label', 'model'),
    )

    class Meta:
        model = Permission
        fields = ['name', 'codename', 'content_type']
        labels = {'name': 'Nombre', 'codename': 'Código'}


class ReporteForm(forms.ModelForm):
    class Meta:
        model = PetReport
        fields = [
            'user',
            'status',
            'species',
            'name',
            'breed',
            'color',
            'description',
            'last_seen_location',
            'image',
            'is_active',
            'is_resolved',
        ]
        labels = {
            'user': 'Autor',
            'status': 'Tipo de reporte',
            'species': 'Especie',
            'name': 'Nombre de la mascota',
            'breed': 'Raza',
            'color': 'Color',
            'description': 'Descripción',
            'last_seen_location': 'Última ubicación',
            'image': 'Foto',
            'is_active': 'Visible en la app',
            'is_resolved': 'Resuelto',
        }


class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['report', 'owner', 'interested']
        labels = {'report': 'Reporte', 'owner': 'Dueño del reporte', 'interested': 'Interesado'}

    def clean(self):
        cleaned = super().clean()
        reporte = cleaned.get('report')
        dueno = cleaned.get('owner')
        interesado = cleaned.get('interested')

        if dueno and interesado and dueno == interesado:
            self.add_error('interested', 'El interesado debe ser distinto del dueño.')

        if reporte and dueno and reporte.user_id != dueno.pk:
            self.add_error('owner', 'El dueño del chat debe ser el autor del reporte.')

        return cleaned


class MensajeForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['chat', 'sender', 'content', 'is_read']
        labels = {
            'chat': 'Chat',
            'sender': 'Remitente',
            'content': 'Contenido',
            'is_read': 'Leído',
        }

    def clean(self):
        cleaned = super().clean()
        chat = cleaned.get('chat')
        remitente = cleaned.get('sender')

        if chat and remitente and not chat.tiene_participante(remitente):
            self.add_error('sender', 'El remitente debe participar en el chat.')

        return cleaned
