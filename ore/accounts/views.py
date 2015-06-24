from ore.accounts.models import OreUser
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView, FormView
from django.db import IntegrityError

from ore.core.views import RequiresLoggedInMixin
from ore.accounts import forms


def loginview(request):
    return auth_views.login(
        request,
        template_name='accounts/login.html',
        authentication_form=forms.AuthenticationForm
    )


class LogoutView(TemplateView):
    template_name = 'accounts/logout_confirm.html'

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(
            self.request, "You have been logged out successfully."
        )
        return redirect('/')


class RegisterView(FormView):
    template_name = 'accounts/new.html'
    form_class = forms.RegistrationForm

    def form_valid(self, form):
        # Create a new user account
        username = form.cleaned_data['name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            user = OreUser.objects.create_user(
                username,
                email=email,
                password=password
            )
            user.save()
        except IntegrityError:
            form.add_error('name', 'That username is already taken.')
            return self.form_invalid(form)

        user = authenticate(username=username, password=password)
        if user is None:
            raise ValueError("User I just created has a different password?")
        login(self.request, user)
        messages.success(
            self.request,
            'Your user account has been created and you have been logged in.'
        )

        return redirect('/')


class SettingsMixin(object):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['active_settings'] = self.settings_name
        return data


class ProfileSettings(RequiresLoggedInMixin, SettingsMixin, TemplateView):
    template_name = 'accounts/settings/profile.html'
    settings_name = 'profile'
