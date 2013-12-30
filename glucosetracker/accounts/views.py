from django.shortcuts import render_to_response, HttpResponseRedirect
from django.views.generic import FormView
from django.template import RequestContext
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from axes.decorators import watch_login
from braces.views import LoginRequiredMixin

from .models import UserSettings
from .forms import UserSettingsForm, SignUpForm


@watch_login
def login_view(request):
    # Force logout.
    logout(request)
    username = password = ''

    # Flag to keep track whether the login was invalid.
    login_failed = False

    if request.POST:
        # We're only allowing lowercase in usernames, so convert
        # what the user entered to lowercase.
        username = request.POST['username'].lower()
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/dashboard/')
        else:
            login_failed = True

    return render_to_response('accounts/login.html',
                              {'login_failed': login_failed},
                              context_instance=RequestContext(request))


class SignUpView(FormView):
    success_url = '/dashboard/'
    form_class = SignUpForm
    template_name = 'accounts/signup.html'

    def get_initial(self):
        # Force logout.
        logout(self.request)

        return {'time_zone': settings.TIME_ZONE}

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.full_clean()

        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']

            user = User.objects.create(username=username)
            user.email = form.cleaned_data['email']
            user.set_password(password)
            user.save()

            # Create an entry for the User Settings.
            user_settings = UserSettings.objects.create(user=user)
            user_settings.time_zone = form.cleaned_data['time_zone']
            user_settings.save()


            # Automatically authenticate the user after user creation.
            user_auth = authenticate(username=username, password=password)
            login(request, user_auth)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class UserSettingsView(LoginRequiredMixin, FormView):
    success_url = '.'
    form_class = UserSettingsForm
    template_name = 'accounts/usersettings.html'

    def get_initial(self):
        user = self.request.user
        settings = user.settings

        return {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'time_zone': settings.user.settings.time_zone,
            'glucose_low': settings.glucose_low,
            'glucose_high': settings.glucose_high,
            'glucose_target_min': settings.glucose_target_min,
            'glucose_target_max': settings.glucose_target_max,
        }

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Settings saved!')
        return super(UserSettingsView, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.full_clean()

        if form.is_valid():
            user = self.request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            #user.email = form.cleaned_data['email']
            user.save()

            user.settings.time_zone = form.cleaned_data['time_zone']
            user.settings.glucose_low = form.cleaned_data['glucose_low']
            user.settings.glucose_high = form.cleaned_data['glucose_high']
            user.settings.glucose_target_min = form.cleaned_data[
                'glucose_target_min']
            user.settings.glucose_target_max = form.cleaned_data[
                'glucose_target_max']
            user.settings.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)