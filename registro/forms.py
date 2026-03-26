from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from consultorio.models import Usuario
from django import forms
from re import match

def validate_chilean_dni(rut: str | None) -> bool:
    """Validate a Chilean RUT.
    
    Args:
        rut: The RUT to validate.
        
    Returns:
        True if the RUT is valid, False otherwise.
    """
    if rut is None:
        return False

    # Clean RUT
    rut = (
        rut
        .replace('.', '')
        .replace('-', '')
    )
    
    # Check format
    if not match(r'^\d{7,8}[0-9Kk]$', rut):
        return False
    
    # Split RUT and DV
    rut_num = int(rut[:-1])
    dv      = rut[-1].upper()
    
    # Calculate DV
    reversed_digits = map(int, reversed(str(rut_num)))
    factors         = [2, 3, 4, 5, 6, 7] * 2
    s               = sum(d * f for d, f in zip(reversed_digits, factors))
    mod             = (-s) % 11
    calculated_dv   = 'K' if mod == 10 else str(mod)
    
    # Check DV
    return dv == calculated_dv

def remove_points_and_hyphens(rut: str | None) -> str:
    """Remove points and hyphens from a RUT.
    
    Args:
        rut: The RUT to clean.

    Returns:
        The cleaned RUT.
    """
    if rut is None:
        return ''
    return (
        rut
        .replace('.', '')
        .replace('-', '')
    )
    
def clean_username(self):
    cleaned_data = self.clean()
    dni          = cleaned_data.get('username')
    
    if not validate_chilean_dni(dni):
        self.add_error("username", "Ingrese un RUT válido")

    return remove_points_and_hyphens(dni)


class RegisterForm(UserCreationForm):
    
    class Meta:
        model = User
        fields = [
            "username", 
            "email", 
            "first_name",
            "last_name",
            "address",
            "phone",
            "birthdate",
        ]
    
    username        = forms.CharField(max_length=12)
    email           = forms.EmailField()
    first_name      = forms.CharField(max_length=80)
    last_name       = forms.CharField(max_length=80, required=False)
    address         = forms.CharField(max_length=255, required=False)
    phone           = forms.CharField(max_length=15, required=False)
    birthdate       = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    usable_password = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Change labels
        self.fields["username"].label   = "RUT"
        self.fields["email"].label      = "Correo"
        self.fields["first_name"].label = "Nombre"
        self.fields["last_name"].label  = "Apellido"
        self.fields["address"].label    = "Dirección"
        self.fields["phone"].label      = "Teléfono"
        self.fields["birthdate"].label  = "Fecha de Nacimiento"
        self.fields["password1"].label  = "Contraseña"
        self.fields["password2"].label  = "Confirmar contraseña"
        
        # Change help texts
        self.fields["username"].help_text   = "Ingrese su RUT (en un formato válido)"
        self.fields["email"].help_text      = "Ingrese un correo válido"
        self.fields["first_name"].help_text = "Ingrese su nombre"
        self.fields["last_name"].help_text  = "Ingrese su apellido"
        self.fields["address"].help_text    = "Ingrese su dirección"
        self.fields["phone"].help_text      = "Ingrese su teléfono"
        self.fields["birthdate"].help_text  = "Ingrese su fecha de nacimiento"
        self.fields["password1"].help_text  = "Ingrese una contraseña segura: al menos 8 caracteres, no común y no solo numérica"
        self.fields["password2"].help_text  = "Repita la contraseña"
        
        # Change placeholders
        self.fields["username"].widget.attrs["placeholder"]   = "RUT"
        self.fields["email"].widget.attrs["placeholder"]      = "Correo"
        self.fields["first_name"].widget.attrs["placeholder"] = "Nombre"
        self.fields["last_name"].widget.attrs["placeholder"]  = "Apellido"
        self.fields["address"].widget.attrs["placeholder"]    = "Dirección"
        self.fields["phone"].widget.attrs["placeholder"]      = "Teléfono"
        self.fields["birthdate"].widget.attrs["placeholder"]  = "Fecha de Nacimiento"
        self.fields["password1"].widget.attrs["placeholder"]  = "Contraseña"
        self.fields["password2"].widget.attrs["placeholder"]  = "Confirmar contraseña"
        
        # Change error messages
        self.fields["username"].error_messages = {
            "unique"   : "Este RUT ya está registrado",
            "invalid"  : "Ingrese un RUT válido",
            "required" : "Este campo es obligatorio"
        }
        
        self.fields["email"].error_messages = {
            "unique"   : "Este correo ya está registrado",
            "invalid"  : "Ingrese un correo válido",
            "required" : "Este campo es obligatorio"
        }
        
        self.fields["first_name"].error_messages = {
            "required" : "Este campo es obligatorio"
        }

        self.fields["password1"].error_messages = {
            "required" : "Este campo es obligatorio",
            "password_too_short" : "La contraseña es muy corta",
        }
        
        self.fields["password2"].error_messages = {
            "required" : "Este campo es obligatorio",
            "password_mismatch" : "Las contraseñas no coinciden"
        }
        
        self.error_messages["password_mismatch"] = "Las contraseñas no coinciden."