from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponseServerError

def custom_404(request, exception):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)

def custom_403(request, exception):
    """Кастомная страница 403"""
    return render(request, '403.html', status=403)

def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)