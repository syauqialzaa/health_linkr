from django.http import HttpResponseRedirect
from django.urls import reverse, resolve
from django.conf import settings
from django.contrib.auth import logout
from .permissions import is_admin, is_patient

class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow all users to access admin login
        if request.path.startswith('/admin/login/'):
            return self.get_response(request)

        # Only handle authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            url_name = resolve(request.path_info).url_name
        except:
            url_name = None

        # Handle admin pages
        if request.path.startswith('/admin/'):
            if not is_admin(request.user):
                return HttpResponseRedirect(reverse('home'))
            return self.get_response(request)

        # Handle auth-related URLs
        auth_urls = [
            'login',
            'signup',
            'password_reset',
            'password_reset_done',
            'password_reset_confirm',
            'password_reset_complete'
        ]

        # Redirect authenticated users away from auth pages
        if url_name in auth_urls:
            if is_admin(request.user):
                return HttpResponseRedirect(reverse('admin:index'))
            return HttpResponseRedirect(reverse('home'))

        return self.get_response(request)