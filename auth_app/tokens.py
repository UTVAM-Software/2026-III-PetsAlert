from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenVerificacionEmail(PasswordResetTokenGenerator):
    """
    Token de un solo uso para verificar el correo. Deja de ser válido cuando el
    correo ya está verificado o cuando el usuario cambia de correo.
    """

    key_salt = 'auth_app.tokens.TokenVerificacionEmail'

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{user.email}{user.email_verificado}{timestamp}'


token_verificacion_email = TokenVerificacionEmail()
