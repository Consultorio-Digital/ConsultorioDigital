from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


def _normalize_rut(value: str) -> str:
    return value.replace(".", "").replace("-", "").strip()


class RutOrEmailBackend(ModelBackend):
    """Autentica por RUT (con o sin puntos/guión) o por correo electrónico."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        user = None

        # 1. Buscar por RUT normalizado (username en el modelo)
        normalized = _normalize_rut(username)
        try:
            user = User.objects.get(username=normalized)
        except User.DoesNotExist:
            pass

        # 2. Si no se encontró, intentar por email
        if user is None:
            try:
                user = User.objects.get(email__iexact=username.strip())
            except User.DoesNotExist:
                pass

        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
