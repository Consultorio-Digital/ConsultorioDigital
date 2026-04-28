# registro/forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from re import match
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column, HTML

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

    TIPO_CHOICES = [
        ('paciente',     'Paciente'),
        ('profesional',  'Profesional'),
    ]

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
    birthdate       = forms.DateField(
                        required=False,
                        input_formats=['%d / %m / %Y', '%d/%m/%Y', '%Y-%m-%d'],
                        widget=forms.TextInput(),
                    )
    tipo            = forms.ChoiceField(choices=TIPO_CHOICES, initial='paciente')
    especialidad    = forms.CharField(max_length=255, required=False)
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
        
        # Help texts: solo donde hay una regla real que comunicar
        self.fields["username"].help_text   = "Ej: 12.345.678-9"
        self.fields["email"].help_text      = ""
        self.fields["first_name"].help_text = ""
        self.fields["last_name"].help_text  = ""
        self.fields["address"].help_text    = ""
        self.fields["phone"].help_text      = ""
        self.fields["birthdate"].help_text  = ""
        self.fields["password1"].help_text  = "Mínimo 8 caracteres, sin secuencias obvias ni solo números"
        self.fields["password2"].help_text  = ""

        # Placeholders: ejemplos concretos, no repetir el label
        self.fields["username"].widget.attrs["placeholder"]   = "12.345.678-9"
        self.fields["email"].widget.attrs["placeholder"]      = "ejemplo@correo.com"
        self.fields["first_name"].widget.attrs["placeholder"] = "María"
        self.fields["last_name"].widget.attrs["placeholder"]  = "González"
        self.fields["address"].widget.attrs["placeholder"]    = "Av. Principal 123, Santiago"
        self.fields["phone"].widget.attrs["placeholder"]      = "+56 9 1234 5678"
        self.fields["birthdate"].widget.attrs["placeholder"]   = "DD / MM / AAAA"
        self.fields["birthdate"].widget.attrs["maxlength"]     = "14"
        self.fields["birthdate"].widget.attrs["inputmode"]     = "numeric"
        self.fields["birthdate"].widget.attrs["autocomplete"]  = "bday"
        self.fields["password1"].widget.attrs["placeholder"]  = "Mínimo 8 caracteres"
        self.fields["password2"].widget.attrs["placeholder"]  = "Repite tu contraseña"
        
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
        
        self.fields['tipo'].label         = 'Tipo de cuenta'
        self.fields['especialidad'].label  = 'Especialidad'
        self.fields['especialidad'].help_text = 'Requerido si eres profesional'
        self.fields['especialidad'].widget.attrs['placeholder'] = 'Ej: Medicina General, Odontología...'

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('tipo',       css_class='login-input'),
            HTML('''
                <div id="div-especialidad">
            '''),
            Field('especialidad', css_class='login-input'),
            HTML('</div>'),
            Field('email',      css_class='login-input'),
            Row(
                Column(Field('first_name', css_class='login-input'), css_class='col-md-6'),
                Column(Field('last_name',  css_class='login-input'), css_class='col-md-6'),
            ),
            Field('username',   css_class='login-input'),
            Field('address',    css_class='login-input'),
            Field('phone',      css_class='login-input'),
            Field('birthdate',  css_class='login-input'),
            Field('password1',  css_class='login-input'),
            Field('password2',  css_class='login-input'),
        )

    def clean_username(self):
        # ── Mantén tu validación de RUT chileno existente ──
        cleaned_data = self.cleaned_data
        dni          = cleaned_data.get('username')

        if not validate_chilean_dni(dni):
            self.add_error('username', 'Ingrese un RUT válido')

        return remove_points_and_hyphens(dni)