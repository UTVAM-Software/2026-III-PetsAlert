from django.core.exceptions import ValidationError

class ContrasenaSegura:
    """Exige al menos una letra, un número y un símbolo (además del largo mínimo de Django)."""

    mensaje = 'La contraseña debe incluir al menos una letra, un número y un símbolo.'

    def validate(self, password, user=None):
        tiene_letra = any(c.isalpha() for c in password)
        tiene_numero = any(c.isdigit() for c in password)
        tiene_simbolo = any(not c.isalnum() and not c.isspace() for c in password)

        if not (tiene_letra and tiene_numero and tiene_simbolo):
            raise ValidationError(self.mensaje, code='contrasena_no_segura')

    def get_help_text(self):
        return self.mensaje
