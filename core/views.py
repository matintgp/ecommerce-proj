from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def home(request):
    """Render the Next.js app's index.html"""
    return render(request, 'index.html')