from django.shortcuts import render

def manual_usuario(request):
    """
    Vista para mostrar el manual de usuario
    """
    return render(request, 'manual/manual.html')
