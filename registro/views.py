from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import RegisterForm

# Create your views here.
def registro(request):
    
    if request.method == "POST":
        
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            
            user = form.save()
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(
                username = user.username, 
                password = raw_password
            )
            login(request, user)
            
            return redirect("/")
        
        else:
            print(form.errors)
            
    else:
        form = RegisterForm()
        
    return render(
        request = request, 
        template_name = "registro.html", 
        context = {
            "form": form,
            "title": "Registro de pacientes"
        }
    )