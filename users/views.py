from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    mods = []
    for key, label in [
        ("projects", "Proyectos"),
        ("catalog", "Materiales"),
        ("dashboard", "Dashboard"),
    ]:
        if request.user.can_see(key):
            mods.append({"key": key, "label": label})
    return render(request, "home.html", {"modules": mods})
