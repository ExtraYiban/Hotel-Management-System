from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from .forms import AccountLoginForm, AccountRegisterForm


class AccountLoginView(LoginView):
	template_name = 'accounts/login.html'
	authentication_form = AccountLoginForm
	redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
	pass


class RegisterView(CreateView):
	model = User
	form_class = AccountRegisterForm
	template_name = 'accounts/register.html'
	success_url = reverse_lazy('home')

	def form_valid(self, form):
		response = super().form_valid(form)
		login(self.request, self.object)
		return response
